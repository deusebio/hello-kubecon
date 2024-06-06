import logging
from typing import Literal, Optional

from ops.model import Model, Relation
from pydantic import ValidationError

from charms.traefik_k8s.v1.ingress import (
    ProviderApplicationData, ProviderIngressData
)
from domain.config import PeerRelationAppData

MODE = Literal["w", "r"]

logger = logging.getLogger(__name__)

CLUSTER = "cluster"
INGRESS = "ingress"


class Context:

    def __init__(self, model: Model):
        self.model = model

    @property
    def cluster_relation(self) -> Optional[Relation]:
        """The S3 relation."""
        return self.model.get_relation(CLUSTER)

    def get_cluster_data(self, mode: MODE = "r") -> Optional[PeerRelationAppData]:
        if relation := self.cluster_relation:
            try:
                relation_content = relation.data[relation.app]
                data = PeerRelationAppData.read(relation_content)
                if mode == "w":
                    data.bind(relation_content)
                return data
            except ValidationError as e:
                logger.debug(f"Cluster relation validation failed: {e}")

    @property
    def ingress_relation(self) -> Optional[Relation]:
        """The S3 relation."""
        return self.model.get_relation(INGRESS)

    @property
    def ingress(self) -> Optional[ProviderIngressData]:
        if relation := self.cluster_relation:
            try:
                return ProviderApplicationData.read(
                    relation.data[relation.app]
                ).ingress
            except ValidationError as e:
                logger.debug(f"Cluster relation validation failed: {e}")

