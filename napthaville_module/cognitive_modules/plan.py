import json
from datetime import datetime
from napthaville.persona.cognitive_modules.plan import plan as plan_function
from napthaville.maze import Maze
from napthaville.persona.persona import Persona
from napthaville.utils import dict_to_scratch, DateTimeEncoder
from napthaville_module.utils import (
    PERSONAS_FOLDER,
    MAZE_FOLDER,
    ALL_PERSONAS,
    _check_persona,
)

def get_plan(task_params: dict):
    debug = task_params.get('debug', False)
    if debug:
        print("Debug mode enabled")
        PERSONAS_FOLDER = '/Users/arshath/play/playground/gen_agents/storage_and_statics/storage/July1_the_ville_isabella_maria_klaus-step-3-1/personas'
        MAZE_FOLDER = '/Users/arshath/play/playground/gen_agents/storage_and_statics/the_ville/matrix'

    init_persona_name = task_params['init_persona_name']
    exists = _check_persona(init_persona_name)
    if not exists:
        res = {
            "error": f"Persona {init_persona_name} not found. Please choose from {ALL_PERSONAS}"
        } 
        return json.dumps(res)

    persona_folder = f"{PERSONAS_FOLDER}/{init_persona_name}"
    init_persona = Persona(init_persona_name, persona_folder)

    # JSON String to dict
    # key is the persona name, value is the persona scratch memory dict
    _personas = json.loads(task_params['personas'])
    personas = {}
    for persona_name, persona_dict in _personas.items():
        personas[persona_name] = dict_to_scratch(persona_dict)

    maze = Maze('maze', MAZE_FOLDER)

    curr_tile = task_params['curr_tile']
    curr_time = task_params['curr_time']
    retrieved = json.loads(task_params['retrieved'])
    init_persona.scratch.curr_tile = curr_tile

    new_day = False
    if not init_persona.scratch.curr_time:
        new_day = "First day"
    elif init_persona.scratch.curr_time.strftime("%A %B %d") != curr_time.strftime(
        "%A %B %d"
    ):
        new_day = "New day"

    init_persona.scratch.curr_time = curr_time

    plan_result = plan_function(
        persona=init_persona,
        maze=maze,
        personas=personas,
        new_day=new_day,
        retrieved=retrieved
    )

    print(plan_result)

    return json.dumps(plan_result)

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

    task_params = {
        "init_persona_name": "Isabella Rodriguez",
        "personas": json.dumps(personas_dict, cls=DateTimeEncoder),
        "curr_tile": "1,1",
        "curr_time": datetime.now(),
        "retrieved": json.dumps({}),
        "debug": True
    }
    print(get_plan(task_params))