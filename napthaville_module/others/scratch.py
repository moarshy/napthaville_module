import json
import os
from napthaville.persona.persona import Persona
from napthaville.utils import scratch_to_dict
from napthaville_module.utils import (
    ALL_PERSONAS,
    _check_persona
)


def get_scratch(task_params: dict):
    persona_name = task_params["persona_name"]
    sims_folder = task_params["sims_folder"]
    exists = _check_persona(persona_name)

    if not exists:
        res = {
            "error": f"Persona {persona_name} not found. Please choose from {ALL_PERSONAS}"
        }
        return json.dumps(res)
    
    persona_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{persona_name}"
    persona = Persona(persona_name, persona_folder)
    scratch = scratch_to_dict(persona.scratch)

    return json.dumps(scratch)
