import os
import json
import math
import uuid
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from napthaville.maze import Maze
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from napthaville_module.run import run as module_run
from napthaville_module.utils import (
    upload_maze_json_to_ipfs,
    get_folder_from_ipfs,
    setup_logging,
    retrieve_json_from_ipfs,
    upload_json_file_to_ipfs,
)

# Existing logging configuration
setup_logging()
logger = logging.getLogger(__name__)

PERSONAS = {
    "Mark Schmidt": "QmXJBcUiMAg7CfNSaYyNH8Ap1hh15chVwPepGbiRckkSxe",
    "Mo Arshy": "QmXMTvYR8P9zNXtujWvcsggix3HGQxaM8KV2QKE3vD2nm2",
    "Richard Blythman": "QmeMDy7GhjVqQwKhUxcjPEqca8tZ5sfFQKBE473otakLgj",
}
BASE_MAZE_IPFS_HASH = "QmWrCkdJHVb5MfQuL1yXh6Wt2Dxp7ajJPDH7cRRdEuBvAK"
BASE_SIMS_IPFS_HASH = "QmXhXrkrGMNukzFzRJMai2nKC2X181bFvZRDw27W2NyGH7"


BASE_SIMS_FOLDER = f"{os.getenv('BASE_OUTPUT_DIR')}"


