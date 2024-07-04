import json
from typing import Mapping
from typing import Optional, TypeVar, Tuple, Union

import yaml
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic.json import pydantic_encoder

NativeTypes = Union[str, int, float]

T = TypeVar("T", bound=BaseModel)

from abc import abstractmethod


class Serializer:

    @classmethod
    @abstractmethod
    def dump(cls, obj: Union[dict, list]) -> str:
        pass

    @classmethod
    @abstractmethod
    def load(cls, obj: str) -> Union[dict, list]:
        pass

    @classmethod
    def serialize(cls, name: str, value: Union[NativeTypes, BaseModel, dict, list]) -> Tuple[str, str]:
        """Serialize the key, value pair."""
        if (
                isinstance(value, str) or
                isinstance(value, int) or
                isinstance(value, float)
        ):
            serialized_value = str(value)
        elif isinstance(value, BaseModel):
            serialized_value = cls.dump(value.dict())
        elif isinstance(value, dict) or isinstance(value, list):
            serialized_value = cls.dump(value)
        else:
            raise ValueError(f"Type of value {type(value)} not serializable")

        return (
            name.replace("_", "-"),
            serialized_value
        )

    @classmethod
    def deserialize(cls, data: Mapping[str, str], key: str, field_info: FieldInfo) -> Optional[NativeTypes]:
        parsed_key = key.replace("_", "-")
        if parsed_key not in data:
            return None
        value = data[parsed_key]
        return cls.load(value) if field_info.annotation not in (str, int) else str(value)


class JsonSerializer(Serializer):
    @classmethod
    def dump(cls, obj: Union[dict, list]) -> str:
        return json.dumps(obj, default=pydantic_encoder)

    @classmethod
    def load(cls, raw: str) -> Union[dict, list]:
        return json.loads(raw)


class YamlSerializer(Serializer):
    @classmethod
    def dump(cls, obj: Union[dict, list]) -> str:
        return yaml.safe_dump(obj)

    @classmethod
    def load(cls, raw: str) -> Union[dict, list]:
        return yaml.safe_load(raw)
