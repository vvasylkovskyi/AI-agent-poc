from typing import Callable
from pydantic import BaseModel


class Tool:
    def __init__(self, name: str, description: str, func: Callable) -> None:
        self.name = name
        self.description = description
        self.func = func

    def act(self, **kwargs) -> str:
        return self.func(**kwargs)


class ToolChoice(BaseModel):
    tool_name: str
    reason_of_choice: str
