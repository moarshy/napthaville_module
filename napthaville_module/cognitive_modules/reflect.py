import json
from napthaville.persona.persona import Persona
from napthaville.persona.cognitive_modules.reflect import reflect
from napthaville_module.utils import (
    PERSONAS_FOLDER,
    ALL_PERSONAS,
    _check_persona
)


def get_reflect(task_params: dict):
    debug = task_params.get('debug', False)
    if debug:
        PERSONAS_FOLDER = '/Users/arshath/play/playground/gen_agents/storage_and_statics/storage/July1_the_ville_isabella_maria_klaus-step-3-1/personas'

    init_persona_name = task_params['init_persona_name']
    exists = _check_persona(init_persona_name)
    if not exists:
        res = {
            "error": f"Persona {init_persona_name} not found. Please choose from {ALL_PERSONAS}"
        }
        return json.dumps(res)

    persona_folder = f"{PERSONAS_FOLDER}/{init_persona_name}"
    persona = Persona(init_persona_name, persona_folder)

    return json.dumps(reflect(persona))


if __name__ == "__main__":
    task_params = {
        "init_persona_name": "Isabella Rodriguez",
        "debug": True
    }
    print(get_reflect(task_params))