class SimulationManager:
    def __init__(self, num_steps: int, ipfs_hash: Optional[str] = None):
        logger.info(f"Initializing SimulationManager with {num_steps} steps")
        self.num_steps = num_steps
        self.game_obj_cleanup = {}

        if ipfs_hash:
            self.load_simulation_from_ipfs(ipfs_hash)
        else:
            self.maze_folder = f"{BASE_SIMS_FOLDER}/maze"
            if not os.path.exists(self.maze_folder):
                get_folder_from_ipfs(BASE_MAZE_IPFS_HASH, self.maze_folder)

            self.maze_folder = f"{self.maze_folder}/{BASE_MAZE_IPFS_HASH}/matrix"
            self.maze = Maze(maze_name="napthaville", maze_folder=self.maze_folder)
            self.sims_folders: Dict[str, str] = {}
            self.persona_tiles: Dict[str, tuple] = {}
            self.personas_to_workers: Dict[str, str] = {}
            self.start_time: datetime
            self.curr_time: datetime
            self.sec_per_step: int
            self.step: Optional[int] = None

        self.chat_personas = {}
        self.chat = False

    def load_simulation_from_ipfs(self, ipfs_hash: str):
        """Load simulation state from IPFS"""
        logger.info(f"Loading simulation state from IPFS hash: {ipfs_hash}")
        simulation_info = retrieve_json_from_ipfs(ipfs_hash)

        self.orchestrator_sims_folder = simulation_info["orchestrator_sims_folder"]
        self.all_personas = simulation_info["personas"]
        self.num_steps = simulation_info["num_steps"]
        self.start_time = datetime.strptime(
            simulation_info["start_time"], "%B %d, %Y, %H:%M:%S"
        )
        self.curr_time = datetime.strptime(
            simulation_info["end_time"], "%B %d, %Y, %H:%M:%S"
        )
        self.sec_per_step = simulation_info["sec_per_step"]
        self.sims_folders = simulation_info["sims_folders"]
        self.maze_ipfs_hash = simulation_info["maze_ipfs_hash"]
        self.step = simulation_info["current_step"]

        # Load the last environment state
        last_env_file = f"{self.orchestrator_sims_folder}/environment/{self.step}.json"
        with open(last_env_file, "r") as f:
            last_env = json.load(f)

        # Set persona tiles based on the last environment state
        self.persona_tiles = {
            persona: (data["x"], data["y"]) for persona, data in last_env.items()
        }

        # Load the maze state using the IPFS hash
        maze_json = retrieve_json_from_ipfs(self.maze_ipfs_hash)
        self.maze = Maze.from_json(maze_json)

        logger.info("Simulation state loaded successfully from IPFS")

    def init_simulation(self):
        """Initialize the simulation environment."""
        logger.info("Initializing simulation environment")
        self.orchestrator_sims_folder = self.fork_sims_folder()
        env = self.load_initial_state()
        self.init_personas(env)
        logger.info("Simulation initialization completed")

    def fork_sims_folder(self) -> str:
        """Create a new simulation folder."""
        logger.info("Creating new simulation folder")
        folder_id = str(uuid.uuid4())
        new_sims_folder = f"{BASE_SIMS_FOLDER}/{folder_id}"
        get_folder_from_ipfs(BASE_SIMS_IPFS_HASH, new_sims_folder)
        new_sims_folder = f"{new_sims_folder}/{BASE_SIMS_IPFS_HASH}"
        logger.info(f"New simulation folder created at: {new_sims_folder}")
        return new_sims_folder

    def load_initial_state(self) -> Tuple[Dict, Dict]:
        """Load initial environment and metadata."""
        logger.info("Loading initial state")
        with open(f"{self.orchestrator_sims_folder}/reverie/meta.json", "r") as f:
            meta = json.load(f)

        self.start_time = datetime.strptime(
            f"{meta['start_date']}, 00:00:00", "%B %d, %Y, %H:%M:%S"
        )
        # self.curr_time = datetime.strptime(meta["curr_time"], "%B %d, %Y, %H:%M:%S")
        # for testing can we set time to 7am
        self.curr_time = datetime.strptime(
            f"{meta['start_date']}, 09:00:00", "%B %d, %Y, %H:%M:%S"
        )
        # self.sec_per_step = meta["sec_per_step"]
        self.sec_per_step = 10 * 60
        self.step = meta["step"]
        self.all_personas = meta["persona_names"]
        logger.info(
            f"Initial state loaded. Start time: {self.start_time}, Current time: {self.curr_time}"
        )

        with open(
            f"{self.orchestrator_sims_folder}/environment/{self.step}.json", "r"
        ) as f:
            env = json.load(f)
        logger.info(f"Environment loaded for step {self.step}")
        return env

    def init_personas(self, env: Dict):
        """Initialize the personas."""
        logger.info("Initializing personas")
        maze_json = self.maze.to_json()
        maze_ipfs_hash = upload_maze_json_to_ipfs(maze_json)
        logger.info(f"Maze uploaded to IPFS. Hash: {maze_ipfs_hash}")

        for persona in self.all_personas:
            logger.info(f"Initializing persona: {persona}")
            input_schema = InputSchema(
                task="prepare_persona",
                task_params={
                    "persona_name": persona,
                    "persona_ipfs_hash": PERSONAS[persona],
                    "curr_time": self.curr_time.strftime("%B %d, %Y, %H:%M:%S"),
                    "maze_ipfs_hash": maze_ipfs_hash,
                    "curr_tile": (env[persona]["x"], env[persona]["y"]),
                },
            )
            response = json.loads(module_run(input_schema))
            self.sims_folders[persona] = response["sims_folder"]
            self.persona_tiles[persona] = (env[persona]["x"], env[persona]["y"])
            self.maze_ipfs_hash = maze_ipfs_hash
            logger.info(
                f"Persona {persona} initialized. Sim folder: {self.sims_folders[persona]}, Tile: {self.persona_tiles[persona]}"
            )
        logger.info("All personas initialized")

    def load_environment(self) -> Dict:
        """Load the environment state for the current step."""
        logger.info(f"Loading environment for step {self.step}")
        with open(
            f"{self.orchestrator_sims_folder}/environment/{self.step}.json"
        ) as json_file:
            env = json.load(json_file)
        logger.info(f"Environment loaded for step {self.step}")
        return env

    def get_all_persona_scratch(self) -> Dict[str, Dict]:
        """Get scratch data for all personas."""
        logger.info("Fetching scratch data for all personas")
        persona_scratch = {}
        for persona in self.all_personas:
            logger.info(f"Fetching scratch data for persona: {persona}")
            input_schema = InputSchema(
                task="get_scratch",
                task_params={
                    "persona_name": persona,
                    "sims_folder": self.sims_folders[persona],
                },
            )
            response = json.loads(module_run(input_schema))
            persona_scratch[persona] = response
            logger.info(f"Scratch data fetched for persona: {persona}")
        logger.info("All persona scratch data fetched")
        return persona_scratch

    async def get_all_person_moves_v2(
        self, personas_scratch: Dict[str, Dict]
    ) -> Dict[str, Dict]:
        """Get all persona moves."""
        logger.info("Starting get_all_person_moves_v2")
        moves = {}
        for persona in self.all_personas:
            logger.info(f"Processing moves for persona: {persona}")

            # (1) get perceived and retrieved ; save the memory on persona
            logger.info(f"Getting perceived and retrieved for {persona}")
            input_schema = InputSchema(
                task="get_perceived_retrieved",
                task_params={
                    "init_persona_name": persona,
                    "sims_folder": self.sims_folders[persona],
                    "curr_time": self.curr_time.strftime("%B %d, %Y, %H:%M:%S"),
                    "maze_ipfs_hash": self.maze_ipfs_hash,
                    "curr_tile": self.persona_tiles[persona],
                },
            )
            retrieved_response = module_run(input_schema)
            retrieved_data = json.loads(retrieved_response)
            logger.info(f"Retrieved data for {persona}: {retrieved_data}")
            retrieved = retrieved_data["retrieved"]
            new_day = retrieved_data["new_day"]
            curr_time = retrieved_data["curr_time"]

            # (2) get_reaction_mode
            logger.info(f"Getting reaction mode for {persona}")
            input_schema = InputSchema(
                task="get_reaction_mode",
                task_params={
                    "retrieved": json.dumps(retrieved),
                    "new_day": new_day,
                    "curr_time": curr_time,
                    "maze_ipfs_hash": self.maze_ipfs_hash,
                    "curr_tile": self.persona_tiles[persona],
                    "sims_folder": self.sims_folders[persona],
                    "personas": json.dumps(personas_scratch),
                    "init_persona_name": persona,
                },
            )
            reaction_mode_response = module_run(input_schema)
            reaction_mode_data = json.loads(reaction_mode_response)
            logger.info(f"Reaction mode data for {persona}: {reaction_mode_data}")
            reaction_mode = reaction_mode_data["reaction_mode"]
            focused_event = reaction_mode_data["focused_event"]

            # if persona == "Richard Blythman": # this is to force chat for debug
            #     reaction_mode = "chat with Mo Arshy"

            # if persona == "Mo Arshy" and self.step == 1:
            #     reaction_mode = "chat with Richard Blythman"

            # (3) next step based on reaction_mode
            if reaction_mode:
                if reaction_mode[:9] == "chat with":
                    logger.info(f"{persona} will chat with {reaction_mode[9:]}")
                    self.chat = True
                    self.chat_personas = [persona, reaction_mode[9:]]
                    persona_plan = await self.chat_react_plan(persona, reaction_mode)
                elif reaction_mode[:4] == "wait":
                    logger.info(f"{persona} will wait {reaction_mode[5:]}")
                    persona_plan = await self.wait_react_plan(persona, reaction_mode)
            else:
                logger.info(f"No reaction for {persona}")
                persona_plan = await self.no_reaction_plan(persona)

            logger.info(f"Persona plan for {persona}: {persona_plan}")

            # (4) reflect and execute
            logger.info(f"Reflecting and executing for {persona}")
            input_schema = InputSchema(
                task="get_reflect_execute",
                task_params={
                    "init_persona_name": persona,
                    "sims_folder": self.sims_folders[persona],
                    "personas_curr_tiles": self.persona_tiles,
                    "plan": persona_plan,
                    "maze_ipfs_hash": self.maze_ipfs_hash,
                },
            )
            reflect_execute_response = module_run(input_schema)
            reflect_execute_data = json.loads(reflect_execute_response)
            logger.info(
                f"Reflect and execute response for {persona}: {reflect_execute_data}"
            )
            moves[persona] = reflect_execute_data["execution"]
            self.maze_ipfs_hash = reflect_execute_data["maze_ipfs_hash"]

        logger.info("Completed get_all_person_moves_v2")
        return moves

    async def chat_react_plan(self, persona, reaction_mode):
        logger.info(f"Starting chat_react_plan for {persona}")
        target_persona_name = reaction_mode[9:].strip()

        # Get personal info for both personas
        init_persona_info = json.loads(
            module_run(
                InputSchema(
                    task="get_personal_info",
                    task_params={
                        "init_persona_name": persona,
                        "sims_folder": self.sims_folders[persona],
                    },
                )
            )
        )
        target_persona_info = json.loads(
            module_run(
                InputSchema(
                    task="get_personal_info",
                    task_params={
                        "init_persona_name": target_persona_name,
                        "sims_folder": self.sims_folders[target_persona_name],
                    },
                )
            )
        )

        # Simulate chat
        curr_chat = []
        for i in range(8):
            init_utterance = json.loads(
                module_run(
                    InputSchema(
                        task="get_utterence",
                        task_params={
                            "init_persona_name": persona,
                            "sims_folder": self.sims_folders[persona],
                            "target_persona_name": target_persona_info["name"],
                            "target_persona_description": target_persona_info[
                                "act_description"
                            ],
                            "curr_chat": json.dumps(curr_chat),
                        },
                    )
                )
            )

            target_utterance = json.loads(
                module_run(
                    InputSchema(
                        task="get_utterence",
                        task_params={
                            "init_persona_name": target_persona_name,
                            "sims_folder": self.sims_folders[target_persona_name],
                            "target_persona_name": init_persona_info["name"],
                            "target_persona_description": init_persona_info[
                                "act_description"
                            ],
                            "curr_chat": json.dumps(init_utterance["curr_chat"]),
                        },
                    )
                )
            )

            curr_chat = target_utterance["curr_chat"]
            logger.info(f"Chat iteration {i+1} completed")

        all_utt = "\n".join([f"{row[0]}: {row[1]}" for row in curr_chat])
        convo_length = math.ceil(int(len(all_utt) / 8) / 30)

        target_persona_scratch = json.loads(
            module_run(
                InputSchema(
                    task="get_scratch",
                    task_params={
                        "persona_name": target_persona_name,
                        "sims_folder": self.sims_folders[target_persona_name],
                    },
                )
            )
        )

        logger.info(f"Chat react plan for {persona}")

        complete_plan_response = json.loads(
            module_run(
                InputSchema(
                    task="get_complete_plan_chat",
                    task_params={
                        "all_utt": all_utt,
                        "init_persona_name": persona,
                        "sims_folder": self.sims_folders[persona],
                        "target_persona_scratch": target_persona_scratch,
                        "maze_ipfs_hash": self.maze_ipfs_hash,
                        "convo_length": convo_length,
                    },
                )
            )
        )

        init_persona_act_address = complete_plan_response["init_persona_act_address"]
        target_persona_return = complete_plan_response["target_persona_return"]

        # make a call to the target persona to return the values
        finalise_target_persona = json.loads(
            module_run(
                InputSchema(
                    task="finalise_target_persona_chat",
                    task_params={
                        "target_persona_name": target_persona_name,
                        "target_persona_return": target_persona_return,
                        "sims_folder": self.sims_folders[target_persona_name],
                    },
                )
            )
        )

        logger.info(f"Chat react plan completed for {persona}")
        return init_persona_act_address

    async def wait_react_plan(self, persona, reaction_mode):
        logger.info(f"Starting wait_react_plan for {persona}")
        wait_react_response = json.loads(
            module_run(
                InputSchema(
                    task="get_complete_plan_wait",
                    task_params={
                        "init_persona_name": persona,
                        "sims_folder": self.sims_folders[persona],
                        "reaction_mode": reaction_mode,
                    },
                )
            )
        )
        logger.info(f"Wait react plan completed for {persona}")
        return wait_react_response

    async def no_reaction_plan(self, persona):
        logger.info(f"Starting no_reaction_plan for {persona}")
        no_reaction_response = json.loads(
            module_run(
                InputSchema(
                    task="get_complete_plan_no_reaction",
                    task_params={
                        "init_persona_name": persona,
                        "sims_folder": self.sims_folders[persona],
                    },
                )
            )
        )
        logger.info(f"No reaction plan completed for {persona}")
        return no_reaction_response

    def update_environment(self, new_env: Dict, personas_scratch: Dict[str, Dict]):
        """Update the environment based on persona movements."""
        logger.info("Updating environment")
        for persona in self.all_personas:
            curr_tile = self.persona_tiles[persona]
            new_tile = (new_env[persona]["x"], new_env[persona]["y"])
            self.persona_tiles[persona] = new_tile
            logger.info(
                f"Updating position for persona {persona}: {curr_tile} -> {new_tile}"
            )

            logger.info(f"Removing events for persona {persona} from tile {curr_tile}")
            self.maze.remove_subject_events_from_tile(persona, curr_tile)

            persona_event = self.get_curr_event_and_desc(personas_scratch[persona])
            logger.info(f"Adding new event for persona {persona} to tile {new_tile}")
            self.maze.add_event_from_tile(persona_event, new_tile)

        logger.info("Environment update completed")

    def get_curr_event_and_desc(
        self, persona_scratch: Dict
    ) -> Tuple[str, Any, Any, Any]:
        """Get the current event and description for a persona."""
        act_address = persona_scratch.get("act_address")
        if not act_address:
            logger.info("No act_address found for persona. Returning empty event.")
            return (persona_scratch["name"], None, None, None)
        else:
            return (
                persona_scratch["act_event"][0],
                persona_scratch["act_event"][1],
                persona_scratch["act_event"][2],
                persona_scratch["act_description"],
            )

    def get_curr_obj_event_and_desc(
        self, persona_scratch: Dict
    ) -> Tuple[str, Any, Any, Any]:
        """Get the current object event and description for a persona."""
        act_address = persona_scratch.get("act_address")
        if not act_address:
            logger.info("No act_address found for persona. Returning empty event.")
            return ("", None, None, None)
        return (
            act_address,
            persona_scratch["act_obj_event"][1],
            persona_scratch["act_obj_event"][2],
            persona_scratch["act_obj_description"],
        )

    def save_movements(self, step: int, movements: Dict[str, Dict]):
        """Save the movements for the current step."""
        logger.info(f"Saving movements for step {step}")

        formatted_movements = {
            "persona": {},
            "meta": {"curr_time": self.curr_time.strftime("%B %d, %Y, %H:%M:%S")},
        }

        for persona, data in movements.items():
            formatted_movements["persona"][persona] = {
                "movement": data[0],
                "pronunciation": data[1],
                "description": data[2],
                "chat": self.personas_scratch[persona]["chat"],
            }

        if self.chat:
            formatted_movements["persona"][self.chat_personas[1].strip()]["chat"] = (
                self.personas_scratch[self.chat_personas[0].strip()]["chat"]
            )

        self.chat = False
        self.chat_personas = []

        if not os.path.exists(f"{self.orchestrator_sims_folder}/movement"):
            os.makedirs(f"{self.orchestrator_sims_folder}/movement", exist_ok=True)

        with open(
            f"{self.orchestrator_sims_folder}/movement/{step}.json", "w"
        ) as outfile:
            json.dump(formatted_movements, outfile, indent=2)

        logger.info(f"Movements saved for step {step}")

    def save_state(self, final_step=None):
        """Save the state of the simulation."""
        logger.info("Saving simulation state")

        folder_info = {
            "orchestrator_sims_folder": self.orchestrator_sims_folder,
            "personas": self.all_personas,
            "num_steps": self.num_steps,
            "start_time": self.start_time.strftime("%B %d, %Y, %H:%M:%S"),
            "end_time": self.curr_time.strftime("%B %d, %Y, %H:%M:%S"),
            "sec_per_step": self.sec_per_step,
            "sims_folders": self.sims_folders,
            "maze_ipfs_hash": self.maze_ipfs_hash,
            "current_step": self.step,
        }
        with open(
            f"{self.orchestrator_sims_folder}/simulation_info.json", "w"
        ) as outfile:
            json.dump(folder_info, outfile, indent=2)

        logger.info(f"State saved to {self.orchestrator_sims_folder}")

        if final_step:
            final_json_ipfs_hash = upload_json_file_to_ipfs(
                f"{self.orchestrator_sims_folder}/simulation_info.json"
            )
            return folder_info, final_json_ipfs_hash
        return folder_info, None

    async def run_simulation(self):
        """Run the simulation for a specified number of steps."""
        logger.info(
            f"Starting simulation from step {self.step} for {self.num_steps} steps"
        )
        for _ in range(self.num_steps):
            logger.info(f"Processing step {self.step} of {self.num_steps}")
            await self.process_step()
            logger.info(f"Step {self.step} completed. Current time: {self.curr_time}")

        return self.save_state(final_step=True)

    def save_environment(self, step: int, movements: Dict[str, List]):
        """Save the environment state for the current step."""
        logger.info(f"Saving environment for step {step}")
        new_env = {}
        for persona, data in movements.items():
            new_env[persona] = {"maze": "the_ville", "x": data[0][0], "y": data[0][1]}

        with open(
            f"{self.orchestrator_sims_folder}/environment/{step}.json", "w"
        ) as outfile:
            json.dump(new_env, outfile, indent=2)
        logger.info(f"Environment saved for step {step}")

    async def process_step(self):
        """Process a single simulation step."""
        logger.info(f"Processing step {self.step}")
        # Load environment
        new_env = self.load_environment()

        # <game_obj_cleanup> cleanup
        for key, value in self.game_obj_cleanup.items():
            self.maze.turn_event_from_tile_idle(key, value)

        self.game_obj_cleanup = {}

        # Get all persona scratch
        self.personas_scratch = self.get_all_persona_scratch()

        # Get curr tiles
        for persona in self.all_personas:
            curr_tile = self.persona_tiles[persona]
            new_tile = (new_env[persona]["x"], new_env[persona]["y"])
            self.persona_tiles[persona] = new_tile
            self.maze.remove_subject_events_from_tile(persona, curr_tile)
            self.maze.add_event_from_tile(
                self.get_curr_event_and_desc(self.personas_scratch[persona]), new_tile
            )

            if not self.personas_scratch[persona]["planned_path"]:
                self.game_obj_cleanup[
                    self.get_curr_obj_event_and_desc(self.personas_scratch[persona])
                ] = new_tile
                self.maze.add_event_from_tile(
                    self.get_curr_obj_event_and_desc(self.personas_scratch[persona]),
                    new_tile,
                )
                blank = (
                    self.get_curr_obj_event_and_desc(self.personas_scratch[persona])[0],
                    None,
                    None,
                    None,
                )
                self.maze.remove_event_from_tile(blank, new_tile)

        # Upload maze to IPFS
        self.maze_ipfs_hash = upload_maze_json_to_ipfs(self.maze.to_json())

        # Get all movements
        movements = await self.get_all_person_moves_v2(self.personas_scratch)
        logger.info(f"Movements: {movements}")

        self.personas_scratch = self.get_all_persona_scratch()
        self.update_environment(new_env, self.personas_scratch)
        self.save_movements(self.step, movements)

        self.step += 1
        self.curr_time += timedelta(seconds=self.sec_per_step)
        self.save_environment(self.step, movements)
        self.save_state()
        logger.info(f"Step {self.step} processing completed")


