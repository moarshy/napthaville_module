import json
from napthaville.persona.cognitive_modules.perceive import perceive
from napthaville.maze import Maze
from napthaville.persona.persona import Persona
from napthaville_module.utils import (
    PERSONAS_FOLDER,
    MAZE_FOLDER,
    ALL_PERSONAS,
    _check_persona
)

def get_perception(task_params: dict):
    exists = _check_persona(task_params['init_persona_name'])

    if not exists:
        res = {
            "error": f"Persona {task_params['init_persona_name']} not found. Please choose from {ALL_PERSONAS}"
        } 
        return json.dumps(res)
    
    persona_folder = f"{PERSONAS_FOLDER}/{task_params['init_persona_name']}"
    persona = Persona(task_params["init_persona_name"], persona_folder)
    maze = Maze('maze', MAZE_FOLDER)

    ret_events = perceive(persona, maze)

    # Convert the ret_events to a list of dictionaries
    ret_events_list = []
    for event in ret_events:
        ret_events_list.append(event.to_dict())

    return json.dumps(ret_events_list)