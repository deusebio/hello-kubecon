from pydantic import BaseModel
from typing import Literal, ClassVar, Optional, Generic, TypeVar, Tuple
import json
from pydantic.json import pydantic_encoder


from ops import RelationDataContent

Backend = Literal["json", "yaml"]

NativeTypes = str | int | float

T = TypeVar("T", bound=BaseModel)

class Serializer(Generic[T]):

    @classmethod
    def serialize(cls, name: str, value: NativeTypes | BaseModel | dict) -> Tuple[str, str]:
        """Serialize the key, value pair."""
        if (
                isinstance(value, str) or
                isinstance(value, int) or
                isinstance(value, float)
        ):
            serialized_value = str(value)
        elif isinstance(value, BaseModel):
            serialized_value = cls._dumps()(value.dict())
        elif isinstance(value, dict) or isinstance(value, list):
            serialized_value = cls._dumps()(value)
        else:
            raise ValueError(f"Type of value {type(value)} not serializable")

        return (
            name.replace("_", "-"),
            serialized_value
        )

    @classmethod
    def read(cls, relation_data: RelationDataContent) -> T:
        """Read data from a relation databag and parse it into a domain object.

        Args:
            relation_data: pointer to the relation databag
            obj: pydantic class represeting the model to be used for parsing
        """
        return cls(**{
            field_name: cls._loads()(
                relation_data[parsed_key]) if field.annotation not in (
                str, int) else str(relation_data[parsed_key])
            for field_name, field in cls.__fields__.items()
            if (parsed_key := field_name.replace("_", "-")) in relation_data
        })


    def dump(self, obj: BaseModel) -> str:
        pass

    def load(self, raw: str) -> BaseModel:
        pass

class JsonSerializer(Serializer):
    def dump(self, obj: BaseModel) -> str:
        return json.dumps(obj, default=pydantic_encoder)

    def load(self, raw: str) -> BaseModel:
        pass




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

    _backend: ClassVar[Backend] = "json"

    _relation: Optional[RelationDataContent] = None

    @classmethod
    def _loads(cls):
        if cls._backend == "json":
            def func(raw):
                return json.loads(raw)
            return func
        elif cls._backend == "yaml":
            def func(raw):
                return yaml.safe_load(raw)
            return func

    @classmethod
    def _dumps(cls):
        if cls._backend == "json":
            return lambda obj: json.dumps(obj, default=pydantic_encoder)
        elif cls._backend == "yaml":
            return lambda obj: yaml.safe_dump(obj)

    @classmethod
    def serialize(cls, name, value) -> Tuple[str, str]:
        """Serialize the key, value pair."""
        if (
                isinstance(value, str) or
                isinstance(value, int) or
                isinstance(value, float)
        ):
            serialized_value = str(value)
        elif isinstance(value, BaseModel):
            serialized_value = cls._dumps()(value.dict())
        elif isinstance(value, dict) or isinstance(value, list):
            serialized_value = cls._dumps()(value)
        else:
            raise ValueError(f"Type of value {type(value)} not serializable")

        return (
            name.replace("_", "-"),
            serialized_value
        )

    def __setattr__(self, name, value):
        if name != "_relation" and self._relation is None:
            raise IOError(f"property {name} cannot be set, as the model is not binded to any databag")

        BaseModel.__setattr__(self, name, value)

        if self._relation is not None and name != "_relation":
            parsed_value = getattr(self, name)
            serialized_key, serialized_value = self.serialize(name,
                                                              parsed_value)
            self._relation[serialized_key] = serialized_value

    def bind(self, relation: RelationDataContent):
        """Create a binding with a relation data.

        When updating the pydantic attributes, the values will be serialized
        to the relation data bag.
        """
        self._relation = relation
        for name in self.__fields__.keys():
            parsed_value = getattr(self, name)
            serialized_key, serialized_value = self.serialize(name,
                                                              parsed_value)
            self._relation[serialized_key] = serialized_value
        return self

    def unbind(self):
        self._relation = None
        return self

    @classmethod
    def read(cls, relation_data: RelationDataContent) -> Self:
        """Read data from a relation databag and parse it into a domain object.

        Args:
            relation_data: pointer to the relation databag
            obj: pydantic class represeting the model to be used for parsing
        """
        return cls(**{
            field_name: cls._loads()(
                relation_data[parsed_key]) if field.annotation not in (
                str, int) else str(relation_data[parsed_key])
            for field_name, field in cls.__fields__.items()
            if (parsed_key := field_name.replace("_", "-")) in relation_data
        })
