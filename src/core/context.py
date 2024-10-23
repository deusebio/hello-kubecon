import logging
from typing import Literal, Optional

from ops.model import Model, Relation
from pydantic import ValidationError

from charms.traefik_k8s.v1.ingress import (
    ProviderApplicationData, ProviderIngressData
)
from core.domain import PeerRelationAppData
from charms.data_platform_libs.v0.data_interfaces import DatabaseRequirerData
from common.data_interfaces import DatabaseConnectionInfo

logger = logging.getLogger(__name__)

CLUSTER = "cluster"
INGRESS = "ingress"
DATABASE = "database"


class Context:

    def __init__(self, model: Model, is_leader: bool):
        self.model = model
        self.is_leader = is_leader

        self.db_requirer = DatabaseRequirerData(
            self.model, relation_name=DATABASE,
            database_name="dummy"
        )

    @property
    def cluster_relation(self) -> Optional[Relation]:
        """The S3 relation."""
        return self.model.get_relation(CLUSTER)

    @property
    def database_relation(self) -> Optional[Relation]:
        """The S3 relation."""
        return self.model.get_relation(DATABASE)

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

    @property
    def database(self) -> DatabaseConnectionInfo | None:
        """The state of metastore DB connection."""
        if relation := self.database_relation:
            try:
                return DatabaseConnectionInfo.read(
                    self.db_requirer.as_dict(relation.id)
                )
            except ValidationError as e:
                logger.debug(f"Cluster relation validation failed: {e}")
        return None
