import argparse
import sys

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

if __name__ == "__main__":
    test_pipeline()