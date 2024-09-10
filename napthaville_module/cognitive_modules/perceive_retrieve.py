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
    retrieve_maze_json_from_ipfs,
    setup_logging,
)


setup_logging()
logger = logging.getLogger(__name__)


def get_perceived_retrieved(task_params: dict):
    # sims_folder, curr_tile, curr_time, init_persona_name, maze_ipfs_hash
    sims_folder = task_params["sims_folder"]
    curr_tile = task_params["curr_tile"]
    curr_time = datetime.strptime(task_params["curr_time"], "%B %d, %Y, %H:%M:%S")
    init_persona_name = task_params["init_persona_name"]
    persona_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}"
    init_persona = Persona(init_persona_name, persona_folder)

    # Retrieve maze_json from IPFS
    maze_ipfs_hash = task_params["maze_ipfs_hash"]
    maze_json = retrieve_maze_json_from_ipfs(maze_ipfs_hash)
    maze = Maze.from_json(maze_json, MAZE_FOLDER)

    init_persona.scratch.curr_tile = curr_tile

    logger.info(f"curr time {init_persona.scratch.curr_time}")

    new_day = False
    if not init_persona.scratch.curr_time:
        new_day = "First day"
    elif init_persona.scratch.curr_time.strftime("%A %B %d") != curr_time.strftime(
        "%A %B %d"
    ):
        new_day = "New day"

    logger.info(f"new day {new_day}")

    init_persona.scratch.curr_time = curr_time

    perceived = perceive(persona=init_persona, maze=maze)
    logger.info(f"Perceived data for {init_persona_name}: {perceived}")
    retrieved = retrieve(persona=init_persona, perceived=perceived)

    init_persona.scratch.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/scratch.json"
    )
    init_persona.s_mem.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/spatial_memory.json"
    )
    init_persona.a_mem.save(
        f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/bootstrap_memory/associative_memory"
    )

    return json.dumps(
        {
            "retrieved": retrieved,
            "new_day": new_day,
            "curr_time": curr_time.strftime("%B %d, %Y, %H:%M:%S"),
        }
    )
