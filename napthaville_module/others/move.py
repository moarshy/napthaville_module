import json
from datetime import datetime
from napthaville.maze import Maze
from napthaville.persona.persona import Persona
from napthaville.persona.cognitive_modules.perceive import perceive
from napthaville.persona.cognitive_modules.retrieve import retrieve
from napthaville.persona.cognitive_modules.reflect import reflect
from napthaville.persona.cognitive_modules.execute import execute
from napthaville.persona.cognitive_modules.plan import plan as cognitive_plan
from napthaville.utils import dict_to_scratch, DateTimeEncoder
from napthaville_module.utils import (
    PERSONAS_FOLDER,
    MAZE_FOLDER,
    ALL_PERSONAS,
    _check_persona,
)


def get_move(task_params: dict):
    debug = task_params['debug']
    if debug:
        PERSONAS_FOLDER = '/Users/arshath/play/playground/gen_agents/storage_and_statics/storage/July1_the_ville_isabella_maria_klaus-step-3-1/personas'
        MAZE_FOLDER = '/Users/arshath/play/playground/gen_agents/storage_and_statics/the_ville/matrix'

    # prepare task params
    curr_tile = task_params['curr_tile']
    curr_time = task_params['curr_time']

    # prepare init persona
    init_persona_name = task_params['init_persona_name']
    if not _check_persona(init_persona_name):
        return json.dumps({"error": f"Persona {init_persona_name} not found. Please choose from {ALL_PERSONAS}"})
    
    persona_folder = f"{PERSONAS_FOLDER}/{init_persona_name}"
    init_persona = Persona(init_persona_name, persona_folder)

    # prepare personas
    _personas = json.loads(task_params['personas'])
    personas = {}
    for persona_name, persona_dict in _personas.items():
        personas[persona_name] = dict_to_scratch(persona_dict)

    # prepare maze
    maze = Maze('maze', MAZE_FOLDER)

    init_persona.scratch.curr_tile = curr_tile

    new_day = False
    if not init_persona.scratch.curr_time:
        new_day = "First day"
    elif init_persona.scratch.curr_time.strftime("%A %B %d") != curr_time.strftime("%A %B %d"):
        new_day = "New day"

    init_persona.scratch.curr_time = curr_time

    # perceive
    perceived = perceive(
        persona=init_persona,
        maze=maze
    )

    # retrieve
    retrieved = retrieve(
        persona=init_persona,
        perceived=perceived
    )

    plan = cognitive_plan(
        persona=init_persona,
        maze=maze,
        personas=personas,
        new_day=new_day,
        retrieved=retrieved
    )

    # reflection
    reflect(init_persona)

    # TODO: at this point, we should save the persona to the database??

    # execute
    persona_names_curr_tile = {}
    for persona_name, persona in personas.items():
        persona_names_curr_tile[persona_name] = persona['curr_tile']

    execute_response = execute(
        persona=init_persona,
        maze=maze,
        persona_names_curr_tile=persona_names_curr_tile,
        plan=plan
    )

    return json.dumps(execute_response)


if __name__ == "__main__":
    
    personas = [
        "Isabella Rodriguez",
        "Maria Lopez",
        "Klaus Mueller"
    ]
    
    personas_folder = f"/Users/arshath/play/playground/gen_agents/storage_and_statics/storage/July1_the_ville_isabella_maria_klaus-step-3-8/personas"

    personas_dict = {}
    for persona in personas:
        persona_folder = f"{personas_folder}/{persona}"
        persona = Persona(persona, persona_folder)
        personas_dict[persona.name] = dict_to_scratch(persona.scratch.to_dict())

    init_persona = Persona(
        'Isabella Ridriguez',
        '/Users/arshath/play/playground/gen_agents/storage_and_statics/storage/July1_the_ville_isabella_maria_klaus-step-3-1/personas/Isabella Rodriguez'
    )

    task_params = {
        "init_persona_name": "Isabella Rodriguez",
        "personas": json.dumps(personas_dict, cls=DateTimeEncoder),
        "curr_tile": init_persona.scratch.curr_tile,
        "curr_time": init_persona.scratch.curr_time,
        "debug": True
    }

    print(get_move(task_params))

    

