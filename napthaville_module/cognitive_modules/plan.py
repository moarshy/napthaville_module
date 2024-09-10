import os
import json
import logging
from datetime import datetime
from napthaville.persona.cognitive_modules.plan import plan as plan_function
from napthaville.persona.cognitive_modules.plan import _wait_react, _chat_react
from napthaville.maze import Maze
from napthaville.persona.persona import Persona
from napthaville.persona.memory_structures.associative_memory import ConceptNode
from napthaville.utils import dict_to_scratch
from napthaville_module.utils import (
    MAZE_FOLDER,
    retrieve_maze_json_from_ipfs,
    setup_logging,
)
from napthaville.persona.cognitive_modules.plan import (
    _long_term_planning,
    _determine_action,
    _choose_retrieved,
    _should_react,
)


setup_logging()
logger = logging.getLogger(__name__)


def get_reaction_mode(task_params: dict):
    retrieved_json = json.loads(task_params["retrieved"])
    retrieved = json_to_conceptnodes(retrieved_json)
    new_day = task_params["new_day"]
    maze_ipfs_hash = task_params["maze_ipfs_hash"]
    sims_folder = task_params["sims_folder"]
    init_persona_name = task_params["init_persona_name"]
    personas = json.loads(task_params["personas"])
    maze_json = retrieve_maze_json_from_ipfs(maze_ipfs_hash)
    maze = Maze.from_json(maze_json, MAZE_FOLDER)
    persona_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}"
    persona = Persona(init_persona_name, persona_folder)

    # add curr_time to persona scratch
    curr_time = datetime.strptime(task_params["curr_time"], "%B %d, %Y, %H:%M:%S")
    persona.scratch.curr_time = curr_time

    if new_day:
        _long_term_planning(persona, new_day, f"{persona_folder}/bootstrap_memory")
    if persona.scratch.act_check_finished:
        _determine_action(persona, maze, f"{persona_folder}/bootstrap_memory")

    focused_event = False
    if retrieved.keys():
        logger.info("_choose_retrieved")
        focused_event = _choose_retrieved(persona, retrieved)

    if focused_event:
        logger.info("_should_react")
        reaction_mode = _should_react(persona, focused_event, personas)
    else:
        reaction_mode = False

    logger.info(f"Focused event: {focused_event}")
    logger.info(f"Reaction mode: {reaction_mode}")

    if isinstance(focused_event, dict):
        for k, v in focused_event.items():
            if isinstance(v, ConceptNode):
                focused_event[k] = v.to_dict()
            if isinstance(v, list):
                focused_event[k] = [e.to_dict() for e in v]

    persona.scratch.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/scratch.json"
    )
    persona.s_mem.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/spatial_memory.json"
    )
    persona.a_mem.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/associative_memory"
    )

    # return {
    #     "reaction_mode": reaction_mode,
    #     "focused_event": focused_event.to_dict() if focused_event else False
    # }
    return json.dumps(
        {
            "reaction_mode": reaction_mode,
            "focused_event": focused_event,
        }
    )


def json_to_conceptnodes(retrieved_json):
    """Convert the JSON representation back to a dictionary with ConceptNode objects."""
    retrieved = {}
    for event_desc, event_data in retrieved_json.items():
        retrieved[event_desc] = {
            "curr_event": ConceptNode.from_dict(event_data["curr_event"]),
            "events": [ConceptNode.from_dict(e) for e in event_data["events"]],
            "thoughts": [ConceptNode.from_dict(t) for t in event_data["thoughts"]],
        }
    return retrieved


def get_plan(task_params: dict):
    init_persona_name = task_params["init_persona_name"]
    sims_folder = task_params["sims_folder"]
    persona_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}"
    init_persona = Persona(init_persona_name, persona_folder)

    # JSON String to dict
    # key is the persona name, value is the persona scratch memory dict
    _personas = json.loads(task_params["personas"])
    personas = {}
    for persona_name, persona_dict in _personas.items():
        personas[persona_name] = dict_to_scratch(persona_dict)

    maze = Maze("maze", MAZE_FOLDER)

    curr_tile = task_params["curr_tile"]
    curr_time = task_params["curr_time"]
    retrieved = json.loads(task_params["retrieved"])
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
        retrieved=retrieved,
    )

    print(plan_result)

    return json.dumps(plan_result)


