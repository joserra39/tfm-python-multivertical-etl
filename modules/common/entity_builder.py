import json
import copy


def load_entity_template(template_path):
    with open(template_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_entity_from_template(template, values):
    """
    Sustituye placeholders {xxx} por valores reales
    """
    entity = copy.deepcopy(template)
    entity_str = json.dumps(entity)

    for key, value in values.items():
        entity_str = entity_str.replace(
            f"{{{key}}}",
            json.dumps(value) if isinstance(value, (list, dict)) else str(value)
        )

    return json.loads(entity_str)
