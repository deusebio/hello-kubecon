from pydantic import BaseModel
from typing import Literal, ClassVar, Optional, Generic, TypeVar, Tuple
import json
from pydantic.json import pydantic_encoder

from pydantic import Field
from ops import RelationDataContent, Model
from typing import Mapping

import yaml

Backend = Literal["json", "yaml"]

NativeTypes = str | int | float

T = TypeVar("T", bound=BaseModel)

from abc import abstractmethod


class Serializer:

    @classmethod
    @abstractmethod
    def dump(cls, obj: dict | list) -> str:
        pass

    @classmethod
    @abstractmethod
    def load(cls, obj: str) -> dict | list:
        pass

    @classmethod
    def serialize(cls, name: str, value: NativeTypes | BaseModel | dict | list) -> Tuple[str, str]:
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
    def deserialize(cls, data: Mapping[str, str], field: Field) -> Optional[str | list | dict]:
        parsed_key = field.name.replace("_", "-")
        if parsed_key not in data:
            return None
        value = data[parsed_key]
        return cls.load(value) if field.annotation not in (str, int) else str(value)


class JsonSerializer(Serializer):
    def dump(self, obj: dict | list) -> str:
        return json.dumps(obj, default=pydantic_encoder)

    def load(self, raw: str) -> dict | list:
        return json.loads(raw)


class YamlSerializer(Serializer):
    def dump(self, obj: dict | list) -> str:
        return yaml.dumps(obj, default=pydantic_encoder)

    def load(self, raw: str) -> dict | list:
        return yaml.loads(raw)

class SecretWrapper(Serializer):

    def __init__(
        self, serializer: Serializer, model: Model, secrets: dict[str, str]
    ):
        self.serializer = serializer
        self.model = model
        self.secrets = secrets

    def dump(self, obj: dict | list) -> str:
        content =  self.serializer.dump(obj, default=pydantic_encoder)
        # write content to secret

    def load(self, raw: str) -> dict | list:
        return yaml.loads(raw)

    @classmethod
    def from_data_content(cls, data_content: Mapping[[str, str], key_secrets: list[str]):
        # read secrets id
        pass

class Protocol:
    serializer: Serializer
    data: RelationDataContent


class BaseRelationData(BaseModel, validate_assignment=True):
    """Base class to provide pydantic representation for Juju databag.

    The class also takes care of serializing/deserializing the content into
    the relation data, using either json or yaml serialization.

    A databag can simply be defined with

    ```
    class Foo(BaseRelationData):
        bar: int
        baz: float
    ```

    Data parsing and validation from RelationDataContent can be done with

    ```
    foo = Foo.read(relation_data)
    ```

    Writing is done by binding a particular BaseRelationData object to some
    relation_data

    ```
    foo.bind(relation_data)
    ```

    Once a binding with some RelationDataContent object is done, item assigment
    takes care of validating and serializing the value into the databag. For
    complex types (derived by pydantic BaseModel) on subfield, either json or
    yaml representation is used, e.g.

    ```
    class Baz(BaseModel):
        baz: int

    class Bar(BaseModel):
        bazs: List[Baz]

    class Foo(BaseRelationData):
        bar: Bar

    foo = Foo(
        bar = Bar(
            bazs=[Baz(baz=1)]
        )
    ).bind(relation_data)

    assert relation_data["bar"] == "{'bazs': [{'baz' : 1}]}"

    # Error - the type is not correct
    foo.bar = 1

    # Success
    foo.bar = Bar(bazs=[Bar(baz=2)])

    assert relation_data["bar"] == "{'bazs': [{'baz' : 2}]}"
    ```
    """

    _protocol: Optional[Protocol] = None

    def __setattr__(self, name, value):
        if name != "_protocol" and self._protocol is None:
            raise IOError(f"property {name} cannot be set, as the model is not binded to any databag")

        BaseModel.__setattr__(self, name, value)

        if (protocol := self._protocol) and name != "_protocol":
            parsed_value = getattr(self, name)
            serialized_key, serialized_value = protocol.serializer.serialize(name, parsed_value)
            self._protocol.data[serialized_key] = serialized_value

    def bind(self, protocol: Protocol):
        """Create a binding with a relation data.

        When updating the pydantic attributes, the values will be serialized
        to the relation data bag.
        """
        self._protocol = protocol
        for name in self.__fields__.keys():
            parsed_value = getattr(self, name)
            serialized_key, serialized_value = protocol.serializer.serialize(name, parsed_value)
            self._protocol.data[serialized_key] = serialized_value
        return self

    def unbind(self):
        self._protocol = None
        return self

    @classmethod
    def read(cls, protocol: Protocol) -> Self:
        """Read data from a relation databag and parse it into a domain object.

        Args:
            relation_data: pointer to the relation databag
            obj: pydantic class represeting the model to be used for parsing
        """
        return cls(**{
            field_name: value
            for field_name, field in cls.__fields__.items()
            if (value := protocol.serializer.deserialize(protocol.data, field))
        })