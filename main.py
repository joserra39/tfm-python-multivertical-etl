import argparse
import sys
import os
import json
import time
from modules.transformer import transform_csv_to_ngsi

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

def save_chunks(entities, output_base_dir, chunk_size=50):
    # Crear el directorio 'outputs' dentro del path proporcionado
    output_path = os.path.join(output_base_dir, "outputs")
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f"Directorio creado: {output_path}")

    # Dividir la lista de entidades en trozos de 50
    for i in range(0, len(entities), chunk_size):
        chunk = entities[i:i + chunk_size]
        
        # Generar nombre de archivo con Timestamp Unix
        timestamp = int(time.time() * 1000) + (i // chunk_size) # Evitar colisión
        file_name = f"air_quality_{timestamp}.json"
        full_file_path = os.path.join(output_path, file_name)
        
        with open(full_file_path, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, indent=4, ensure_ascii=False)
        
        print(f"Generado: {file_name} con {len(chunk)} entidades.")

def main():
    if len(sys.argv) < 2:
        print("Error: Se requiere el path del directorio de datos.")
        sys.exit(1)
        
    directory_path = sys.argv[1]
    all_entities = []

    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} no es un directorio válido.")
        sys.exit(1)

    # Procesar todos los archivos CSV
    for filename in os.listdir(directory_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(directory_path, filename)
            print(f"--- Procesando {filename} ---")
            try:
                entities = transform_csv_to_ngsi(file_path)
                all_entities.extend(entities)
            except Exception as e:
                print(f"Error procesando {filename}: {e}")

    # Guardar en ficheros de 50 entidades
    if all_entities:
        save_chunks(all_entities, directory_path)
        print(f"\nProceso completado. Total entidades: {len(all_entities)}")
    else:
        print("No se encontraron entidades válidas para procesar.")

if __name__ == "__main__":
    # test_pipeline()
    main()