class InputSchema(BaseModel):
    task: str
    task_params: Dict


async def run(inputs, cfg: Dict = None):
    logger.info(f"Running simulation with inputs: {inputs}")

    num_steps = inputs["num_steps"]
    ipfs_hash = inputs.get("ipfs_hash")

    sim_manager = SimulationManager(num_steps, ipfs_hash)

    if not ipfs_hash:
        sim_manager.init_simulation()

    orchestrator_sims_folder = sim_manager.orchestrator_sims_folder
    folder_info = None
    final_json_ipfs_hash = None
    try:
        folder_info, final_json_ipfs_hash = await sim_manager.run_simulation()
        # pass
    except Exception as e:
        logger.error(f"Error running simulation: {e}")
        final_json_ipfs_hash = upload_json_file_to_ipfs(
            f"{orchestrator_sims_folder}/simulation_info.json"
        )
        return {
            "error": "Error running simulation",
            "folder_info": folder_info,
            "final_json_ipfs_hash": final_json_ipfs_hash,
        }

    logger.info("Simulation completed successfully")
    return {"folder_info": folder_info, "final_json_ipfs_hash": final_json_ipfs_hash}


if __name__ == "__main__":
    inputs = {"num_steps": 300}
    logger.info("Starting main execution")
    result = asyncio.run(run(inputs))
    logger.info(f"Execution completed. Result: {result}")
