import sys
import os
import json
import time
import importlib
from modules.common.loader import OrionLoader


def test_pipeline():
    parser = argparse.ArgumentParser(description="Test de Pipeline ETL")
    
    # Definimos los parámetros que esperamos de Jenkins
    parser.add_argument("--url", help="URL del CSV")
    parser.add_argument("--mapping", help="Estructura JSON")
    parser.add_argument("--device_id", help="ID del dispositivo")
    parser.add_argument("--api_key", help="API Key")
    parser.add_argument("--token", help="Token de seguridad")

    args = parser.parse_args()

    print("--- INICIO DE PRUEBA DE PIPELINE ---")
    print(f"Versión de Python en el nodo: {sys.version}")
    print(f"URL recibida: {args.url}")
    print(f"Mapping recibido: {args.mapping}")
    print(f"Device ID: {args.device_id}")
    print(f"API Key: {args.api_key}")
    # Por seguridad, solemos ocultar parte del token en los logs
    token_display = f"{args.token[:4]}****" if args.token else "None"
    print(f"Token recibido: {token_display}")
    print("--- PRUEBA COMPLETADA CON ÉXITO ---")

def save_chunks(entities, output_base_dir, vertical_name, chunk_size=50):
    output_path = os.path.join(output_base_dir, "outputs")
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for i in range(0, len(entities), chunk_size):
        chunk = entities[i:i + chunk_size]
        timestamp = int(time.time() * 1000) + (i // chunk_size)
        # Incluimos el nombre de la vertical en el fichero
        file_name = f"{vertical_name}_{timestamp}.json"
        full_file_path = os.path.join(output_path, file_name)
        
        with open(full_file_path, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, indent=4, ensure_ascii=False)
        print(f"Generado: {file_name}")

def main():
    # Ahora esperamos 2 parámetros: PATH y VERTICAL
    if len(sys.argv) < 3:
        print("Uso: python main.py <PATH_DATOS> <NOMBRE_VERTICAL>")
        print("Ejemplo: python main.py ./datos airquality")
        sys.exit(1)
        
    directory_path = sys.argv[1]
    vertical_name = sys.argv[2]
    all_entities = []

    # --- LÓGICA DE CARGA DINÁMICA ---
    try:
        # Importa el módulo modules.airquality (o el que pases por parámetro)
        module = importlib.import_module(f"modules.{vertical_name}.transformer")
        # Obtenemos la función de transformación del módulo cargado
        transform_func = getattr(module, "transform_csv_to_ngsi")
    except ImportError:
        print(f"Error: No existe el trasformador para la vertical '{vertical_name}'")
        sys.exit(1)
    except AttributeError:
        print(f"Error: El módulo '{vertical_name}' no tiene la función 'transform_csv_to_ngsi'")
        sys.exit(1)

    # Procesar archivos
    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} no es un directorio.")
        sys.exit(1)

    for filename in os.listdir(directory_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(directory_path, filename)
            print(f"Procesando {filename} con vertical: {vertical_name}")
            try:
                # Usamos la función cargada dinámicamente
                entities = transform_func(file_path)
                all_entities.extend(entities)
            except Exception as e:
                print(f"Error en {filename}: {e}")

    if all_entities:
        if os.getenv("ORION_URL"):
            loader = OrionLoader(os.getenv("ORION_URL"))
            loader.upsert_entities(all_entities)
        else:
            save_chunks(all_entities, directory_path, vertical_name)
    else:
        print("No se generaron entidades.")

if __name__ == "__main__":
    # test_pipeline()
    main()