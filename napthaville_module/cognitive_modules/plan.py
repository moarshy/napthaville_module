import os
import json
import logging
from napthaville.persona.cognitive_modules.plan import plan as plan_function
from napthaville.persona.cognitive_modules.plan import _wait_react, _chat_react
from napthaville.maze import Maze
from napthaville.persona.persona import Persona
from napthaville.persona.memory_structures.associative_memory import ConceptNode
from napthaville.utils import dict_to_scratch
from napthaville_module.utils import (
    MAZE_FOLDER,
    ALL_PERSONAS,
    _check_persona,
    retrieve_maze_json_from_ipfs
)
from napthaville.persona.cognitive_modules.plan import _long_term_planning, _determine_action, _choose_retrieved, _should_react


logger = logging.getLogger(__name__)


def get_reaction_mode(task_params: dict):
    retrieved_json = json.loads(task_params['retrieved'])
    retrieved = json_to_conceptnodes(retrieved_json)
    new_day = task_params['new_day']
    maze_ipfs_hash = task_params['maze_ipfs_hash']
    sims_folder = task_params['sims_folder']
    init_persona_name = task_params['init_persona_name']
    personas = json.loads(task_params['personas'])
    maze_json = retrieve_maze_json_from_ipfs(maze_ipfs_hash)
    maze = Maze.from_json(maze_json, MAZE_FOLDER)
    persona_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}"
    persona = Persona(init_persona_name, persona_folder)

    if new_day:
        _long_term_planning(persona, new_day, f"{persona_folder}/bootstrap_memory")
    if persona.scratch.act_check_finished:
        _determine_action(persona, maze, f"{persona_folder}/bootstrap_memory")

    focused_event = False
    if retrieved:
        focused_event = _choose_retrieved(persona, retrieved)
    
    if focused_event:
        reaction_mode = _should_react(persona, focused_event, personas)
    else:
        reaction_mode = False

    persona.scratch.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/scratch.json")
    persona.s_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/spatial_memory.json")
    persona.a_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/associative_memory")    

    # return {
    #     "reaction_mode": reaction_mode,
    #     "focused_event": focused_event.to_dict() if focused_event else False
    # }

    logger.info(f"Focused event: {focused_event}")
    logger.info(f"Focused event type: {type(focused_event)}")

    if isinstance(focused_event, ConceptNode):
        focused_event = focused_event.to_dict()
    elif isinstance(focused_event, dict):
        for key, value in focused_event.items():
            if isinstance(value, ConceptNode):
                focused_event[key] = value.to_dict()
            elif isinstance(value, list):
                focused_event[key] = [v.to_dict() for v in value if isinstance(v, ConceptNode)]
    elif isinstance(focused_event, list):
        focused_event = [v.to_dict() for v in focused_event if isinstance(v, ConceptNode)]

    return json.dumps({
        "reaction_mode": reaction_mode,
        "focused_event": focused_event
        })

def json_to_conceptnodes(retrieved_json):
    """Convert the JSON representation back to a dictionary with ConceptNode objects."""
    retrieved = {}
    for event_desc, event_data in retrieved_json.items():
        retrieved[event_desc] = {
            "curr_event": ConceptNode.from_dict(event_data["curr_event"]),
            "events": [ConceptNode.from_dict(e) for e in event_data["events"]],
            "thoughts": [ConceptNode.from_dict(t) for t in event_data["thoughts"]]
        }
    return retrieved


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


def get_complete_plan_chat(task_params: dict):
    persona_name = task_params["init_persona_name"]
    sims_folder = task_params["sims_folder"]
    all_utt = task_params["all_utt"]
    convo_length = task_params["convo_length"]
    target_persona_scratch = task_params["target_persona_scratch"]
    exists = _check_persona(persona_name)

    if not exists:
        res = {
            "error": f"Persona {persona_name} not found. Please choose from {ALL_PERSONAS}"
        }
        return json.dumps(res)
    
    personals_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{persona_name}"
    persona = Persona(persona_name, personals_folder)

    persona = _chat_react(
        persona=persona,
        target_persona_scratch=target_persona_scratch,
        all_utt=all_utt,
        convo_length=convo_length,
        sims_folder=sims_folder,
        init_persona_name=persona_name
    )

    if persona.scratch.act_event[1] != "chat with":
        persona.scratch.chatting_with = None
        persona.scratch.chat = None
        persona.scratch.chatting_end_time = None

    curr_persona_chat_buffer = persona.scratch.chatting_with_buffer
    for persona_name, buffer_count in curr_persona_chat_buffer.items():
        if persona_name != persona.scratch.chatting_with:
            persona.scratch.chatting_with_buffer[persona_name] -= 1

    persona.scratch.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{persona_name}/bootstrap_memory/scratch.json")
    persona.s_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{persona_name}/bootstrap_memory/spatial_memory.json")
    persona.a_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{persona_name}/bootstrap_memory/associative_memory")

    return json.dumps(persona.scratch.act_address)


def get_complete_plan_wait(task_params: dict):
    sims_folder = task_params["sims_folder"]
    init_persona_name = task_params["init_persona_name"]
    personals_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}"
    persona = Persona(init_persona_name, personals_folder)
    reaction_mode = task_params["reaction_mode"]
    persona = _wait_react(persona, reaction_mode)
    
    if persona.scratch.act_event[1] != "chat with":
        persona.scratch.chatting_with = None
        persona.scratch.chat = None
        persona.scratch.chatting_end_time = None

    curr_persona_chat_buffer = persona.scratch.chatting_with_buffer
    for persona_name, buffer_count in curr_persona_chat_buffer.items():
        if persona_name != persona.scratch.chatting_with:
            persona.scratch.chatting_with_buffer[persona_name] -= 1

    persona.scratch.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/scratch.json")
    persona.s_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/spatial_memory.json")
    persona.a_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/associative_memory")

    return json.dumps(persona.scratch.act_address)


def get_complete_plan_no_reaction(task_params: dict):
    sims_folder = task_params["sims_folder"]
    init_persona_name = task_params["init_persona_name"]
    personals_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}"
    persona = Persona(init_persona_name, personals_folder)

    if persona.scratch.act_event[1] != "chat with":
        persona.scratch.chatting_with = None
        persona.scratch.chat = None
        persona.scratch.chatting_end_time = None

    curr_persona_chat_buffer = persona.scratch.chatting_with_buffer
    for persona_name, buffer_count in curr_persona_chat_buffer.items():
        if persona_name != persona.scratch.chatting_with:
            persona.scratch.chatting_with_buffer[persona_name] -= 1

    persona.scratch.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/scratch.json")
    persona.s_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/spatial_memory.json")
    persona.a_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/associative_memory")

    return json.dumps(persona.scratch.act_address)