from common.core.v2.relations import BaseRelationData
from common.core.v2.serializers import YamlSerializer


class DatabaseConnectionInfo(BaseRelationData):
    """Class representing a information related to a database connection."""
    _backend = YamlSerializer()

    endpoint: str
    username: str
    password: str
    dbname: str
