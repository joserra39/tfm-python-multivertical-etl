import os
import re
import pandas as pd
from datetime import datetime

from modules.common.entity_builder import (
    load_entity_template,
    build_entity_from_template
)

ENTITY_TEMPLATE = load_entity_template(
    os.path.join(os.path.dirname(__file__), "entity.json")
)

SOURCE_URL = "https://datos.madrid.es/dataset/300146-0-depuradoras-vertido/downloads"

MONTH_MAP = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12
}

PARAMETER_MAP = {
    "DBO5": "biochemicalOxygenDemand5",
    "SS": "suspendedSolids",
    "PT": "totalPhosphorus",
    "NT": "totalNitrogen"
}

def read_csv(file_path):
    return pd.read_csv(file_path, sep=";", dtype=str, encoding="utf-8")

def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def parse_decimal(value):
    if pd.isna(value):
        return None

    if isinstance(value, str):
        value = value.strip().replace(",", ".")
        if value == "":
            return None

    return float(value)


def clean_numeric_text(value):
    text = normalize_text(value)
    if not text:
        return None

    upper = text.upper()
    if upper in {"--", "NA", "N/A", ""}:
        return None

    text = text.replace(" ", "")

    if text.startswith("<"):
        text = text[1:]

    text = text.replace(",", ".")
    text = re.sub(r"[^0-9.\-]", "", text)

    if not text:
        return None

    return text


def parse_float(value):
    text = clean_numeric_text(value)
    if text is None:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def load_stations_info(static_csv_path):
    df = read_csv(static_csv_path)

    required_cols = ["id", "name", "lon", "lat"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en datos_estaticos.csv: {missing}")

    stations = {}

    for _, row in df.iterrows():
        station_id = str(row["id"]).strip()

        stations[station_id] = {
            "stationName": str(row["name"]).strip(),
            "location": [
                parse_decimal(row["lon"]) or 0.0,
                parse_decimal(row["lat"]) or 0.0
            ]
        }

    return stations


def parse_edar_parametro(value):
    text = normalize_text(value).replace(" ", "")
    if "_" not in text:
        raise ValueError(f"Formato EDAR_PARAMETRO inválido: {value!r}")

    station_code, parameter_code = text.split("_", 1)
    station_code = station_code.upper()
    parameter_code = parameter_code.upper()

    if parameter_code not in PARAMETER_MAP:
        raise ValueError(f"Parámetro desconocido: {parameter_code!r}")

    return station_code, parameter_code


def parse_period_column(column_name, default_year=None):
    text = normalize_text(column_name).lower()
    match = re.match(r"^(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(\d{2})$", text)
    if not match:
        return None

    month_code = match.group(1)
    half_code = match.group(2)
    month = MONTH_MAP[month_code]

    if half_code == "01":
        day = 1
        fortnight = "Primera quincena"
    elif half_code == "02":
        day = 15
        fortnight = "Segunda quincena"
    else:
        return None

    year = int(default_year) if default_year else datetime.utcnow().year
    date_observed = datetime(year, month, day).strftime("%Y-%m-%dT00:00:00Z")
    period = f"{year}-{str(month).zfill(2)}"

    return {
        "dateObserved": date_observed,
        "period": period,
        "fortnight": fortnight
    }


def infer_year_from_filename(file_path):
    filename = os.path.basename(file_path)
    match = re.search(r"(20\d{2})", filename)
    if match:
        return int(match.group(1))
    return None


def transform_csv_to_ngsi(static_data_directory_path, file_path):
    df = read_csv(file_path)

    static_data_path = os.path.join(
        os.path.dirname(static_data_directory_path),
        "datos_estaticos",
        "datos_estaticos.csv"
    )
    stations_info = load_stations_info(static_data_path)

    first_col = df.columns[0]
    if first_col not in {"EDAR_PARAMETRO", "EDAR_PARAMETRO (mg/l)"}:
        raise ValueError(f"Columna principal no esperada: {first_col!r}")

    period_columns = [c for c in df.columns if parse_period_column(c) is not None]
    if not period_columns:
        raise ValueError("No se encontraron columnas de periodos quincenales válidas")

    detected_year = infer_year_from_filename(file_path)
    if detected_year is None:
        detected_year = datetime.utcnow().year

    grouped_entities = {}

    for _, row in df.iterrows():
        station_code, parameter_code = parse_edar_parametro(row[first_col])
        attribute_name = PARAMETER_MAP[parameter_code]

        station_info = stations_info.get(
            station_code,
            {
                "stationName": f"EDAR {station_code}",
                "location": [0.0, 0.0]
            }
        )

        station_name = station_info["stationName"]
        location = station_info["location"]

        for period_col in period_columns:
            period_info = parse_period_column(period_col, default_year=detected_year)
            raw_value = row.get(period_col)
            numeric_value = parse_float(raw_value)

            if numeric_value is None:
                continue

            entity_key = (station_code, period_info["dateObserved"])

            if entity_key not in grouped_entities:
                grouped_entities[entity_key] = {
                    "entity_id": station_code,
                    "name": station_name,
                    "dateObserved": period_info["dateObserved"],
                    "period": period_info["period"],
                    "fortnight": period_info["fortnight"],
                    "source": SOURCE_URL,
                    "coordinates": location,
                    "biochemicalOxygenDemand5": 0,
                    "suspendedSolids": 0,
                    "totalPhosphorus": 0,
                    "totalNitrogen": 0
                }

            grouped_entities[entity_key][attribute_name] = numeric_value

    entities = []

    for _, payload in sorted(grouped_entities.items(), key=lambda x: x[0]):
        entity = build_entity_from_template(
            ENTITY_TEMPLATE,
            payload
        )
        entities.append(entity)

    print(f"Total filas CSV: {len(df)}")
    print(f"Entidades WaterQualityObserved generadas: {len(entities)}")

    return entities