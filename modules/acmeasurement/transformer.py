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


def normalize_columns(df):
    rename_map = {}

    for col in df.columns:
        norm = normalize_column_name(col)

        if norm in ["ano", "anio", "year"]:
            rename_map[col] = "ANIO"
        elif norm in ["mes", "month"]:
            rename_map[col] = "MES"
        elif norm in ["fecha", "date", "fecha_lectura", "fecha_medida", "periodo"]:
            rename_map[col] = "FECHA"
        elif norm in ["codigo_interno", "id", "identificador", "codigo_edificio", "centro_codigo"]:
            rename_map[col] = "IDENTIFICADOR"
        elif norm in ["edificio", "nombre_edificio", "centro", "nombre_centro", "equipamiento"]:
            rename_map[col] = "BUILDING"
        elif norm in ["direccion", "domicilio", "via", "calle"]:
            rename_map[col] = "DIRECCION"
        elif norm in ["distrito"]:
            rename_map[col] = "DISTRITO"
        elif norm in ["latitud", "latitude"]:
            rename_map[col] = "LATITUD"
        elif norm in ["longitud", "longitude"]:
            rename_map[col] = "LONGITUD"
        elif norm in ["consumo", "consumo_kwh", "energia", "energia_kwh", "electricidad_kwh", "valor"]:
            rename_map[col] = "ENERGY"
        elif norm in ["unidad", "unidad_medida"]:
            rename_map[col] = "ENERGY_UNIT"
        elif norm in ["tipo", "tipo_medida", "magnitud", "vector_energetico", "suministro"]:
            rename_map[col] = "MEASUREMENT_TYPE"
        else:
            rename_map[col] = col.strip()

    return df.rename(columns=rename_map)


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
    fecha = normalize_text(row.get("FECHA"))
    anio = normalize_text(row.get("ANIO"))
    mes = normalize_text(row.get("MES"))

    if fecha:
        try:
            return parse_date(fecha)
        except Exception:
            pass

        try:
            dt = pd.to_datetime(fecha, dayfirst=True, errors="coerce")
            if pd.notna(dt):
                return dt.strftime("%Y-%m-%dT00:00:00Z")
        except Exception:
            pass

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
        f"FECHA={fecha!r}, ANIO={anio!r}, MES={mes!r}"
    )


def build_period(row):
    fecha = normalize_text(row.get("FECHA"))
    anio = normalize_text(row.get("ANIO"))
    mes = normalize_text(row.get("MES"))

    if anio and mes:
        month_num = parse_month(mes)
        if month_num:
            return f"{anio}-{str(month_num).zfill(2)}"

    if fecha:
        try:
            dt = pd.to_datetime(fecha, dayfirst=True, errors="coerce")
            if pd.notna(dt):
                return dt.strftime("%Y-%m")
        except Exception:
            pass

    return ""


def build_name(row):
    building = normalize_text(row.get("BUILDING"))
    measurement_type = normalize_text(row.get("MEASUREMENT_TYPE"))

    if building and measurement_type:
        return f"{building} - {measurement_type}"

    if building:
        return building

    if measurement_type:
        return measurement_type

    return "ACMeasurement"


def build_measurement_type(row):
    measurement_type = normalize_text(row.get("MEASUREMENT_TYPE"))
    if measurement_type:
        return measurement_type

    return "monthlyEnergyConsumption"


def build_energy_unit(row):
    unit = normalize_text(row.get("ENERGY_UNIT"))
    if unit:
        return unit

    return "kWh"


def build_entity_id(row, date_observed):
    identifier = normalize_text(row.get("IDENTIFICADOR"))
    building = normalize_text(row.get("BUILDING"))
    period = build_period(row)

    base_id = identifier or building
    if not base_id:
        raise ValueError("No existe identificador suficiente para construir el id de la entidad")

    safe_base_id = re.sub(r"[^A-Za-z0-9:_-]", "_", base_id)
    safe_period = re.sub(r"[^A-Za-z0-9:_-]", "_", period) if period else date_observed[:10]

    return f"ACMeasurement:{safe_base_id}:{safe_period}"


def transform_csv_to_ngsi(file_path):
    df = read_csv(file_path)
    df = normalize_columns(df)

    if "ENERGY" not in df.columns:
        raise ValueError("El CSV no contiene una columna reconocible de consumo/energía")

    if "FECHA" not in df.columns and ("ANIO" not in df.columns or "MES" not in df.columns):
        raise ValueError("El CSV debe contener FECHA o bien ANIO y MES")

    entities = []
    seen_ids = set()

    for _, row in df.iterrows():
        energy = parse_float(row.get("ENERGY"))
        if energy is None:
            continue

        try:
            date_observed = build_date_observed(row)
        except Exception:
            continue

        lat = parse_coordinate(row.get("LATITUD")) if "LATITUD" in df.columns else None
        lon = parse_coordinate(row.get("LONGITUD")) if "LONGITUD" in df.columns else None

        try:
            entity_id = build_entity_id(row, date_observed)
        except Exception:
            continue

        if entity_id in seen_ids:
            continue

        seen_ids.add(entity_id)

        coordinates = [lon, lat] if lat is not None and lon is not None else None
        building = normalize_text(row.get("BUILDING"))
        address = normalize_text(row.get("DIRECCION"))
        area_served = normalize_text(row.get("DISTRITO"))
        measurement_type = build_measurement_type(row)
        energy_unit = build_energy_unit(row)
        period = build_period(row)
        name = build_name(row)

        entity_data = {
            "entity_id": entity_id,
            "name": name,
            "dateObserved": date_observed,
            "building": building,
            "address": address,
            "areaServed": area_served,
            "measurementType": measurement_type,
            "energy": energy,
            "energyUnit": energy_unit,
            "period": period,
            "source": SOURCE_URL
        }

        if coordinates is not None:
            entity_data["coordinates"] = coordinates

        entity = build_entity_from_template(
            ENTITY_TEMPLATE,
            entity_data
        )

        entities.append(entity)

    print(f"Entidades generadas: {len(entities)}")
    return entities