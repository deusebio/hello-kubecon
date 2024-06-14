#!/usr/bin/env python3
# Copyright 2021 Jon Seager
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging
import random
import urllib
from typing import Optional, Union

from charms.traefik_k8s.v1.ingress import IngressPerAppRequirer
from ops.main import main
from ops.charm import ActionEvent, RelationEvent, RelationCreatedEvent
from ops.model import ActiveStatus, MaintenanceStatus, WaitingStatus
from pydantic import ValidationError


from charms.core.classes import TypeSafeCharmBase
from charms.core.classes import validate_params
from charms.core.relations import parse_relation_data
from domain.config import HelloKubeconConfig, PullActionModel, PeerRelationAppData, SubField
from domain.context import Context

logger = logging.getLogger(__name__)

class HelloKubeconCharm(TypeSafeCharmBase[HelloKubeconConfig]):
    """Charm the service."""

    config_type = HelloKubeconConfig

    def __init__(self, *args):
        super().__init__(*args)

        self.context = Context(self.model, self.unit.is_leader())

        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.gosherve_pebble_ready, self._on_config_changed)
        self.framework.observe(self.on.pull_site_action, self._pull_site_action)

        self.framework.observe(self.on.update_status, self._update_status)

        self.framework.observe(self.on.cluster_relation_created,
                               self._on_cluster_relation_created)
        self.framework.observe(self.on.cluster_relation_changed,
                               self._on_cluster_relation_changed)

        self.ingress = IngressPerAppRequirer(
            self,
            port=8080,
            host=f"{self.app.name}-endpoints.{self.model.name}.svc.cluster.local",
            strip_prefix=True
        )

    def _on_install(self, _):
        # Download the site
        self._fetch_site("https://jnsgr.uk/demo-site")

    def _on_config_changed(self, event):
        """Handle the config-changed event"""
        # Get the gosherve container so we can configure/manipulate it
        container = self.unit.get_container("gosherve")
        # Create a new config layer
        layer = self._gosherve_layer()

        if container.can_connect():
            # Get the current config
            services = container.get_plan().to_dict().get("services", {})
            # Check if there are any changes to services
            if services != layer["services"]:
                # Changes were made, add the new layer
                container.add_layer("gosherve", layer, combine=True)
                logging.info("Added updated layer 'gosherve' to Pebble plan")
                # Restart it and report a new status to Juju
                container.restart("gosherve")
                logging.info("Restarted gosherve service")
            # All is well, set an ActiveStatus
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("waiting for Pebble in workload container")

    def _gosherve_layer(self):
        """Returns a Pebble configration layer for Gosherve"""
        return {
            "summary": "gosherve layer",
            "description": "pebble config layer for gosherve",
            "services": {
                "gosherve": {
                    "override": "replace",
                    "summary": "gosherve",
                    "command": "/gosherve",
                    "startup": "enabled",
                    "environment": {
                        "REDIRECT_MAP_URL": self.config.redirect_map,
                        "WEBROOT": "/srv",
                    },
                }
            },
        }

    def _fetch_site(self, site_src: str):
        """Fetch latest copy of website from Github and move into webroot"""
        # Set the site URL
        # site_src = "https://jnsgr.uk/demo-site"
        # Set some status and do some logging
        self.unit.status = MaintenanceStatus("Fetching web site")
        logger.info("Downloading site from %s", site_src)
        # Download the site
        urllib.request.urlretrieve(site_src, "/srv/index.html")
        # Set the unit status back to Active
        self.unit.status = ActiveStatus()

    @validate_params(PullActionModel)
    def _pull_site_action(self, event: ActionEvent, params: Optional[Union[PullActionModel, ValidationError]] = None):
        """Action handler that pulls the latest site archive and unpacks it"""
        if isinstance(params, ValidationError):
            event.fail("input params did not pass validation")
            logger.error(params)
            return

        logger.info(f"My URL is: {params.url}")
        self._fetch_site(params.url)
        event.set_results({"result": "site pulled"})

    def _on_cluster_relation_created(self, event: RelationCreatedEvent):
        if self.unit.is_leader():
            logger.info(f"Writing data to the databag")

            PeerRelationAppData(
                my_key=42,
                complex_property=[SubField(subkey="enrico")]
            ).bind(event.relation.data[event.app])

    @parse_relation_data(app_model=PeerRelationAppData)
    def _on_cluster_relation_changed(
            self, event: RelationEvent,
            app_data: Optional[
                Union[PeerRelationAppData, ValidationError]] = None,
            unit_data: Optional[
                Union[PeerRelationAppData, ValidationError]] = None
    ) -> None:
        """Adds the peer unit in an awesome way
        Args:
            event: The triggering relation joined/changed event.
        """
        if isinstance(app_data, ValidationError):
            logger.info(f"Could not parse app data because of {app_data}")

        if isinstance(unit_data, ValidationError):
            logger.info(f"Could not parse unit data because of {unit_data}")

        logger.info(f"The app data model is {app_data}")

    def _update_status(self, _: RelationEvent):
        if self.unit.is_leader():
            self.context.cluster.my_key = round(random.random()*100, 2)

        logger.info(f"My ingress is: {self.context.ingress.url}")

if __name__ == "__main__":
    main(HelloKubeconCharm)
