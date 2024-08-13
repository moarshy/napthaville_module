import json
from napthaville.maze import Maze
from napthaville.persona.persona import Persona
from napthaville.persona.cognitive_modules.retrieve import new_retrieve
from napthaville.persona.cognitive_modules.converse import (
    generate_summarize_agent_relationship,
    generate_one_utterance
)
from napthaville_module.utils import (
    PERSONAS_FOLDER,
    MAZE_FOLDER,
    ALL_PERSONAS,
    _check_persona
)


def get_personal_info(task_params: dict):
    persona_name = task_params["persona_name"]
    exists = _check_persona(persona_name)

    if not exists:
        res = {
            "error": f"Persona {persona_name} not found. Please choose from {ALL_PERSONAS}"
        }
    
    else:
        personals_folder = f"{PERSONAS_FOLDER}/{persona_name}"
        persona = Persona(persona_name, personals_folder)
        name = persona.scratch.name
        act_description = persona.scratch.act_description
        res =  {
            "name": name,
            "act_description": act_description
        }
    return json.dumps(res)


def get_utterence(task_params: dict):
    exists = _check_persona(task_params['init_persona_name'])

    if not exists:
        res = {
            "error": f"Persona {task_params['init_persona_name']} not found. Please choose from {ALL_PERSONAS}"
        } 
        return json.dumps(res)

    persona_folder = f"{PERSONAS_FOLDER}/{task_params['init_persona_name']}"
    init_persona = Persona(task_params["init_persona_name"], persona_folder)
    target_persona_name = task_params["target_persona_name"]
    target_persona_description = task_params["target_persona_description"]
    curr_chat = json.loads(task_params["curr_chat"])
    maze = Maze('maze', MAZE_FOLDER)

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