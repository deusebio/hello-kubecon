from typing import Optional, ClassVar
from typing_extensions import Self

from ops import RelationDataContent
from pydantic import BaseModel

from common.core.v2.serializers import BaseSerializer, JsonSerializer

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

    _backend: ClassVar[BaseSerializer] = JsonSerializer()
    _relation: Optional[RelationDataContent] = None

    def __setattr__(self, name, value):
        if name != "_relation" and self._relation is None:
            raise IOError(f"property {name} cannot be set, as the model is not binded to any databag")

        BaseModel.__setattr__(self, name, value)

        if self._relation is not None and name != "_relation":
            parsed_value = getattr(self, name)
            serialized_key, serialized_value = self._backend.serialize(name, parsed_value)
            self._relation[serialized_key] = serialized_value

    def bind(self, relation: RelationDataContent):
        """Create a binding with a relation data.

        When updating the pydantic attributes, the values will be serialized
        to the relation data bag.
        """
        self._relation = relation
        for name in self.model_fields.keys():
            parsed_value = getattr(self, name)
            serialized_key, serialized_value = self._backend.serialize(name, parsed_value)
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
            name: value
            for name, field in cls.model_fields.items()
            if (value := cls._backend.deserialize(relation_data, name, field))
        })