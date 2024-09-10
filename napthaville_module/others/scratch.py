import json
import os
import logging
from napthaville.persona.persona import Persona
from napthaville.utils import scratch_to_dict
from napthaville_module.utils import setup_logging


setup_logging()
logger = logging.getLogger(__name__)


def get_scratch(task_params: dict):
    logger.info(f"Getting scratch for persona: {task_params}")
    persona_name = task_params["persona_name"]
    sims_folder = task_params["sims_folder"]
    persona_folder = f"{os.getenv('BASE_OUTPUT_DIR')}/{sims_folder}"
    persona = Persona(persona_name, persona_folder)
    scratch = scratch_to_dict(persona.scratch)
    return json.dumps(scratch)
