from typing import Type
from pydantic import BaseModel


def model_structure_repr(model: Type[BaseModel]) -> str:
    fields = model.__annotations__
    return ", ".join(f"{key}: {value}" for key, value in fields.items())


def extract_first_nested_dict(data_dict):
    # If it's already a flat dictionary with our parameters, return it
    if all(isinstance(v, (str, int, float)) for v in data_dict.values()):
        return data_dict
    # Otherwise, look for nested dictionary
    for key, value in data_dict.items():
        if isinstance(value, dict):
            return value
    return {}
