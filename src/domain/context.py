import logging
from typing import Literal, Optional

from ops.model import Model, Relation
from pydantic import ValidationError

from charms.traefik_k8s.v1.ingress import (
    ProviderApplicationData, ProviderIngressData
)
from domain.config import PeerRelationAppData

logger = logging.getLogger(__name__)

CLUSTER = "cluster"
INGRESS = "ingress"


class Context:

    def __init__(self, model: Model, is_leader: bool):
        self.model = model
        self.is_leader = is_leader

    @property
    def cluster_relation(self) -> Optional[Relation]:
        """The S3 relation."""
        return self.model.get_relation(CLUSTER)

    @property
    def cluster(self) -> Optional[PeerRelationAppData]:
        if relation := self.cluster_relation:
            try:
                relation_content = relation.data[relation.app]
                data = PeerRelationAppData.read(relation_content)
                if self.is_leader:
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
        if relation := self.ingress_relation:
            try:
                out = ProviderApplicationData.read(
                    relation.data[relation.app]
                )
                return out.ingress
            except ValidationError as e:
                logger.debug(f"Cluster relation validation failed: {e}")

