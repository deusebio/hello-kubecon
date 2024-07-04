from functools import cached_property
from typing import TypeVar, Generic, Type, Any, Dict, Union

from typing_extensions import Self

from ops.charm import CharmBase
from ops.model import ConfigData
from pydantic import BaseModel, ValidationError

ReadOnlyTypes = Union[ConfigData, Dict[str, Any]]


class ReadOnlyData(BaseModel):

    @classmethod
    def read(cls, raw: ReadOnlyTypes) -> Self:
        try:
            table = str.maketrans("-", "_")
            return cls(**{
                key.translate(table): value
                for key, value in raw.items()
            })
        except ValidationError as e:
            raise e


TypedConfig = TypeVar("TypedConfig", bound=ReadOnlyData)


class TypeSafeCharmBase(CharmBase, Generic[TypedConfig]):
    """Class to be used for extending config-typed charms."""

    config_type: Type[TypedConfig]

    @cached_property
    def config(self) -> TypedConfig:
        return self.config_type.read(self.model.config)
