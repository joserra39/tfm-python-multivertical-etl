import os
import re
import pandas as pd
from datetime import datetime

from modules.common.time_utils import parse_date
from modules.common.entity_builder import (
    load_entity_template,
    build_entity_from_template
)
from modules.common.isd_calculator import calculate_isd_crowdflow

ENTITY_TEMPLATE = load_entity_template(
    os.path.join(os.path.dirname(__file__), "entity.json")
)

def read_csv_with_fallback(file_path):
    encodings = ["utf-8", "cp1252", "latin1"]
    last_error = None

    for encoding in encodings:
        try:
            return pd.read_csv(file_path, sep=";", dtype=str, encoding=encoding)
        except UnicodeDecodeError as e:
            last_error = e

    raise last_error

def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()

def normalize_hour(hora_texto):
    hora_texto = normalize_text(hora_texto)

    parts = hora_texto.split(":")
    if len(parts) >= 2:
        h = parts[0].zfill(2)
        m = parts[1].zfill(2)
        return f"{h}:{m}"

    raise ValueError(f"Formato de HORA no válido: {hora_texto!r}")


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
    lower = lower.replace("codigo_postal", "codigo_postal")
    lower = re.sub(r"[^a-z0-9]+", "_", lower).strip("_")
    return lower


def normalize_columns(df):
    rename_map = {}

    for col in df.columns:
        norm = normalize_column_name(col)

        if norm in ["fecha"]:
            rename_map[col] = "FECHA"
        elif norm in ["hora"]:
            rename_map[col] = "HORA"
        elif norm in ["identificador"]:
            rename_map[col] = "IDENTIFICADOR"
        elif norm in ["peatones"]:
            rename_map[col] = "PEATONES"
        elif norm in ["bicicletas"]:
            rename_map[col] = "BICICLETAS"
        elif norm in ["device_id"]:
            rename_map[col] = "DEVICE_ID"
        elif norm in ["numero_distrito", "n_mero_distrito"]:
            rename_map[col] = "NUMERO_DISTRITO"
        elif norm in ["distrito"]:
            rename_map[col] = "DISTRITO"
        elif norm in ["direccion"]:
            rename_map[col] = "DIRECCION"
        elif norm in ["nombre_vial"]:
            rename_map[col] = "NOMBRE_VIAL"
        elif norm in ["numero"]:
            rename_map[col] = "NUMERO"
        elif norm in ["codigo_postal"]:
            rename_map[col] = "CODIGO_POSTAL"
        elif norm in ["observaciones_direccion"]:
            rename_map[col] = "OBSERVACIONES_DIRECCION"
        elif norm in ["latitud", "latitude"]:
            rename_map[col] = "LATITUD"
        elif norm in ["longitud", "longitude"]:
            rename_map[col] = "LONGITUD"
        else:
            rename_map[col] = col.strip()

    return df.rename(columns=rename_map)


def parse_int(value):
    if pd.isna(value):
        return None

    text = str(value).strip()
    if text == "":
        return None

    text = text.replace(".", "").replace(",", "")
    return int(text)


def parse_coordinate(value):
    if pd.isna(value):
        return None

    text = str(value).strip()
    if text == "":
        return None

    if "," in text and "." not in text:
        return float(text.replace(",", "."))

    sign = -1 if text.startswith("-") else 1
    digits = text.replace("-", "").replace(".", "").replace(",", "")

    if not digits.isdigit():
        return None

    if len(digits) >= 7:
        integer_part = digits[:2] if len(digits) >= 8 else digits[:1]
        decimal_part = digits[2:] if len(digits) >= 8 else digits[1:]
        return sign * float(f"{integer_part}.{decimal_part}")

    return sign * float(text.replace(",", "."))


def build_date_observed(row):
    fecha = normalize_text(row.get("FECHA"))
    hora = normalize_hour(row.get("HORA", "00:00"))
    solo_fecha = fecha.split(maxsplit=1)[0]
    fecha_hora = f"{solo_fecha} {hora}"

    try:
        return parse_date(fecha_hora)
    except Exception as e:
        print(f"[ERROR PARSE FECHA/HORA] FECHA=[{fecha!r}] | HORA=[{hora!r}] | FECHA_HORA=[{fecha_hora!r}] | error={e}")
        raise


