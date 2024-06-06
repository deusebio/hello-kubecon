from typing import List

from pydantic import BaseModel, model_validator, ConfigDict
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated

from charms.core.relations import BaseRelationData


class HelloKubeconConfig(BaseModel):
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


class PullActionModel(BaseModel):
    """Data model for parameters of the pull action."""

    url: Url


class SubField(BaseModel):
    """Data model for a subfield of a complicated property in the relation databag."""
    subkey: str


class PeerRelationAppData(BaseRelationData):
    """Data model for the relation databag."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    my_key: float
    complex_property: List[SubField]
