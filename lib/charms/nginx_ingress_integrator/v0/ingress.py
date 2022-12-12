"""Library for the ingress relation.

This library contains the Requires and Provides classes for handling
the ingress interface.

Import `IngressRequires` in your charm, with two required options:
    - "self" (the charm itself)
    - config_dict

`config_dict` accepts the following keys:
    - service-hostname (required)
    - service-name (required)
    - service-port (required)
    - additional-hostnames
    - limit-rps
    - limit-whitelist
    - max-body-size
    - path-routes
    - retry-errors
    - rewrite-enabled
    - rewrite-target
    - service-namespace
    - session-cookie-max-age
    - tls-secret-name

See [the config section](https://charmhub.io/nginx-ingress-integrator/configure) for descriptions
of each, along with the required type.

As an example, add the following to `src/charm.py`:
```
from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

# In your charm's `__init__` method.
self.ingress = IngressRequires(self, {"service-hostname": self.config["external_hostname"],
                                      "service-name": self.app.name,
                                      "service-port": 80})

# In your charm's `config-changed` handler.
self.ingress.update_config({"service-hostname": self.config["external_hostname"]})
```
And then add the following to `metadata.yaml`:
```
requires:
  ingress:
    interface: ingress
```
You _must_ register the IngressRequires class as part of the `__init__` method
rather than, for instance, a config-changed event handler. This is because
doing so won't get the current relation changed event, because it wasn't
registered to handle the event (because it wasn't created in `__init__` when
the event was fired).
"""
import logging
from typing import Union, Dict, Optional
from pydantic import ValidationError

from ops.charm import CharmEvents, RelationEvent
from ops.framework import EventSource, Object

from charms.core.relations import parse_relation_data, RelationDataModel

# The unique Charmhub library identifier, never change it
LIBID = "db0af4367506491c91663468fb5caa4c"

# Increment this major API version when introducing breaking changes
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 9

logger = logging.getLogger(__name__)

REQUIRED_INGRESS_RELATION_FIELDS = {
    "service-hostname",
    "service-name",
    "service-port",
}

OPTIONAL_INGRESS_RELATION_FIELDS = {
    "additional-hostnames",
    "limit-rps",
    "limit-whitelist",
    "max-body-size",
    "retry-errors",
    "rewrite-target",
    "rewrite-enabled",
    "service-namespace",
    "session-cookie-max-age",
    "tls-secret-name",
    "path-routes",
}


class IngressRelationData(RelationDataModel):
    service_hostname: str
    service_name: str
    service_port: int
    additional_hostnames: Optional[str] = None
    limit_rps: Optional[str] = None
    limit_whitelist: Optional[str] = None
    max_body_size: Optional[str] = None
    retry_errors: Optional[str] = None
    rewrite_target: Optional[str] = None
    rewrite_enabled: Optional[str] = None
    service_namespace: Optional[str] = None
    session_cookie_max_age: Optional[str] = None
    tls_secret_name: Optional[str] = None
    path_routes: Optional[str] = None


class IngressAvailableEvent(RelationEvent):
    pass


class IngressCharmEvents(CharmEvents):
    """Custom charm events."""

    ingress_available = EventSource(IngressAvailableEvent)


class IngressRequires(Object):
    """This class defines the functionality for the 'requires' side of the 'ingress' relation.

    Hook events observed:
        - relation-changed
    """

    def __init__(self, charm, config_dict: Union[Dict, IngressRelationData]):
        super().__init__(charm, "ingress")

        self.framework.observe(charm.on["ingress"].relation_changed, self._on_relation_changed)

        self.config: IngressRelationData = config_dict if isinstance(config_dict, IngressRelationData) \
            else IngressRelationData(**config_dict)

    def _on_relation_changed(self, event):
        """Handle the relation-changed event."""
        # `self.unit` isn't available here, so use `self.model.unit`.
        if self.model.unit.is_leader():
            self.config.write(event.relation.data[self.model.app])

    def update_config(self, config_dict: Union[Dict, IngressRelationData]):
        """Allow for updates to relation."""
        if self.model.unit.is_leader():

            self.config = config_dict if isinstance(config_dict, IngressRelationData) \
                else self.config.copy(update=config_dict)

            relation = self.model.get_relation("ingress")

            if relation:
                self.config.write(relation.data[self.model.app])


class IngressProvides(Object):
    """This class defines the functionality for the 'provides' side of the 'ingress' relation.

    Hook events observed:
        - relation-changed
    """

    def __init__(self, charm):
        super().__init__(charm, "ingress")
        # Observe the relation-changed hook event and bind
        # self.on_relation_changed() to handle the event.
        self.framework.observe(charm.on["ingress"].relation_changed, self._on_relation_changed)
        self.charm = charm

    @parse_relation_data(app_model=IngressRelationData)
    def _on_relation_changed(
            self, event: RelationEvent, params: Optional[Union[IngressRelationData, ValidationError]] = None
    ):
        """Handle a change to the ingress relation.

        Confirm we have the fields we expect to receive."""
        # `self.unit` isn't available here, so use `self.model.unit`.
        if not self.model.unit.is_leader():
            return

        # Create an event that our charm can use to decide it's okay to
        # configure the ingress.
        self.charm.on.ingress_available.emit(event.relation, app=event.app, unit=event.unit)
