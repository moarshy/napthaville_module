import json
import logging
from napthaville_module.schemas import InputSchema
from napthaville_module.others.chat import get_personal_info, get_utterence
from napthaville_module.cognitive_modules.reflect_execute import get_reflect_execute
from napthaville_module.cognitive_modules.perceive_retrieve import (
    get_perceived_retrieved,
)
from napthaville_module.cognitive_modules.plan import get_plan
from napthaville_module.others.scratch import get_scratch
from napthaville_module.others.move import get_move
from napthaville_module.others.prepare import prepare_persona, fork_persona
from napthaville_module.utils import BASE_OUTPUT_DIR, setup_logging
from napthaville_module.cognitive_modules.plan import get_reaction_mode
from napthaville_module.cognitive_modules.plan import (
    get_complete_plan_chat,
    get_complete_plan_wait,
    get_complete_plan_no_reaction,
    finalise_target_persona_chat,
)

setup_logging()
logger = logging.getLogger(__name__)


def run(
    inputs: InputSchema,
    worker_nodes=None,
    orchestrator_node=None,
    flow_run=None,
    cfg: dict = None,
):
    if BASE_OUTPUT_DIR is None:
        return json.dumps({"error": "BASE_OUTPUT_DIR is not set"})
    # logger.info(f"Running task {inputs.task} with params {inputs.task_params}")

    task = inputs.task
    task_params = inputs.task_params

    if task == "get_personal_info":
        return get_personal_info(task_params)

    elif task == "get_utterence":
        return get_utterence(task_params)

    elif task == "get_perceived_retrieved":
        return get_perceived_retrieved(task_params)

    elif task == "get_scratch":
        return get_scratch(task_params)

    elif task == "get_plan":
        return get_plan(task_params)

    elif task == "get_move":
        return get_move(task_params)

    elif task == "fork_persona":
        return fork_persona(task_params)

    elif task == "get_reaction_mode":
        return get_reaction_mode(task_params)

    elif task == "get_reflect_execute":
        return get_reflect_execute(task_params)

    elif task == "get_complete_plan_chat":
        return get_complete_plan_chat(task_params)

    elif task == "get_complete_plan_wait":
        return get_complete_plan_wait(task_params)

    elif task == "get_complete_plan_no_reaction":
        return get_complete_plan_no_reaction(task_params)

    elif task == "prepare_persona":
        return prepare_persona(task_params)

    elif task == "finalise_target_persona_chat":
        return finalise_target_persona_chat(task_params)

    else:
        return json.dumps({"error": f"Task {task} not found"})
