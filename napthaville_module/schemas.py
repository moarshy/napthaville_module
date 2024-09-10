from pydantic import BaseModel
from typing import Dict, Any


class InputSchema(BaseModel):
    task: str
    task_params: Dict[str, Any]
