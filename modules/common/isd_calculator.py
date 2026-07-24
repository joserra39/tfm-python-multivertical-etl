# modules/common/isd_calculator.py

ENERGY_GOOD_THRESHOLD = 6732.25
ENERGY_BAD_THRESHOLD = 78369.40
TRANSPORT_PE_MAX_REFERENCE = 2300
TRANSPORT_BI_MAX_REFERENCE = 50
NOISE_GOOD_THRESHOLD = 55
NOISE_BAD_THRESHOLD = 75

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


# ---- Flujo de personas ----

def calculate_isd_crowdflow(category, intensity):
    if intensity is None:
        return None

    max_reference = {
        "Peatones": TRANSPORT_PE_MAX_REFERENCE,
        "Bicicletas": TRANSPORT_BI_MAX_REFERENCE
    }

    max_val = max_reference.get(category)
    if max_val is None or max_val <= 0:
        return None

    normalized = min(intensity / max_val, 1.0)

    isd = 1.0 - normalized

    return round(max(0.0, min(1.0, isd)), 4)


# ---- Nivel de ruido ----

def calculate_isd_noiselevel(laEq):
    if laEq <= NOISE_GOOD_THRESHOLD:
        return 1.0

    if laEq >= NOISE_BAD_THRESHOLD:
        return 0.0

    isd = (NOISE_BAD_THRESHOLD - laEq) / (NOISE_BAD_THRESHOLD - NOISE_GOOD_THRESHOLD)

    return round(max(0.0, min(1.0, isd)), 4)