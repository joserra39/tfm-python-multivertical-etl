import os
import re
import pandas as pd
from datetime import datetime

from modules.common.time_utils import parse_date
from modules.common.entity_builder import (
    load_entity_template,
    build_entity_from_template
)

ENTITY_TEMPLATE = load_entity_template(
    os.path.join(os.path.dirname(__file__), "entity.json")
)

SOURCE_URL = "https://datos.madrid.es"


def read_csv(file_path):
    return pd.read_csv(file_path, sep=";", dtype=str, encoding="utf-8")


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_column_name(col):
    col = normalize_text(col)

    replacements = {
        "á": "a", "à": "a", "ä": "a", "â": "a",
        "é": "e", "è": "e", "ë": "e", "ê": "e",
        "í": "i", "ì": "i", "ï": "i", "î": "i",
        "ó": "o", "ò": "o", "ö": "o", "ô": "o",
        "ú": "u", "ù": "u", "ü": "u", "û": "u",
        "ñ": "n"
    }

    lower = col.lower()
    for src, dst in replacements.items():
        lower = lower.replace(src, dst)

    lower = lower.replace("ãº", "u")
    lower = lower.replace("ã³", "o")
    lower = lower.replace("ã¡", "a")
    lower = lower.replace("ã­", "i")
    lower = lower.replace("ã±", "n")

    lower = re.sub(r"[^a-z0-9]+", "_", lower).strip("_")
    return lower


def parse_float(value):
    if pd.isna(value):
        return None

    text = str(value).strip()
    if text == "":
        return None

    text = text.replace(" ", "")

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", "")

    try:
        return float(text)
    except ValueError:
        return None


def parse_coordinate(value):
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    digits = text.replace(".", "").replace(",", "").strip()

    if not digits.replace("-", "").isdigit():
        return None

    if len(digits) < 4:
        return None

    normalized = digits[:2] + "." + digits[2:]
    return float(normalized)


def parse_month(value):
    text = normalize_text(value).lower()

    month_map = {
        "1": 1, "01": 1, "enero": 1, "ene": 1,
        "2": 2, "02": 2, "febrero": 2, "feb": 2,
        "3": 3, "03": 3, "marzo": 3, "mar": 3,
        "4": 4, "04": 4, "abril": 4, "abr": 4,
        "5": 5, "05": 5, "mayo": 5, "may": 5,
        "6": 6, "06": 6, "junio": 6, "jun": 6,
        "7": 7, "07": 7, "julio": 7, "jul": 7,
        "8": 8, "08": 8, "agosto": 8, "ago": 8,
        "9": 9, "09": 9, "septiembre": 9, "sep": 9, "setiembre": 9,
        "10": 10, "octubre": 10, "oct": 10,
        "11": 11, "noviembre": 11, "nov": 11,
        "12": 12, "diciembre": 12, "dic": 12
    }

    return month_map.get(text)


def build_date_observed(row):
    anio = normalize_text(row.get("AÑO"))
    mes = normalize_text(row.get("MES"))
    month_num = parse_month(mes)
    if anio and month_num:
        try:
            dt = datetime(int(anio), int(month_num), 1)
            return dt.strftime("%Y-%m-%dT00:00:00Z")
        except Exception as e:
            print(f"[ERROR PARSE ANIO/MES] ANIO=[{anio!r}] MES=[{mes!r}] error={e}")
            raise

    raise ValueError(
        f"No se pudo construir dateObserved. Valores recibidos: "
        f"ANIO={anio!r}, MES={mes!r}"
    )


def build_period(row):
    anio = normalize_text(row.get("AÑO"))
    mes = normalize_text(row.get("MES"))

    if anio and mes:
        month_num = parse_month(mes)
        if month_num:
            return f"{anio}-{str(month_num).zfill(2)}"

    return ""


def build_name(row):
    building = normalize_text(row.get("EDIFICIO"))
    measurement_type = normalize_text(row.get("TIPO"))

    if building and measurement_type:
        return f"{building} - {measurement_type}"

    if building:
        return building

    if measurement_type:
        return measurement_type

    return "ACMeasurement"


