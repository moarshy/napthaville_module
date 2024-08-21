import json
import os
import logging
from datetime import datetime
from napthaville.persona.cognitive_modules.perceive import perceive
from napthaville.persona.cognitive_modules.retrieve import retrieve
from napthaville.maze import Maze
from napthaville.persona.persona import Persona
from napthaville_module.utils import (
    MAZE_FOLDER,
    ALL_PERSONAS,
    _check_persona,
    retrieve_maze_json_from_ipfs
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_perceived_retrieved(task_params: dict):
    # sims_folder, curr_tile, curr_time, init_persona_name, maze_ipfs_hash
    sims_folder = task_params['sims_folder']
    curr_tile = task_params['curr_tile']
    curr_time = datetime.strptime(task_params['curr_time'], "%B %d, %Y, %H:%M:%S")
    
    init_persona_name = task_params['init_persona_name']
    if not _check_persona(init_persona_name):
        return json.dumps({"error": f"Persona {init_persona_name} not found. Please choose from {ALL_PERSONAS}"})
    
    persona_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}"
    init_persona = Persona(init_persona_name, persona_folder)

    # Retrieve maze_json from IPFS
    maze_ipfs_hash = task_params['maze_ipfs_hash']
    maze_json = retrieve_maze_json_from_ipfs(maze_ipfs_hash)
    maze = Maze.from_json(maze_json, MAZE_FOLDER)

    init_persona.scratch.curr_tile = curr_tile

    new_day = (not init_persona.scratch.curr_time or 
                init_persona.scratch.curr_time.date() != curr_time.date())

    init_persona.scratch.curr_time = curr_time

    perceived = perceive(persona=init_persona, maze=maze)
    logger.info(f"Perceived data for {init_persona_name}: {perceived}")
    retrieved = retrieve(persona=init_persona, perceived=perceived)

    init_persona.scratch.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/scratch.json")
    init_persona.s_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/spatial_memory.json")
    init_persona.a_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/associative_memory")

    return json.dumps({
        "retrieved": retrieved,
        'new_day': new_day,
        'curr_time': curr_time.strftime("%B %d, %Y, %H:%M:%S")
    })
