import json
from napthaville_module.schemas import InputSchema
from napthaville_module.others.chat import get_personal_info, get_utterence
from napthaville_module.cognitive_modules.perceive import get_perception
from napthaville_module.cognitive_modules.retrieve import get_retrieved_events
from napthaville_module.cognitive_modules.perceive_retrieve import get_perceive_retrieve
from napthaville_module.cognitive_modules.plan import get_plan
from napthaville_module.others.scratch import get_scratch
from napthaville_module.others.move import get_move
from napthaville_module.utils import BASE_OUTPUT_DIR, ALL_PERSONAS, get_logger


logger = get_logger()


def run(inputs: InputSchema, worker_nodes = None, orchestrator_node = None, flow_run = None, cfg: dict = None):
    if BASE_OUTPUT_DIR is None:
        return json.dumps({"error": "BASE_OUTPUT_DIR is not set"})
    logger.info(f"Running task {inputs.task} with params {inputs.task_params}")

    task = inputs.task
    task_params = inputs.task_params

    if task == "get_personal_info":
        return get_personal_info(task_params)
    
    elif task == "get_utterence":
        return get_utterence(task_params)
    
    elif task == "get_perception":
        return get_perception(task_params)
    
    elif task == "get_retrieved_events":
        return get_retrieved_events(task_params)
    
    elif task == "get_perceive_retrieve":
        return get_perceive_retrieve(task_params)
    
    elif task == "get_scratch":
        return get_scratch(task_params)
    
    elif task == "get_plan":
        return get_plan(task_params)
    
    elif task == "get_move":
        return get_move(task_params)
    
    else:
        res = {
            "error": f"Task {task} not found. Please choose from {ALL_PERSONAS}"
        }
        return json.dumps(res)


# if __name__ == "__main__":
    # # Test get_personal_info
    # inputs = {
    #     "task": "get_personal_info",
    #     "task_params": {
    #         "persona_name": "Isabella Rodriguez",
    #     }
    # }

    # inputs = InputSchema(**inputs)

    # res = run(inputs)
    # print(res)
    # print(type(res))

    # # Test get_utterence
    # inputs = {
    #     "task": "get_utterence",
    #     "task_params": {
    #         "init_persona_name": "Isabella Rodriguez",
    #         "target_persona_name": "Maria Lopez",
    #         "target_persona_description": "sleeping",
    #         "curr_chat": "[]",
    #         "maze_folder": "/Users/arshath/play/playground/gen_agents/storage_and_statics/the_ville/matrix"
    #     }
    # }

    # inputs = InputSchema(**inputs)
    # res = run(inputs)
    # print(res)
    # print(type(res))
    # res = json.loads(res)
    # print(type(res))
    # print(res['curr_chat'])
    # print(type(res['curr_chat']))


    # inputs = {
    #     "task": "get_utterence",
    #     "task_params": {
    #         "init_persona_name": "Maria Lopez",
    #         "target_persona_name": "Isabella Rodriguez",
    #         "target_persona_description": "sleeping",
    #         "curr_chat": json.dumps(res['curr_chat']),
    #         "maze_folder": "/Users/arshath/play/playground/gen_agents/storage_and_statics/the_ville/matrix"
    #     }
    # }
    # inputs = InputSchema(**inputs)
    # res = run(inputs)
    # print(res)