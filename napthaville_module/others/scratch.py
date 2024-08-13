import json
from napthaville.maze import Maze
from napthaville.persona.persona import Persona
from napthaville.utils import scratch_to_dict
from napthaville_module.utils import (
    PERSONAS_FOLDER,
    MAZE_FOLDER,
    ALL_PERSONAS,
    _check_persona
)


def get_scratch(task_params: dict):
    debug = task_params.get('debug', False)
    if debug:
        PERSONAS_FOLDER = '/Users/arshath/play/playground/gen_agents/storage_and_statics/storage/July1_the_ville_isabella_maria_klaus-step-3-1/personas'

    persona_name = task_params["persona_name"]
    exists = _check_persona(persona_name)

    if not exists:
        res = {
            "error": f"Persona {persona_name} not found. Please choose from {ALL_PERSONAS}"
        }
        return json.dumps(res)
    else:
        persona_folder = f"{PERSONAS_FOLDER}/{persona_name}"
        persona = Persona(persona_name, persona_folder)
        scratch = scratch_to_dict(persona.scratch)

    return json.dumps(scratch)


if __name__ == "__main__":
    task_params = {
        "persona_name": "Isabella Rodriguez",
        "debug": True
    }
    print(get_scratch(task_params))
