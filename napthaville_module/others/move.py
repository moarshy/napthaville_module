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
from napthaville.persona.cognitive_modules.perceive import perceive
from napthaville.persona.cognitive_modules.retrieve import retrieve
from napthaville.persona.cognitive_modules.reflect import reflect
from napthaville.persona.cognitive_modules.execute import execute
from napthaville.persona.cognitive_modules.plan import plan as cognitive_plan
from napthaville.utils import dict_to_scratch, DateTimeEncoder
from napthaville_module.utils import (
    MAZE_FOLDER,
    ALL_PERSONAS,
    _check_persona,
    retrieve_maze_json_from_ipfs,
    upload_maze_json_to_ipfs
)


logger = logging.getLogger(__name__)


def prepare_maze(persona, maze):
    p_x, p_y = persona.scratch.curr_tile
    maze.tiles[p_y][p_x]['events'].add(persona.scratch.get_curr_event_and_desc())
    return maze

def get_move(task_params: Dict[str, Any]) -> str:
    try:
        sims_folder = task_params['sims_folder']
        curr_tile = task_params['curr_tile']
        curr_time = datetime.strptime(task_params['curr_time'], "%B %d, %Y, %H:%M:%S")
        
        init_persona_name = task_params['init_persona_name']
        if not _check_persona(init_persona_name):
            return json.dumps({"error": f"Persona {init_persona_name} not found. Please choose from {ALL_PERSONAS}"})
        
        persona_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}"
        init_persona = Persona(init_persona_name, persona_folder)

        _personas = json.loads(task_params['personas'])
        personas = {name: dict_to_scratch(persona_dict) for name, persona_dict in _personas.items()}

        # Retrieve maze_json from IPFS
        maze_ipfs_hash = task_params['maze_ipfs_hash']
        maze_json = retrieve_maze_json_from_ipfs(maze_ipfs_hash)
        maze = Maze.from_json(maze_json, MAZE_FOLDER)

        init_persona.scratch.curr_tile = curr_tile

        maze = prepare_maze(init_persona, maze)

        new_day = (not init_persona.scratch.curr_time or 
                   init_persona.scratch.curr_time.date() != curr_time.date())

        init_persona.scratch.curr_time = curr_time

        perceived = perceive(persona=init_persona, maze=maze)
        retrieved = retrieve(persona=init_persona, perceived=perceived)
        plan = cognitive_plan(persona=init_persona, maze=maze, personas=personas,
                              new_day=new_day, retrieved=retrieved)
        reflect(init_persona)

        # Save memories
        init_persona.a_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/associative_memory")
        init_persona.scratch.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/scratch.json")
        init_persona.s_mem.save(f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}/{init_persona_name}/bootstrap_memory/spatial_memory.json")

        persona_names_curr_tile = {name: persona['curr_tile'] for name, persona in personas.items()}
        execute_response = execute(persona=init_persona, maze=maze,
                                   persona_names_curr_tile=persona_names_curr_tile, plan=plan)

        # Upload updated maze back to IPFS
        updated_maze_json = maze.to_json()
        new_maze_ipfs_hash = upload_maze_json_to_ipfs(updated_maze_json)

        to_return = {
            "execute_response": execute_response,
            "chat": init_persona.scratch.chat,
            "maze_ipfs_hash": new_maze_ipfs_hash
        }

        return json.dumps(to_return, cls=DateTimeEncoder)

    except Exception as e:
        logger.error(f"Error in get_move: {str(e)}")
        return json.dumps({"error": str(e)})