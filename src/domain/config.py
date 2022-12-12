from typing import List
from pydantic import BaseModel, root_validator, validator

from charms.core.relations import RelationDataModel


class HelloKubeconConfig(BaseModel):
    """Data model for charm config."""

    external_hostname: str
    redirect_map: str

    @root_validator(pre=False)
    def combined_field_validator(cls, values):
        if values.get("external_hostname") == values.get("redirect_map"):
            raise ValueError("The two values cannot be the same")
        return values


class PullActionModel(BaseModel):
    """Data model for parameters of the pull action."""

    url: str

    @validator('url')
    def is_url(cls, v: str):
        if not v.startswith("http"):
            raise ValueError('url should be starting with http')
        return v


class SubField(BaseModel):
    """Data model for a subfield of a complicated property in the relation databag."""
    subkey: str

class PeerRelationModel(RelationDataModel):
    """Data model for the relation databag."""
    my_key: float
    complex_property: List[SubField]
