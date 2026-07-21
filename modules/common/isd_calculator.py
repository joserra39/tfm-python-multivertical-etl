# modules/common/isd_calculator.py

ENERGY_GOOD_THRESHOLD = 6732.25
ENERGY_BAD_THRESHOLD = 78369.40


# ---- Energía ----

def calculate_isd_energy(energy):

    if energy <= ENERGY_GOOD_THRESHOLD:
        return 1.0

    if energy >= ENERGY_BAD_THRESHOLD:
        return 0.0

    isd = (ENERGY_BAD_THRESHOLD - energy) / (ENERGY_BAD_THRESHOLD - ENERGY_GOOD_THRESHOLD)
    return round(max(0.0, min(1.0, isd)), 4)

# ---- Calidad del Aire ----

def calculate_isd_airquality(nivelIcaGeneral):

    # AQUI debería calcularse el ISD en base al nivelIcaGeneral
    
    no2 = row_or_dict.get("NO2")
    pm10 = row_or_dict.get("PM10")
    pm25 = row_or_dict.get("PM25")
    o3 = row_or_dict.get("O3")

    scores = {
        "NO2": _normalize_inverse_linear(no2, good=0, bad=200),
        "PM10": _normalize_inverse_linear(pm10, good=0, bad=100),
        "PM25": _normalize_inverse_linear(pm25, good=0, bad=60),
        "O3": _normalize_inverse_linear(o3, good=0, bad=180),
    }

    weights = {
        "NO2": 0.35,
        "PM10": 0.25,
        "PM25": 0.25,
        "O3": 0.15,
    }

    return _weighted_mean(scores, weights)





# -------------------------------------------------------------

def clamp(value, min_value=0.0, max_value=100.0):
    return max(min_value, min(max_value, value))


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_inverse_linear(value, good, bad):
    v = _safe_float(value)
    if v is None or bad == good:
        return None
    score = 100.0 * (bad - v) / (bad - good)
    return clamp(score)


def _weighted_mean(values, weights):
    num = 0.0
    den = 0.0
    for key, w in weights.items():
        v = values.get(key)
        if v is None:
            continue
        num += v * w
        den += w
    if den == 0:
        return None
    return round(num / den, 2)





# ---- Ruido ----
def calculate_isd_noise(row_or_dict):
    leq_day = row_or_dict.get("leq_day")
    leq_night = row_or_dict.get("leq_night")

    scores = {
        "leq_day": _normalize_inverse_linear(leq_day, good=45, bad=80),
        "leq_night": _normalize_inverse_linear(leq_night, good=40, bad=75),
    }

    weights = {
        "leq_day": 0.5,
        "leq_night": 0.5,
    }

    return _weighted_mean(scores, weights)


# ---- Agua ----
def calculate_isd_water(row_or_dict):
    cod = row_or_dict.get("COD")
    bod5 = row_or_dict.get("BOD5")
    ss = row_or_dict.get("SS")
    nh4 = row_or_dict.get("NH4")

    scores = {
        "COD": _normalize_inverse_linear(cod, good=0, bad=1000),
        "BOD5": _normalize_inverse_linear(bod5, good=0, bad=500),
        "SS": _normalize_inverse_linear(ss, good=0, bad=600),
        "NH4": _normalize_inverse_linear(nh4, good=0, bad=50),
    }

    weights = {
        "COD": 0.25,
        "BOD5": 0.25,
        "SS": 0.25,
        "NH4": 0.25,
    }

    return _weighted_mean(scores, weights)


# ---- Aforo peatonal / bicicletas ----
def calculate_isd_crowdflow(row_or_dict):
    ped_density = row_or_dict.get("pedestrian_density")
    bike_density = row_or_dict.get("bike_density")

    scores = {
        "pedestrian_density": _normalize_inverse_linear(ped_density, good=0, bad=5.0),
        "bike_density": _normalize_inverse_linear(bike_density, good=0, bad=3.0),
    }

    weights = {
        "pedestrian_density": 0.55,
        "bike_density": 0.45,
    }

    return _weighted_mean(scores, weights)