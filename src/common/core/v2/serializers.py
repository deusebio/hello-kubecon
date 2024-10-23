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

class BaseSerializer:

    def serialize(self, name: str, value: Union[NativeTypes, BaseModel, dict, list]) -> Tuple[str, str]:
        """Return the serialized version of the key and value."""
        pass

    def deserialize(self, data: Mapping[str, str], key: str, field_info: FieldInfo) -> Optional[NativeTypes]:
        """Return the deserialized version for a given key in the data, according to the specification. """
        pass


class DictSerializer(BaseSerializer):

    @classmethod
    @abstractmethod
    def dump(cls, obj: Union[dict, list]) -> str:
        pass

    @classmethod
    @abstractmethod
    def load(cls, obj: str) -> Union[dict, list]:
        pass

    @staticmethod
    def _to_raw(item: Union[BaseModel, dict, list]) -> Union[list, dict]:
        if isinstance(item, BaseModel):
            return item.model_dump()
        elif isinstance(item, list):
            return [DictSerializer._to_raw(element) for element in item]
        elif isinstance(item, dict):
            return {key: DictSerializer._to_raw(value) for key, value in item.items()}
        else:
            raise ValueError(f"type {type(item)} not recognized")

    def serialize(self, name: str, value: Union[NativeTypes, BaseModel, dict, list]) -> Tuple[str, str]:
        """Serialize the key, value pair."""
        if (
                isinstance(value, str) or
                isinstance(value, int) or
                isinstance(value, float)
        ):
            serialized_value = str(value)
        elif isinstance(value, BaseModel) or isinstance(value, dict) or isinstance(value, list):
            serialized_value = self.dump(self._to_raw(value))
        else:
            raise ValueError(f"Type of value {type(value)} not serializable")

        return (
            name.replace("_", "-"),
            serialized_value
        )

    def deserialize(self, data: Mapping[str, str], key: str, field_info: FieldInfo) -> Optional[NativeTypes]:
        parsed_key = key.replace("_", "-")
        if parsed_key not in data:
            return None
        value = data[parsed_key]
        return self.load(value) if field_info.annotation not in (str, int) else str(value)


class JsonSerializer(DictSerializer):
    @classmethod
    def dump(cls, obj: Union[dict, list]) -> str:
        return json.dumps(obj, default=pydantic_encoder)

    @classmethod
    def load(cls, raw: str) -> Union[dict, list]:
        return json.loads(raw)


class YamlSerializer(DictSerializer):
    @classmethod
    def dump(cls, obj: Union[dict, list]) -> str:
        return yaml.safe_dump(obj)

    @classmethod
    def load(cls, raw: str) -> Union[dict, list]:
        return yaml.safe_load(raw)


# from ops import Model
#
# class SecretWrapper(BaseSerializer):
#
#     def __init__(
#         self, serializer: DictSerializer, model: Model, secrets: dict[str, str]
#     ):
#         self.serializer = serializer
#         self.model = model
#         self.secrets = secrets
#
#     def serialize(self, name: str, value: Union[NativeTypes, BaseModel, dict, list]) -> Tuple[str, str]:
#         """Return the serialized version of the key and value."""
#         field_name, content =  self.serializer.serialize(name, value)
#
#         pass
#
#     def deserialize(cls, data: Mapping[str, str], key: str, field_info: FieldInfo) -> Optional[NativeTypes]:
#         """Return the deserialized version for a given key in the data, according to the specification. """
#         pass
#
#
#     def dump(self, obj: dict | list) -> str:
#         content =  self.serializer.dump(obj, default=pydantic_encoder)
#         # write content to secret
#
#     def load(self, raw: str) -> dict | list:
#         return yaml.loads(raw)
#
#     @classmethod
#     def from_data_content(cls, data_content: Mapping[[str, str], key_secrets: list[str]):
#         # read secrets id
#         pass
#
# class Protocol:
#     serializer: Serializer
#     data: RelationDataContent
#



