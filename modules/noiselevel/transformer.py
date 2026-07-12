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

STATIONS_INFO = {
    "1":  {"name": "Paseo de Recoletos",       "coords": [-3.691877, 40.422599]},
    "2":  {"name": "Carlos V",                 "coords": [-3.691509, 40.409121]},
    "3":  {"name": "Plaza del Carmen",         "coords": [-3.703175, 40.419251]},
    "4":  {"name": "Plaza de España",          "coords": [-3.712253, 40.424005]},
    "5":  {"name": "Barrio del Pilar",         "coords": [-3.711543, 40.478197]},
    "6":  {"name": "Gregorio Marañón",         "coords": [-3.690758, 40.437548]},
    "8":  {"name": "Escuelas Aguirre",         "coords": [-3.682377, 40.421575]},
    "10": {"name": "Cuatro Caminos",           "coords": [-3.707157, 40.445581]},
    "11": {"name": "Ramón y Cajal",            "coords": [-3.677359, 40.451522]},
    "12": {"name": "Manuel Becerra",           "coords": [-3.668584, 40.428741]},
    "13": {"name": "Vallecas",                 "coords": [-3.651506, 40.388116]},
    "14": {"name": "Plaza Elíptica",           "coords": [-3.718807, 40.384978]},
    "16": {"name": "Arturo Soria",             "coords": [-3.639284, 40.440013]},
    "17": {"name": "Villaverde",               "coords": [-3.713312, 40.347100]},
    "18": {"name": "Farolillo",                "coords": [-3.731786, 40.394788]},
    "19": {"name": "Alto de Extremadura",      "coords": [-3.741950, 40.407871]},
    "20": {"name": "Avenida de Moratalaz",     "coords": [-3.645215, 40.408028]},
    "24": {"name": "Casa de Campo",            "coords": [-3.747319, 40.419390]},
    "25": {"name": "Santa Eugenia",            "coords": [-3.602561, 40.379072]},
    "26": {"name": "Embajada",                 "coords": [-3.580128, 40.459331]},
    "27": {"name": "Barajas Pueblo",           "coords": [-3.580101, 40.476929]},
    "28": {"name": "Cuatro Vientos",           "coords": [-3.777830, 40.375250]},
    "29": {"name": "El Pardo",                 "coords": [-3.774551, 40.517989]},
    "30": {"name": "Campo de las Naciones",    "coords": [-3.616317, 40.460761]},
    "31": {"name": "Sanchinarro",              "coords": [-3.660454, 40.494254]},
    "47": {"name": "Méndez Álvaro",            "coords": [-3.686808, 40.398022]},
    "48": {"name": "Castellana",               "coords": [-3.690302, 40.439854]},
    "50": {"name": "Plaza Castilla",           "coords": [-3.688719, 40.465628]},
    "54": {"name": "Ensanche de Vallecas",     "coords": [-3.612100, 40.372993]},
    "55": {"name": "Urb Embajada 2",           "coords": [-3.580599, 40.462298]},
    "86": {"name": "Tres Olivos",              "coords": [-3.689643, 40.500598]}
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

def transform_csv_to_ngsi(file_path):
    df = read_csv_with_fallback(file_path)
    df = normalize_columns(df)

    required_cols = ["NMT", "ANO", "MES", "DIA", "TIPO", "LAeq", "L1", "L10", "L50", "L90", "L99"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el CSV: {missing}")

    entities = []

    for _, row in df.iterrows():
        station_id = str(row["NMT"]).strip()
        station_info = STATIONS_INFO.get(
            station_id,
            {"name": f"Estación {station_id}", "coords": [0.0, 0.0]}
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