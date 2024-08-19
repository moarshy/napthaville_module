import json
import os
from napthaville.persona.persona import Persona
from napthaville.persona.cognitive_modules.reflect import reflect
from napthaville.persona.cognitive_modules.execute import execute
from napthaville_module.utils import (
    retrieve_maze_json_from_ipfs,
    save_maze_json_to_ipfs
)
from napthaville.maze import Maze


def get_reflect_execute(task_params: dict):
    sims_folder = task_params["sims_folder"]
    init_persona_name = task_params["init_persona_name"]
    personas_curr_tiles = task_params["personas_curr_tiles"]
    plan = task_params["plan"]
    personals_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}"
    persona = Persona(init_persona_name, personals_folder)

    maze_ipfs_hash = task_params["maze_ipfs_hash"]
    maze_json = retrieve_maze_json_from_ipfs(maze_ipfs_hash)
    maze = Maze.from_json(maze_json)

    persona = reflect(persona)

    execution = execute(
        persona=persona,
        maze=maze,
        persona_names_curr_tile=personas_curr_tiles,
        plan=plan
    )

    # Save the persona's memory to the file system.
    persona.scratch.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/scratch.json")
    persona.s_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/spatial_memory.json")
    persona.a_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/associative_memory")

    maze_json = maze.to_json()
    maze_ipfs_hash = save_maze_json_to_ipfs(maze_json)
    

    return json.dumps({
        "execution": execution,
        "maze_ipfs_hash": maze_ipfs_hash
    })