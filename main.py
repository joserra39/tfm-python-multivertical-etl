import argparse
import sys
import os
import json
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

def main():
    # Jenkins pasa el path como primer argumento: python main.py /ruta/datos
    if len(sys.argv) < 2:
        print("Error: Se requiere el path del directorio.")
        sys.exit(1)
        
    directory_path = sys.argv[1]
    all_ngsi_entities = []

    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} no es un directorio válido.")
        sys.exit(1)

    for filename in os.listdir(directory_path):
        if filename.endswith(".csv"):
            print(f"Procesando {filename}...")
            file_path = os.path.join(directory_path, filename)
            entities = transform_csv_to_ngsi(file_path)
            all_ngsi_entities.extend(entities)

    # Guardar resultado o enviar a un Context Broker
    with open('output_ngsi.json', 'w', encoding='utf-8') as f:
        json.dump(all_ngsi_entities, f, indent=4, ensure_ascii=False)
    
    print(f"Proceso finalizado. {len(all_ngsi_entities)} entidades generadas.")

if __name__ == "__main__":
    # test_pipeline()
    main()