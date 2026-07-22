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

# Mapeo de magnitudes (Código CSV -> (Magnitud, Cód. Unidad))
# Cód. Unidad:
#   Gases y Partículas -> µg/m3 -> GQ
#   CO / Hidrocarburos -> mg/m3 -> GP
MAGNITUDES_MAP = {
    1:   ("SO2", "GQ"),       # Dióxido de Azufre
    6:   ("CO", "GP"),        # Monóxido de Carbono
    7:   ("NO", "GQ"),        # Monóxido de Nitrógeno
    8:   ("NO2", "GQ"),       # Dióxido de Nitrógeno
    9:   ("PM25", "GQ"),      # Partículas < 2.5 µm
    10:  ("PM10", "GQ"),      # Partículas < 10 µm
    12:  ("NOx", "GQ"),       # Óxidos de Nitrógeno
    14:  ("O3", "GQ"),        # Ozono
    20:  ("TOL", "GQ"),       # Tolueno
    30:  ("BEN", "GQ"),       # Benceno
    35:  ("EBE", "GQ"),       # Etilbenceno
    37:  ("MXY", "GQ"),       # Metaxileno
    38:  ("PXY", "GQ"),       # Paraxileno
    39:  ("OXY", "GQ"),       # Ortoxileno
    42:  ("TCH", "GP"),       # Hidrocarburos totales (hexano)
    43:  ("CH4", "GP"),       # Metano
    44:  ("NMHC", "GP"),      # Hidrocarburos no metánicos (hexano)
    431: ("MPX", "GP")        # Metaparaxileno
}

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
    print(f"load_stations_info(static_csv_path): {static_csv_path}")
    df = read_csv(static_csv_path)

    required_cols = ["id", "name", "lon", "lat", "district"]
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
            "district": str(row["district"]).strip() if not pd.isna(row["district"]) else ""
        }

    return stations

def categoria_ica(nivel):
    categorias = {
        0: "Sin datos",
        1: "Buena",
        2: "Razonablemente buena",
        3: "Regular",
        4: "Desfavorable",
        5: "Muy desfavorable",
        6: "Extremadamente desfavorable"
    }
    return categorias.get(nivel)

def nivel_ica_so2(value):
    v = parse_decimal(value)
    if v is None:
        return 0
    if v <= 100:
        return 1
    if v <= 200:
        return 2
    if v <= 350:
        return 3
    if v <= 500:
        return 4
    if v <= 750:
        return 5
    return 6

def nivel_ica_no2(value):
    v = parse_decimal(value)
    if v is None:
        return 0
    if v <= 40:
        return 1
    if v <= 90:
        return 2
    if v <= 120:
        return 3
    if v <= 230:
        return 4
    if v <= 340:
        return 5
    return 6

def nivel_ica_pm25(value):
    v = parse_decimal(value)
    if v is None:
        return 0
    if v <= 10:
        return 1
    if v <= 20:
        return 2
    if v <= 25:
        return 3
    if v <= 50:
        return 4
    if v <= 75:
        return 5
    return 6

def nivel_ica_pm10(value):
    v = parse_decimal(value)
    if v is None:
        return 0
    if v <= 20:
        return 1
    if v <= 40:
        return 2
    if v <= 50:
        return 3
    if v <= 100:
        return 4
    if v <= 150:
        return 5
    return 6

def nivel_ica_o3(value):
    v = parse_decimal(value)
    if v is None:
        return 0
    if v <= 50:
        return 1
    if v <= 100:
        return 2
    if v <= 130:
        return 3
    if v <= 240:
        return 4
    if v <= 380:
        return 5
    return 6

def calculate_ica_levels_and_categories(values):
    niveles = {
        "nivelIcaSO2": nivel_ica_so2(values.get("SO2")),
        "nivelIcaNO2": nivel_ica_no2(values.get("NO2")),
        "nivelIcaPM25": nivel_ica_pm25(values.get("PM25")),
        "nivelIcaPM10": nivel_ica_pm10(values.get("PM10")),
        "nivelIcaO3": nivel_ica_o3(values.get("O3"))
    }

    nivel_general = max(niveles.values())

    categorias = {
        "categoriaIcaSO2": categoria_ica(niveles["nivelIcaSO2"]),
        "categoriaIcaNO2": categoria_ica(niveles["nivelIcaNO2"]),
        "categoriaIcaPM25": categoria_ica(niveles["nivelIcaPM25"]),
        "categoriaIcaPM10": categoria_ica(niveles["nivelIcaPM10"]),
        "categoriaIcaO3": categoria_ica(niveles["nivelIcaO3"]),
        "categoriaIcaGeneral": categoria_ica(nivel_general)
    }

    return {
        **niveles,
        "nivelIcaGeneral": nivel_general,
        **categorias
    }

