import json
from napthaville.persona.persona import Persona
from napthaville.maze import Maze
from napthaville.persona.cognitive_modules.execute import execute
from napthaville_module.utils import (
    PERSONAS_FOLDER,
    ALL_PERSONAS,
    _check_persona,
    MAZE_FOLDER
)


def get_execute(task_params: dict):
    init_persona_name = task_params['init_persona_name']
    exists = _check_persona(init_persona_name)
    if not exists:
        res = {
            "error": f"Persona {init_persona_name} not found. Please choose from {ALL_PERSONAS}"
        }
        return json.dumps(res)
    
    # prepare persona
    persona_folder = f"{PERSONAS_FOLDER}/{init_persona_name}"
    persona = Persona(init_persona_name, persona_folder)

    # prepare maze
    maze = Maze(
        maze_name="maze_1",
        maze_folder=MAZE_FOLDER
    )

    persona_names_curr_tile = task_params['persona_names_curr_tile']

    plan = task_params['plan']

    execute_response = execute(persona, maze, persona_names_curr_tile, plan)
    print(execute_response)

    return json.dumps(execute_response)