def build_measurement_type(row):
    measurement_type = normalize_text(row.get("TIPO"))
    if measurement_type:
        return measurement_type

    return "monthlyEnergyConsumption"


def build_energy_unit(row):
    unit = normalize_text(row.get("UNIDADES"))
    if unit:
        return unit

    return "kWh"


def build_entity_id(row):
    base_id = normalize_text(row.get("ID"))
    sensor = normalize_text(row.get("SENSOR"))
    measurement_class = normalize_text(row.get("CLASE"))
    if not base_id:
        raise ValueError(
            f"No se puede construir el entity_id porque falta ID. "
            f"ID={base_id!r}"
        )

    parts = [base_id, sensor, measurement_class]
    raw_entity_id = "_".join([p for p in parts if p])
    safe_entity_id = re.sub(r"[^A-Za-z0-9:_-]", "_", raw_entity_id)

    return safe_entity_id


def transform_csv_to_ngsi(file_path):
    df = read_csv(file_path)

    # Validaciones mínimas sobre cabeceras originales
    required_cols = ["AÑO", "MES", "ID", "TIPOEDIFICIO", "EDIFICIO", "DIRECCION", "DISTRITO", "CÓDIGO DISTRITO", "BARRIO", "CÓDIGO BARRIO", "COORDENADA-X", "COORDENADA-Y", "LONGITUD", "LATITUD", "SENSOR", "TIPO", "CLASE", "GRUPO", "UNIDADES", "CONSUMO"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el CSV: {missing}")

    entities = []
    discard_energy_none = 0
    discard_energy = 0
    discard_id_exception = 0
    for _, row in df.iterrows():
        consumo = row.get("CONSUMO")
        energy = parse_float(consumo)
        if energy is None:
            if consumo is None:
                discard_energy += 1
            else:
                discard_energy_none += 1
            continue
            # 511 registros que tienen "NO DATA" en consumo
        try:
            entity_id = build_entity_id(row)
        except Exception:
            print ("entity_id Exception")
            discard_id_exception += 1
            continue

        lat = parse_coordinate(row.get("LATITUD")) if "LATITUD" in df.columns else None
        lon = parse_coordinate(row.get("LONGITUD")) if "LONGITUD" in df.columns else None
        coordinates = [lon, lat] if lat is not None and lon is not None else None
        building_id = normalize_text(row.get("ID"))
        building_name = normalize_text(row.get("EDIFICIO"))
        address = normalize_text(row.get("DIRECCION"))
        measurement_type = build_measurement_type(row)
        energy_unit = build_energy_unit(row)
        period = build_period(row)
        name = build_name(row)
        date_observed = build_date_observed(row)
        district = normalize_text(row.get("DISTRITO"))
        neighborhood = normalize_text(row.get("BARRIO"))
        sensor = normalize_text(row.get("SENSOR"))
        sensor_type = normalize_text(row.get("TIPO"))
        measurement_class = normalize_text(row.get("CLASE"))
        measurement_group = normalize_text(row.get("GRUPO"))

        entity = build_entity_from_template(
            ENTITY_TEMPLATE,
            {
                "entity_id": entity_id,
                "name": name,
                "dateObserved": date_observed,
                "buildingId": building_id,
                "buildingName": building_name,
                "address": address,
                "measurementType": measurement_type,
                "energy": energy,
                "energyUnit": energy_unit,
                "period": period,
                "source": SOURCE_URL,
                "coordinates": coordinates,
                "district": district,
                "neighborhood": neighborhood,
                "sensor": sensor,
                "sensorType": sensor_type,
                "measurementClass": measurement_class,
                "measurementGroup": measurement_group
            }
        )

        entities.append(entity)

    print(f"Descartadas por CONSUMO no parseable: {discard_energy}")
    print(f"Descartadas por CONSUMO vacio: {discard_energy_none}")
    print(f"Descartadas por error en ID: {discard_id_exception}")
    print(f"Total filas CSV: {len(df)}")
    print(f"Entidades generadas: {len(entities)}")
    return entities