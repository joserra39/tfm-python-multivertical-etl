import pandas as pd
import json
import os
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

# Diccionario de estaciones
# Mapeo que incluye códigos antiguos (versión corta) y nuevos (versión nacional)
ESTACIONES_INFO = {
    "28079003": {"name": "Pza. del Carmen", "coords": [-3.70317, 40.41921]},
    "28079035": {"name": "Pza. del Carmen", "coords": [-3.70317, 40.41921]},
    "28079005": {"name": "Barrio del Pilar", "coords": [-3.71157, 40.47823]},
    "28079039": {"name": "Barrio del Pilar", "coords": [-3.71157, 40.47823]},
    "28079010": {"name": "Cuatro Caminos", "coords": [-3.70713, 40.44554]},
    "28079038": {"name": "Cuatro Caminos", "coords": [-3.70713, 40.44554]},
    "28079013": {"name": "Vallecas", "coords": [-3.65172, 40.38815]},
    "28079040": {"name": "Vallecas", "coords": [-3.65172, 40.38815]},
    "28079020": {"name": "Moratalaz", "coords": [-3.64531, 40.40795]},
    "28079036": {"name": "Moratalaz", "coords": [-3.64531, 40.40795]},
    "28079015": {"name": "Pza. Castilla - Baja", "coords": [-3.68875, 40.46558]},
    "28079050": {"name": "Pza. Castilla - Alta", "coords": [-3.68882, 40.46558]},
    "28079001": {"name": "Paseo Recoletos", "coords": [-3.69231, 40.42155]},
    "28079002": {"name": "Glta. de Carlos V", "coords": [-3.69036, 40.40744]},
    "28079004": {"name": "Pza. de España", "coords": [-3.71226, 40.42388]},
    "28079006": {"name": "Pza. Dr. Marañón", "coords": [-3.69000, 40.43547]},
    "28079007": {"name": "Pza. M. de Salamanca", "coords": [-3.68250, 40.43042]},
    "28079008": {"name": "Escuelas Aguirre", "coords": [-3.68232, 40.42155]},
    "28079009": {"name": "Pza. Luca de Tena", "coords": [-3.69417, 40.40319]},
    "28079011": {"name": "Av. Ramón y Cajal", "coords": [-3.67735, 40.45147]},
    "28079012": {"name": "Pza. Manuel Becerra", "coords": [-3.66914, 40.43003]},
    "28079014": {"name": "Pza. Fdez. Ladreda", "coords": [-3.71536, 40.38829]},
    "28079016": {"name": "Arturo Soria", "coords": [-3.63924, 40.44005]},
    "28079017": {"name": "Villaverde Alto", "coords": [-3.71332, 40.34715]},
    "28079018": {"name": "C/ Farolillo", "coords": [-3.73183, 40.39478]},
    "28079019": {"name": "Huerta Castañeda", "coords": [-3.74306, 40.40808]},
    "28079021": {"name": "Pza. Cristo Rey", "coords": [-3.71764, 40.43855]},
    "28079022": {"name": "Paseo Pontones", "coords": [-3.71444, 40.40422]},
    "28079023": {"name": "Final C/ Alcalá", "coords": [-3.61634, 40.43851]},
    "28079024": {"name": "Casa de Campo", "coords": [-3.74735, 40.41936]},
    "28079025": {"name": "Santa Eugenia", "coords": [-3.60842, 40.38393]},
    "28079026": {"name": "Urb. Embajada", "coords": [-3.58000, 40.47194]},
    "28079027": {"name": "Barajas", "coords": [-3.58056, 40.47692]},
    "28079047": {"name": "Méndez Álvaro", "coords": [-3.68682, 40.39811]},
    "28079048": {"name": "Paseo Castellana", "coords": [-3.69056, 40.43989]},
    "28079049": {"name": "Retiro", "coords": [-3.68232, 40.41444]},
    "28079054": {"name": "Ensanche Vallecas", "coords": [-3.61214, 40.37301]},
    "28079055": {"name": "Urb. Embajada", "coords": [-3.58075, 40.46233]},
    "28079056": {"name": "Plaza Elíptica", "coords": [-3.71878, 40.38503]},
    "28079057": {"name": "Sanchinarro", "coords": [-3.66052, 40.49420]},
    "28079058": {"name": "El Pardo", "coords": [-3.77461, 40.51883]},
    "28079059": {"name": "Parque Juan Carlos I", "coords": [-3.60951, 40.46525]},
    "28079060": {"name": "Tres Olivos", "coords": [-3.68673, 40.50059]}
}

def transform_csv_to_ngsi(file_path):
    df = pd.read_csv(file_path, sep=';')
    
    # Normalizar columnas (Ancho a Largo)
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
    # Agrupamos por Estación, Año, Mes, Día y Hora para consolidar contaminantes
    grouped = df_long.groupby(['PROVINCIA', 'MUNICIPIO', 'ESTACION', 'ANO', 'MES', 'DIA', 'HORA'])

    for (prov, muni, esta, ano, mes, dia, hora), group in grouped:
        # Generar ID de 8 dígitos: 28 + 079 + XXX
        est_id_8 = f"{prov:02d}{muni:03d}{esta:03d}"
        station_info = ESTACIONES_INFO.get(est_id_8, {"name": f"Estación {est_id_8}", "coords": [0.0, 0.0]})
        
        # Fecha ISO (Restamos 1 a la hora porque H01 es la franja 00:00-01:00)
        # date_str = f"{ano:04d}-{mes:02d}-{dia:02d}T{hora-1:02d}:00:00"

        date_observed = build_iso_datetime(
            year=ano,
            month=mes,
            day=dia,
            hour=hora
        )

        entity = build_entity_from_template(
            ENTITY_TEMPLATE,
            {
                "station_id": est_id_8,
                "dateObserved": date_observed,
                "coordinates": station_info["coords"],
                "station_name": station_info["name"]
            }
        )
        
        # Añadir contaminantes
        for _, row in group.iterrows():
            mag_id = row['MAGNITUD']
            if mag_id in MAGNITUDES_MAP:
                attr_name, unit = MAGNITUDES_MAP[mag_id]
                entity[attr_name] = {
                    "type": "Number",
                    "value": float(row['VALOR']),
                    "metadata": {
                        "unitCode": {"value": unit}
                    }
                }
        
        entities.append(entity)
        
    return entities