from typing import List

from pydantic import BaseModel, model_validator, ConfigDict
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated

from common.core.classes import ReadOnlyData
from common.core.v2.relations import BaseRelationData
from common.core.v2.serializers import JsonSerializer


class HelloKubeconConfig(ReadOnlyData):
    """Data model for charm config."""

    external_hostname: str
    redirect_map: str

    @model_validator(mode="before")
    @classmethod
    def combined_field_validator(cls, values):
        if values.get("external_hostname") == values.get("redirect_map"):
            raise ValueError("The two values cannot be the same")
        return values


def is_url(v: str):
    if not v.startswith("http"):
        raise ValueError('url should be starting with http')
    return v


Url = Annotated[str, AfterValidator(is_url)]


class PullActionModel(ReadOnlyData):
    """Data model for parameters of the pull action."""

    url: Url


class SubField(BaseModel):
    """Data model for a subfield of a complicated property in the relation databag."""
    subkey: str


class PeerRelationAppData(BaseRelationData):
    """Data model for the relation databag."""
    _backend = JsonSerializer()
    model_config = ConfigDict(arbitrary_types_allowed=True)

    my_key: float
    complex_property: List[SubField]


class PeerUnitData(BaseRelationData):
    _backend = JsonSerializer()

    ingress_address: str
