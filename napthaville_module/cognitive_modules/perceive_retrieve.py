import json
from napthaville.persona.cognitive_modules.perceive import perceive
from napthaville.persona.cognitive_modules.retrieve import retrieve
from napthaville.maze import Maze
from napthaville.persona.persona import Persona
from napthaville_module.utils import (
    PERSONAS_FOLDER,
    MAZE_FOLDER,
    ALL_PERSONAS,
    _check_persona
)

def get_perceive_retrieve(task_params: dict):
    debug = task_params.get('debug', False)
    if debug:
        PERSONAS_FOLDER = '/Users/arshath/play/playground/gen_agents/storage_and_statics/storage/July1_the_ville_isabella_maria_klaus-step-3-1/personas'
        MAZE_FOLDER = '/Users/arshath/play/playground/gen_agents/storage_and_statics/the_ville/matrix'
    
    exists = _check_persona(task_params['init_persona_name'])

    if not exists:
        res = {
            "error": f"Persona {task_params['init_persona_name']} not found. Please choose from {ALL_PERSONAS}"
        } 
        return json.dumps(res)
    
    persona_folder = f"{PERSONAS_FOLDER}/{task_params['init_persona_name']}"
    persona = Persona(task_params["init_persona_name"], persona_folder)
    maze = Maze('maze', MAZE_FOLDER)

    perceived_events = perceive(persona, maze)
    retrieved_events = retrieve(persona, perceived_events)

    return json.dumps(retrieved_events)



if __name__ == "__main__":
    task_params = {
        "init_persona_name": "Isabella Rodriguez",
        "debug": True
    }
    print(get_perceive_retrieve(task_params))