def get_complete_plan_chat(task_params: dict):
    logger.info("get_complete_plan_chat")
    persona_name = task_params["init_persona_name"]
    sims_folder = task_params["sims_folder"]
    all_utt = task_params["all_utt"]
    convo_length = task_params["convo_length"]
    target_persona_scratch = task_params["target_persona_scratch"]
    personals_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}"
    persona = Persona(persona_name, personals_folder)

    logger.info(f"all_utt: {all_utt}")
    logger.info(f"convo_length: {convo_length}")
    logger.info(f"all utt type: {type(all_utt)}")

    to_return = _chat_react(
        persona=persona,
        target_persona_scratch=target_persona_scratch,
        all_utt=all_utt,
        convo_length=convo_length,
        sims_folder=sims_folder,
        init_persona_name=persona_name,
    )

    if persona.scratch.act_event[1] != "chat with":
        persona.scratch.chatting_with = None
        persona.scratch.chat = None
        persona.scratch.chatting_end_time = None

    curr_persona_chat_buffer = persona.scratch.chatting_with_buffer
    for persona_name, buffer_count in curr_persona_chat_buffer.items():
        if persona_name != persona.scratch.chatting_with:
            persona.scratch.chatting_with_buffer[persona_name] -= 1

    persona.scratch.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/scratch.json"
    )
    persona.s_mem.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/spatial_memory.json"
    )
    persona.a_mem.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/associative_memory"
    )

    # return json.dumps(persona.scratch.act_address)
    return json.dumps(
        {
            "init_persona_act_address": persona.scratch.act_address,
            "target_persona_return": to_return,
        }
    )


def get_complete_plan_wait(task_params: dict):
    sims_folder = task_params["sims_folder"]
    init_persona_name = task_params["init_persona_name"]
    personals_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}"
    persona = Persona(init_persona_name, personals_folder)
    reaction_mode = task_params["reaction_mode"]
    _wait_react(persona, reaction_mode)

    if persona.scratch.act_event[1] != "chat with":
        persona.scratch.chatting_with = None
        persona.scratch.chat = None
        persona.scratch.chatting_end_time = None

    curr_persona_chat_buffer = persona.scratch.chatting_with_buffer
    for persona_name, buffer_count in curr_persona_chat_buffer.items():
        if persona_name != persona.scratch.chatting_with:
            persona.scratch.chatting_with_buffer[persona_name] -= 1

    persona.scratch.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/scratch.json"
    )
    persona.s_mem.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/spatial_memory.json"
    )
    persona.a_mem.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/associative_memory"
    )

    return json.dumps(persona.scratch.act_address)


def get_complete_plan_no_reaction(task_params: dict):
    sims_folder = task_params["sims_folder"]
    init_persona_name = task_params["init_persona_name"]
    personals_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}"
    persona = Persona(init_persona_name, personals_folder)

    if persona.scratch.act_event[1] != "chat with":
        persona.scratch.chatting_with = None
        persona.scratch.chat = None
        persona.scratch.chatting_end_time = None

    curr_persona_chat_buffer = persona.scratch.chatting_with_buffer
    for persona_name, buffer_count in curr_persona_chat_buffer.items():
        if persona_name != persona.scratch.chatting_with:
            persona.scratch.chatting_with_buffer[persona_name] -= 1

    persona.scratch.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/scratch.json"
    )
    persona.s_mem.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/spatial_memory.json"
    )
    persona.a_mem.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/associative_memory"
    )

    return json.dumps(persona.scratch.act_address)


def finalise_target_persona_chat(task_params: dict):
    target_persona_return = task_params["target_persona_return"]
    target_persona_name = task_params["target_persona_name"]
    sims_folder = task_params["sims_folder"]
    personals_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}"
    persona = Persona(target_persona_name, personals_folder)

    persona.scratch.f_daily_schedule[
        target_persona_return["start_index"] : target_persona_return["end_index"]
    ] = target_persona_return["ret"]

    # convert chatting end time to datetime
    target_persona_return["chatting_end_time"] = datetime.strptime(
        target_persona_return["chatting_end_time"], "%Y-%m-%dT%H:%M:%S"
    )
    target_persona_return["act_start_time"] = datetime.strptime(
        target_persona_return["act_start_time"], "%Y-%m-%dT%H:%M:%S"
    )

    persona.scratch.add_new_action(
        target_persona_return["act_address"],
        target_persona_return["inserted_act_dur"],
        target_persona_return["inserted_act"],
        target_persona_return["act_pronunciatio"],
        target_persona_return["act_event"],
        target_persona_return["chatting_with"],
        target_persona_return["chat"],
        target_persona_return["chatting_with_buffer"],
        target_persona_return["chatting_end_time"],
        target_persona_return["act_obj_description"],
        target_persona_return["act_obj_pronunciatio"],
        target_persona_return["act_obj_event"],
        target_persona_return["act_start_time"],
    )

    persona.scratch.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/scratch.json"
    )
    persona.s_mem.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/spatial_memory.json"
    )
    persona.a_mem.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/associative_memory"
    )

    persona_scratch = persona.scratch.to_dict()
    logger.info(f"persona_scratch: {persona_scratch}")

    return json.dumps(persona.scratch.act_address)
