import json
import logging
from napthaville_module.schemas import InputSchema
from napthaville.persona.persona import Persona
from napthaville.persona.cognitive_modules.retrieve import new_retrieve
from napthaville.persona.cognitive_modules.converse import (
    generate_summarize_agent_relationship,
    generate_one_utterance
)
from napthaville.maze import Maze

def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

logger = get_logger()


ALL_PERSONAS = [
    "Isabella Rodriguez",
    "Maria Lopez",
    "Klaus Mueller"
]


def _check_persona(persona_name: str):
    if persona_name not in ALL_PERSONAS:
        return False
    return True


def get_personal_info(task_params: dict):
    persona_name = task_params["persona_name"]
    persona_folder = task_params['persona_folder']

    exists = _check_persona(persona_name)

    if not exists:
        res = {
            "error": f"Persona {persona_name} not found. Please choose from {ALL_PERSONAS}"
        }
    
    else:
        personals_folder = f"{persona_folder}/{persona_name}"
        persona = Persona(persona_name, personals_folder)
        name = persona.scratch.name
        act_description = persona.scratch.act_description
        res =  {
            "name": name,
            "act_description": act_description
        }
    return json.dumps(res)


def get_utterence(task_params: dict):
    # check if init persona exists
    exists = _check_persona(task_params['init_persona_name'])

    if not exists:
        res = {
            "error": f"Persona {task_params['init_persona_name']} not found. Please choose from {ALL_PERSONAS}"
        } 
        return json.dumps(res)

    persona_folder = f"{task_params['init_persona_folder']}/{task_params['init_persona_name']}"
    init_persona = Persona(task_params["init_persona_name"], persona_folder)
    target_persona_name = task_params["target_persona_name"]
    target_persona_description = task_params["target_persona_description"]
    curr_chat = json.loads(task_params["curr_chat"])
    maze_folder = task_params["maze_folder"]
    maze = Maze('maze', maze_folder)

    focal_points = [f"{target_persona_name}"]
    retrieved = new_retrieve(init_persona, focal_points, 50)
    relationship = generate_summarize_agent_relationship(
        init_persona,
        target_persona_name,
        retrieved
    )
    last_chat = ""
    for i in curr_chat[-4:]:
        last_chat += ": ".join(i) + "\n"
    
    if last_chat:
        focal_points = [
            f"{relationship}",
            f"{target_persona_name} is {target_persona_description}",
            last_chat,
        ]
    else:
        focal_points = [
            f"{relationship}",
            f"{target_persona_name} is {target_persona_description}",
        ]
    retrieved = new_retrieve(init_persona, focal_points, 15)
    utt, end = generate_one_utterance(
        maze=maze,
        init_persona=init_persona,
        target_persona_name=target_persona_name,
        target_persona_description=target_persona_description,
        retrieved=retrieved,
        curr_chat=curr_chat
    )

    curr_chat += [[init_persona.scratch.name, utt]]

    res = {
        "utterance": utt,
        "end": end,
        "curr_chat": curr_chat
    }

    return json.dumps(res)


def run(inputs: InputSchema, worker_nodes = None, orchestrator_node = None, flow_run = None, cfg: dict = None):
    logger.info(f"Running task {inputs.task} with params {inputs.task_params}")

    task = inputs.task
    task_params = inputs.task_params

    if task == "get_personal_info":
        return get_personal_info(task_params)
    
    elif task == "get_utterence":
        return get_utterence(task_params)
    
    else:
        res = {
            "error": f"Task {task} not found. Please choose from {ALL_PERSONAS}"
        }
        return json.dumps(res)


if __name__ == "__main__":

    # Test get_personal_info
    inputs = {
        "task": "get_personal_info",
        "task_params": {
            "persona_name": "Isabella Rodriguez",
            "persona_folder": "/Users/arshath/play/playground/gen_agents/storage_and_statics/storage/July1_the_ville_isabella_maria_klaus-step-3-1/personas"
        }
    }

    inputs = InputSchema(**inputs)

    res = run(inputs)
    print(res)
    print(type(res))

    # Test get_utterence
    inputs = {
        "task": "get_utterence",
        "task_params": {
            "init_persona_name": "Isabella Rodriguez",
            "init_persona_folder": "/Users/arshath/play/playground/gen_agents/storage_and_statics/storage/July1_the_ville_isabella_maria_klaus-step-3-1/personas",
            "target_persona_name": "Maria Lopez",
            "target_persona_description": "sleeping",
            "curr_chat": "[]",
            "maze_folder": "/Users/arshath/play/playground/gen_agents/storage_and_statics/the_ville/matrix"
        }
    }

    inputs = InputSchema(**inputs)
    res = run(inputs)
    print(res)
    print(type(res))
    res = json.loads(res)
    print(type(res))
    print(res['curr_chat'])
    print(type(res['curr_chat']))


    inputs = {
        "task": "get_utterence",
        "task_params": {
            "init_persona_name": "Maria Lopez",
            "init_persona_folder": "/Users/arshath/play/playground/gen_agents/storage_and_statics/storage/July1_the_ville_isabella_maria_klaus-step-3-1/personas",
            "target_persona_name": "Isabella Rodriguez",
            "target_persona_description": "sleeping",
            "curr_chat": json.dumps(res['curr_chat']),
            "maze_folder": "/Users/arshath/play/playground/gen_agents/storage_and_statics/the_ville/matrix"
        }
    }
    inputs = InputSchema(**inputs)
    res = run(inputs)
    print(res)