def calculate_isd_airquality(nivelIcaGeneral):
    try:
        nivel = int(nivelIcaGeneral)
    except (TypeError, ValueError):
        return None

    if nivel <= 1:
        return 1.0

    if nivel >= 6:
        return 0.0

    isd = (6 - nivel) / 5
    return round(max(0.0, min(1.0, isd)), 4)

def transform_csv_to_ngsi(file_path):

    print(f"os.path.dirname(file_path): {os.path.dirname(file_path)}")
    stations_info = load_stations_info(
        os.path.join(
            os.path.dirname(file_path),
            "../datos_estaticos",
            "datos_estaticos.csv"
        )
    )

    df = pd.read_csv(file_path, sep=';')

    id_vars = ['PROVINCIA', 'MUNICIPIO', 'ESTACION', 'MAGNITUD', 'ANO', 'MES', 'DIA']
    h_cols = [f'H{i:02d}' for i in range(1, 25)]
    v_cols = [f'V{i:02d}' for i in range(1, 25)]

    df_values = df.melt(id_vars=id_vars, value_vars=h_cols, var_name='HORA', value_name='VALOR')
    df_values['HORA'] = df_values['HORA'].str.replace('H', '').astype(int)

    df_valid = df.melt(id_vars=id_vars, value_vars=v_cols, var_name='HORA_V', value_name='VALIDO')
    df_valid['HORA'] = df_valid['HORA_V'].str.replace('V', '').astype(int)

    df_long = pd.merge(df_values, df_valid, on=id_vars + ['HORA'])
    df_long = df_long[df_long['VALIDO'] == 'V']

    entities = []

    grouped = df_long.groupby(['PROVINCIA', 'MUNICIPIO', 'ESTACION', 'ANO', 'MES', 'DIA', 'HORA'])

    for (prov, muni, esta, ano, mes, dia, hora), group in grouped:
        est_id_8 = f"{int(prov):02d}{int(muni):03d}{int(esta):03d}"

        station_info = stations_info.get(
            est_id_8,
            {
                "name": f"Estación {est_id_8}",
                "coords": [0.0, 0.0],
                "district": ""
            }
        )

        date_observed = build_iso_datetime(
            year=int(ano),
            month=int(mes),
            day=int(dia),
            hour=int(hora)
        )

        pollutant_values = {
            "SO2": None,
            "NO2": None,
            "PM25": None,
            "PM10": None,
            "O3": None
        }

        extra_attrs = {}

        for _, row in group.iterrows():
            mag_id = int(row['MAGNITUD'])
            if mag_id in MAGNITUDES_MAP:
                attr_name, unit = MAGNITUDES_MAP[mag_id]
                attr_value = parse_decimal(row['VALOR'])

                if attr_value is None:
                    continue

                extra_attrs[attr_name] = {
                    "type": "Number",
                    "value": attr_value,
                    "metadata": {
                        "unitCode": {"value": unit}
                    }
                }

                if attr_name in pollutant_values:
                    pollutant_values[attr_name] = attr_value

        ica_data = calculate_ica_levels_and_categories(pollutant_values)
        isd = calculate_isd_airquality(ica_data["nivelIcaGeneral"])

        entity = build_entity_from_template(
            ENTITY_TEMPLATE,
            {
                "station_id": est_id_8,
                "dateObserved": date_observed,
                "coordinates": station_info["coords"],
                "station_name": station_info["name"],
                "source": "Ayuntamiento de Madrid",
                "district": station_info["district"],
                "nivelIcaSO2": ica_data["nivelIcaSO2"],
                "categoriaIcaSO2": ica_data["categoriaIcaSO2"],
                "nivelIcaNO2": ica_data["nivelIcaNO2"],
                "categoriaIcaNO2": ica_data["categoriaIcaNO2"],
                "nivelIcaPM25": ica_data["nivelIcaPM25"],
                "categoriaIcaPM25": ica_data["categoriaIcaPM25"],
                "nivelIcaPM10": ica_data["nivelIcaPM10"],
                "categoriaIcaPM10": ica_data["categoriaIcaPM10"],
                "nivelIcaO3": ica_data["nivelIcaO3"],
                "categoriaIcaO3": ica_data["categoriaIcaO3"],
                "nivelIcaGeneral": ica_data["nivelIcaGeneral"],
                "categoriaIcaGeneral": ica_data["categoriaIcaGeneral"],
                "isd": isd
            }
        )

        entity.update(extra_attrs)
        entities.append(entity)

    return entities