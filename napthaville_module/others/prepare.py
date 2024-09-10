import json
import os
import yaml
import uuid
import shutil
import logging
from pathlib import Path
from datetime import datetime
from napthaville.maze import Maze
from napthaville.persona.persona import Persona
from napthaville.persona.cognitive_modules.converse import load_history_via_whisper
from napthaville_module.utils import (
    PERSONAS_FOLDER,
    MAZE_FOLDER,
    retrieve_maze_json_from_ipfs,
    upload_maze_json_to_ipfs,
    get_folder_from_ipfs,
    setup_logging,
)


setup_logging()
logger = logging.getLogger(__name__)


def prepare_persona(task_params: dict):
    logger.info(f"Preparing persona: {task_params}")
    persona_name = task_params.get("persona_name")
    persona_ipfs_hash = task_params.get("persona_ipfs_hash")
    curr_time = task_params.get("curr_time")
    curr_tile = task_params.get("curr_tile")
    maze_ipfs_hash = task_params.get("maze_ipfs_hash")

    if isinstance(curr_time, str):
        curr_time = datetime.strptime(curr_time, "%B %d, %Y, %H:%M:%S")

    # 1. get folder from IPFS
    base_folder = Path(os.getenv("BASE_OUTPUT_DIR"))
    folder_id = str(uuid.uuid4())
    new_persona_folder = f"{base_folder}/{folder_id}"
    get_folder_from_ipfs(persona_ipfs_hash, new_persona_folder)
    new_persona_folder = f"{new_persona_folder}/{persona_ipfs_hash}"
    print(f"new_persona_folder: {new_persona_folder}")

    # 2. load in persona
    persona = Persona(persona_name, new_persona_folder)

    # 3. load whisper
    with open(f"{new_persona_folder}/persona.yaml", "r") as f:
        persona_yaml = yaml.safe_load(f)
    whisper = persona_yaml.get("whisper", None)
    print(f"whisper: {whisper}")
    load_history_via_whisper(persona, whisper, curr_time)

    # 4. Retrieve maze_json from IPFS
    maze_ipfs_hash = task_params["maze_ipfs_hash"]
    maze_json = retrieve_maze_json_from_ipfs(maze_ipfs_hash)
    curr_tile = task_params["curr_tile"]
    maze = Maze.from_json(maze_json, MAZE_FOLDER)
    maze.tiles[curr_tile[1]][curr_tile[0]]["events"].add(
        persona.scratch.get_curr_event_and_desc()
    )

    # Upload updated maze back to IPFS
    updated_maze_json = maze.to_json()
    new_maze_ipfs_hash = upload_maze_json_to_ipfs(updated_maze_json)

    # 4. save persona
    persona.a_mem.save(f"{new_persona_folder}/bootstrap_memory/associative_memory")
    persona.scratch.save(f"{new_persona_folder}/bootstrap_memory/scratch.json")
    persona.s_mem.save(f"{new_persona_folder}/bootstrap_memory/spatial_memory.json")

    # 5. return persona folder and maze
    to_return = {
        "maze_ipfs_hash": new_maze_ipfs_hash,
        "sims_folder": f"{folder_id}/{persona_ipfs_hash}",
    }

    return json.dumps(to_return)


def fork_persona(task_params):
    if not PERSONAS_FOLDER or not MAZE_FOLDER:
        raise ValueError(
            "PERSONAS_FOLDER and MAZE_FOLDER must be set in environment variables when not in debug mode"
        )

    # Create a new persona folder
    base_persona_folder = Path(PERSONAS_FOLDER) / task_params["persona_name"]

    # New sims folder
    new_sims_folder = Path(os.getenv("BASE_OUTPUT_DIR")) / str(uuid.uuid4())

    # New fork folder
    new_persona_folder = new_sims_folder / task_params["persona_name"]

    # Create the new_sims_folder
    new_sims_folder.mkdir(parents=True, exist_ok=True)

    # Copy the base persona folder to the new persona folder
    shutil.copytree(base_persona_folder, new_persona_folder)

    # Retrieve maze_json from IPFS
    maze_ipfs_hash = task_params["maze_ipfs_hash"]
    logger.info(f"maze_ipfs_hash: {maze_ipfs_hash}")
    maze_json = retrieve_maze_json_from_ipfs(maze_ipfs_hash)

    curr_tile = task_params["curr_tile"]
    maze = Maze.from_json(maze_json, MAZE_FOLDER)
    persona = Persona(task_params["persona_name"], new_persona_folder)
    maze.tiles[curr_tile[1]][curr_tile[0]]["events"].add(
        persona.scratch.get_curr_event_and_desc()
    )

    # Upload updated maze back to IPFS
    updated_maze_json = maze.to_json()
    new_maze_ipfs_hash = upload_maze_json_to_ipfs(updated_maze_json)

    to_return = {
        "maze_ipfs_hash": new_maze_ipfs_hash,
        "sims_folder": new_sims_folder.name,
    }

    return json.dumps(to_return)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    os.environ["BASE_OUTPUT_DIR"] = "/Users/arshath/play/napthaville_module"
    os.environ["IPFS_GATEWAY_URL"] = "/dns/provider.akash.pro/tcp/31832/http"
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

    maze = Maze(
        "test", "/Users/arshath/play/playground/customizeable_personas/the_ville/matrix"
    )
    maze_json = maze.to_json()
    maze_ipfs_hash = upload_maze_json_to_ipfs(maze_json)
    logger.info(f"maze_ipfs_hash: {maze_ipfs_hash}")

    personas = {
        "Mark Schmidt": "QmXJBcUiMAg7CfNSaYyNH8Ap1hh15chVwPepGbiRckkSxe",
        "Mo Arshy": "QmXMTvYR8P9zNXtujWvcsggix3HGQxaM8KV2QKE3vD2nm2",
        "Richard Blythman": "QmeMDy7GhjVqQwKhUxcjPEqca8tZ5sfFQKBE473otakLgj",
    }

    curr_time = datetime.now().strftime("%B %d, %Y, %H:%M:%S")
    curr_tile = (0, 0)

    for persona_name, persona_ipfs_hash in personas.items():
        task_params = {
            "persona_name": persona_name,
            "persona_ipfs_hash": persona_ipfs_hash,
            "curr_time": curr_time,
            "curr_tile": curr_tile,
            "maze_ipfs_hash": maze_ipfs_hash,
        }
        print(prepare_persona(task_params))

# running "python -m dotenv run python napthaville_module/others/prepare.py"
