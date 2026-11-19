from dataclasses import fields, is_dataclass
from enum import Enum

def to_dict(value):
    if is_dataclass(value):
        return {f.name: to_dict(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {k: to_dict(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [to_dict(v) for v in value]
    if isinstance(value, Enum): return value.value
    return value
