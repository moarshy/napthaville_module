import os 
import logging


BASE_OUTPUT_DIR = os.getenv("BASE_OUTPUT_DIR", None)
PERSONAS_FOLDER = f"{BASE_OUTPUT_DIR}/napthaville/step-3-3/personas"
MAZE_FOLDER = f"{BASE_OUTPUT_DIR}/napthaville/the_ville/matrix"


ALL_PERSONAS = [
    "Isabella Rodriguez",
    "Maria Lopez",
    "Klaus Mueller"
]


def _check_persona(persona_name: str):
    if persona_name not in ALL_PERSONAS:
        return False
    return True


def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger