import json
from napthaville.persona.memory_structures.associative_memory import ConceptNode
from napthaville.persona.persona import Persona
from napthaville.persona.cognitive_modules.retrieve import retrieve
from napthaville_module.utils import (
    PERSONAS_FOLDER,
    ALL_PERSONAS,
    _check_persona
)


def get_retrieved_events(task_params: dict):
    debug = task_params.get('debug', False)
    if debug:
        PERSONAS_FOLDER = '/Users/arshath/play/playground/gen_agents/storage_and_statics/storage/July1_the_ville_isabella_maria_klaus-step-3-1/personas'

    exists = _check_persona(task_params['init_persona_name'])

    if not exists:
        res = {
            "error": f"Persona {task_params['init_persona_name']} not found. Please choose from {ALL_PERSONAS}"
        }
        return json.dumps(res)

    persona_folder = f"{PERSONAS_FOLDER}/{task_params['init_persona_name']}"
    persona = Persona(task_params["init_persona_name"], persona_folder)
    perceived_events = json.loads(task_params["perceived_events"])
    perceived_events = [ConceptNode.from_dict(event) for event in perceived_events]

    retrieved_events = retrieve(persona, perceived_events)

    return json.dumps(retrieved_events)