def build_address(row):
    direccion = normalize_text(row.get("DIRECCION"))
    if direccion:
        return direccion

    nombre_vial = normalize_text(row.get("NOMBRE_VIAL"))
    numero = normalize_text(row.get("NUMERO"))
    codigo_postal = normalize_text(row.get("CODIGO_POSTAL"))

    parts = [p for p in [nombre_vial, numero] if p]
    address = " ".join(parts)

    if codigo_postal:
        address = f"{address}, {codigo_postal} Madrid" if address else f"{codigo_postal} Madrid"

    return address


def detect_category_and_intensity(row):
    peatones = parse_int(row.get("PEATONES"))
    bicicletas = parse_int(row.get("BICICLETAS"))

    if peatones is not None:
        return "Peatones", peatones

    if bicicletas is not None:
        return "Bicicletas", bicicletas

    return None, None

def read_csv(file_path):
    return pd.read_csv(file_path, sep=";", dtype=str, encoding="utf-8")

def parse_decimal(value):
    if value is None or pd.isna(value):
        return None
    try:
        return float(str(value).replace(",", ".").strip())
    except (ValueError, TypeError):
        return None
    
def load_stations_info(static_csv_path):
    df = read_csv(static_csv_path)

    required_cols = ["id", "address", "lon", "lat", "district"]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en datos_estaticos.csv: {missing}")

    stations = {}

    for _, row in df.iterrows():
        station_id = str(row["id"]).strip()
        stations[station_id] = {
            "address": str(row["address"]).strip(),
            "coords": [
                parse_decimal(row["lon"]) or 0.0,
                parse_decimal(row["lat"]) or 0.0
            ],
            "district": str(row["district"]).strip() if not pd.isna(row["district"]) else ""
        }

    return stations

def transform_csv_to_ngsi(directory_path, file_path):

    stations_info = load_stations_info(
        os.path.join(
            directory_path,
            "datos_estaticos",
            "datos_estaticos.csv"
        )
    )
        
    df = read_csv_with_fallback(file_path)
    df = normalize_columns(df)

    required_cols = ["FECHA", "HORA", "IDENTIFICADOR", "LATITUD", "LONGITUD"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el CSV: {missing}")

    if "PEATONES" not in df.columns and "BICICLETAS" not in df.columns:
        raise ValueError("El CSV no contiene ni PEATONES ni BICICLETAS")

    entities = []
    previous_key = None
    for _, row in df.iterrows():
        identifier = normalize_text(row.get("IDENTIFICADOR"))
        station_info = stations_info.get(
            identifier,
            {
                "address": build_address(row),
                "coords": [parse_coordinate(row.get("LONGITUD")), parse_coordinate(row.get("LATITUD"))],
                "district": normalize_text(row.get("DISTRITO"))
            }
        )
        date_observed = build_date_observed(row)
        category, intensity = detect_category_and_intensity(row)
        direction = normalize_text(row.get("OBSERVACIONES_DIRECCION"))
        name = normalize_text(row.get("DEVICE_ID"))
        isd = calculate_isd_crowdflow(category, intensity)

        current_key = (identifier, date_observed)
        # El Ayto. de Madrid no está devolviendo la hora en UTC y, por este motivo, hay PK duplicados
        # Se ignora la segunda lectura con el mismo identificador-fecha_hora para que de fallo el .sql
        if current_key == previous_key:
            continue
        if category is None or intensity is None:
            continue

        previous_key  = current_key

        entity = build_entity_from_template(
            ENTITY_TEMPLATE,
            {
                "entity_id": f"{identifier}",
                "name": name,
                "dateObserved": date_observed,
                "coordinates": station_info["coords"],
                "district": station_info["district"],
                "address": station_info["address"],
                "category": category,
                "direction": direction,
                "intensity": intensity,
                "source": "Ayuntamiento de Madrid",
                "isd": isd
            }
        )

        entities.append(entity)

    print(f"Entidades generadas: {len(entities)}")
    return entities