import json
import uuid
import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from napthaville.maze import Maze
from napthaville.persona.persona import Persona
from napthaville_module.utils import (
    PERSONAS_FOLDER,
    MAZE_FOLDER,
    retrieve_maze_json_from_ipfs,
    upload_maze_json_to_ipfs
)


logger = logging.getLogger(__name__)

def fork_persona(task_params):
    if not PERSONAS_FOLDER or not MAZE_FOLDER:
        raise ValueError("PERSONAS_FOLDER and MAZE_FOLDER must be set in environment variables when not in debug mode")

    # Create a new persona folder
    base_persona_folder = Path(PERSONAS_FOLDER) / task_params['persona_name']

    # New sims folder
    new_sims_folder = Path(os.getenv('BASE_OUTPUT_DIR')) / str(uuid.uuid4())
    
    # New fork folder
    new_persona_folder = new_sims_folder / task_params['persona_name']

    # Create the new_sims_folder
    new_sims_folder.mkdir(parents=True, exist_ok=True)

    # Copy the base persona folder to the new persona folder
    shutil.copytree(base_persona_folder, new_persona_folder)

    # Retrieve maze_json from IPFS
    maze_ipfs_hash = task_params['maze_ipfs_hash']
    maze_json = retrieve_maze_json_from_ipfs(maze_ipfs_hash)

    curr_tile = task_params['curr_tile']
    maze = Maze.from_json(maze_json, MAZE_FOLDER)
    persona = Persona(task_params['persona_name'], new_persona_folder)
    maze.tiles[curr_tile[1]][curr_tile[0]]['events'].add(persona.scratch.get_curr_event_and_desc())

    # Upload updated maze back to IPFS
    updated_maze_json = maze.to_json()
    new_maze_ipfs_hash = upload_maze_json_to_ipfs(updated_maze_json)

    to_return = {
        "maze_ipfs_hash": new_maze_ipfs_hash,
        "sims_folder": new_sims_folder.name
    }

    return json.dumps(to_return)