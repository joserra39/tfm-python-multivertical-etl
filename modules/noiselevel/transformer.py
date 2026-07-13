import os
import pandas as pd

from modules.common.entity_builder import (
    load_entity_template,
    build_entity_from_template
)
from modules.common.time_utils import build_iso_datetime

ENTITY_TEMPLATE = load_entity_template(
    os.path.join(os.path.dirname(__file__), "entity.json")
)

SOURCE_URL = "https://datos.madrid.es"

NOISE_TYPE_CONFIG = {
    "D": ("day", 7, 0),
    "E": ("evening", 19, 0),
    "N": ("night", 23, 0),
    "T": ("total", 23, 59)
}

def read_csv_with_fallback(file_path):
    encodings = ["utf-8", "cp1252", "latin1"]
    last_error = None

    for encoding in encodings:
        try:
            return pd.read_csv(file_path, sep=";", dtype=str, encoding=encoding)
        except UnicodeDecodeError as e:
            last_error = e

    raise last_error

def parse_decimal(value):
    if pd.isna(value):
        return None

    if isinstance(value, str):
        value = value.strip().replace(",", ".")
        if value == "":
            return None

    return float(value)

def normalize_columns(df):
    rename_map = {}

    for col in df.columns:
        normalized = col.strip()
        lower = normalized.lower()

        if lower in ["año", "ańo", "ano"]:
            rename_map[col] = "ANO"
        elif lower == "mes":
            rename_map[col] = "MES"
        elif lower == "dia":
            rename_map[col] = "DIA"
        elif lower == "nmt":
            rename_map[col] = "NMT"
        elif lower == "tipo":
            rename_map[col] = "TIPO"
        else:
            rename_map[col] = normalized

    return df.rename(columns=rename_map)

def build_noise_attributes(row):
    attrs = {}

    for field in ["LAeq", "L1", "L10", "L50", "L90", "L99"]:
        value = parse_decimal(row.get(field))
        if value is not None:
            attrs[field] = {
                "type": "Number",
                "value": value,
                "metadata": {
                    "unitCode": {"value": "dbA"}
                }
            }

    return attrs

def load_stations_info(static_csv_path):
    df = read_csv_with_fallback(static_csv_path)

    required_cols = ["id", "name", "lon", "lat", "heightAverage", "address"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en datos_estaticos.csv: {missing}")

    stations = {}

    for _, row in df.iterrows():
        station_id = str(row["id"]).strip()
        stations[station_id] = {
            "name": str(row["name"]).strip(),
            "coords": [
                parse_decimal(row["lon"]) or 0.0,
                parse_decimal(row["lat"]) or 0.0
            ],
            "heightAverage": parse_decimal(row["heightAverage"]),
            "address": str(row["address"]).strip() if not pd.isna(row["address"]) else ""
        }

    return stations


def transform_csv_to_ngsi(file_path):
    df = read_csv_with_fallback(file_path)
    df = normalize_columns(df)

    static_data_path = os.path.join(
        os.path.dirname(file_path),
        "datos_estaticos",
        "datos_estaticos.csv"
    )
    stations_info = load_stations_info(static_data_path)

    required_cols = ["NMT", "ANO", "MES", "DIA", "TIPO", "LAeq", "L1", "L10", "L50", "L90", "L99"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el CSV: {missing}")

    entities = []

    for _, row in df.iterrows():
        station_id = str(row["NMT"]).strip()
        station_info = stations_info.get(
            station_id,
            {
                "name": f"Estación {station_id}",
                "coords": [0.0, 0.0],
                "heightAverage": None,
                "address": ""
            }
        )

        noise_type_raw = str(row["TIPO"]).strip().upper()
        noise_type, hour, minute = NOISE_TYPE_CONFIG.get(
            noise_type_raw,
            (noise_type_raw.lower(), 0, 0)
        )

        date_observed = build_iso_datetime(
            year=int(row["ANO"]),
            month=int(row["MES"]),
            day=int(row["DIA"]),
            hour=hour,
            minute=minute
        )

        entity = build_entity_from_template(
            ENTITY_TEMPLATE,
            {
                "station_id": station_id,
                "dateObserved": date_observed,
                "coordinates": station_info["coords"],
                "station_name": station_info["name"],
                "source": SOURCE_URL
            }
        )

        entity.update(build_noise_attributes(row))
        entities.append(entity)

    print(f"Entidades generadas: {len(entities)}")
    return entities