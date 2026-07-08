import sys
import os
import json
import time
import importlib
import logging
import tc_etl_lib as tc
from modules.common.auth_keycloak import KeycloakAuthManager
from pathlib import Path

# --------------------------------------------------
# Load .env only in local environments
# --------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --------------------------------------------------
# Logging configuration
# --------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def chunked(data, size):
    for i in range(0, len(data), size):
        yield data[i:i + size]

def save_chunks(entities, output_base_dir, vertical_name, chunk_size=50):
    output_path = os.path.join(output_base_dir, "outputs")
    os.makedirs(output_path, exist_ok=True)

    for i, chunk in enumerate(chunked(entities, chunk_size)):
        timestamp = int(time.time() * 1000) + i
        file_name = f"{vertical_name}_{timestamp}.json"
        full_path = os.path.join(output_path, file_name)

        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(chunk, f, indent=4, ensure_ascii=False)

        logger.info("Generado fichero de salida: %s", file_name)

# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    if len(sys.argv) < 3:
        logger.error("Uso: python main.py <PATH_DATOS> <VERTICAL>")
        sys.exit(1)

    directory_path = sys.argv[1]
    vertical_name = sys.argv[2]

    # FIWARE ServicePath derivado de la vertical
    service_path = f"/{vertical_name}"

    if not os.path.isdir(directory_path):
        logger.error("El directorio %s no es válido", directory_path)
        sys.exit(1)

    logger.info("Ejecutando ETL para vertical '%s'", vertical_name)
    logger.info("FIWARE ServicePath: %s", service_path)

    all_entities = []

    # --------------------------------------------------
    # Keycloak authentication (OAuth2)
    # --------------------------------------------------
    auth = None
    if os.getenv("KEYCLOAK_URL"):
        logger.info("Configurando autenticación Keycloak")

        # Usamos nuestra nueva clase que sí acepta client_id/secret
        auth = KeycloakAuthManager(
            endpoint=os.getenv("KEYCLOAK_URL"),
            service=os.getenv("FIWARE_SERVICE"),
            user=os.getenv("KEYCLOAK_USER"),
            password=os.getenv("KEYCLOAK_PASSWORD"),
            client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
            client_secret=os.getenv("KEYCLOAK_CLIENT_SECRET")
        )

        try:
            auth.get_auth_token_subservice(service_path)
        except Exception as e:
            logger.error("Error autenticando contra Keycloak: %s", e)
            raise

    # --------------------------------------------------
    # Dynamic transformer loading
    # --------------------------------------------------
    try:
        module = importlib.import_module(f"modules.{vertical_name}.transformer")
        transform_func = getattr(module, "transform_csv_to_ngsi")
    except Exception as e:
        logger.error("No se pudo cargar el transformer de '%s': %s", vertical_name, e)
        sys.exit(1)

    # --------------------------------------------------
    # CSV processing
    # --------------------------------------------------
    for filename in os.listdir(directory_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(directory_path, filename)
            logger.info("Procesando fichero %s", filename)
            try:
                entities = transform_func(file_path)
                all_entities.extend(entities)
            except Exception as e:
                logger.error("Error procesando %s: %s", filename, e)

    if not all_entities:
        logger.warning("No se generaron entidades NGSI")
        return

    logger.info("Total de entidades generadas: %d", len(all_entities))

    # --------------------------------------------------
    # Orion configuration
    # --------------------------------------------------
    orion_base_url = os.getenv("ORION_BASE_URL")

    if not orion_base_url:
        logger.warning(
            "ORION_BASE_URL no definido. Guardando entidades en disco"
        )
        # Almacena las entidades en ficheros JSON por bloques
        # save_chunks(all_entities, directory_path, vertical_name)

        # Creamos una copia para no alterar las entidades originales si se usan luego
        entities_for_sql = []
        for entity in all_entities:
            sql_ready_entity = entity.copy()
            for key, attr in sql_ready_entity.items():
                # Si el atributo es un diccionario (como location o address)
                # y tiene una clave 'value', serializamos ese 'value'
                if isinstance(attr, dict) and 'value' in attr:
                    if isinstance(attr['value'], (dict, list)):
                        # Convertimos el dict/list en un string JSON
                        attr['value'] = json.dumps(attr['value'])
            entities_for_sql.append(sql_ready_entity)
        # --------------------------------------------

        path_sql = Path(os.path.join(directory_path, "outputs", "inserts.sql"))

        logger.info("Guardando entidades en SQL: %s", path_sql)
        with tc.sqlFileStore(path=path_sql, subservice=service_path, namespace=vertical_name) as store:
            store(all_entities)
        return

    # --------------------------------------------------
    # Send entities to Orion
    # --------------------------------------------------
    logger.info("Enviando entidades a Orion (%s)", orion_base_url)

    cbm = tc.cb.cbManager(endpoint=orion_base_url)

    with tc.orionStore(
        cb=cbm,
        auth=auth,
        subservice=service_path
    ) as store:
        for chunk in chunked(all_entities, 50):
            store(chunk)

    logger.info("Carga completada correctamente en Orion")

# --------------------------------------------------
# Entry point
# --------------------------------------------------
if __name__ == "__main__":
    main()
