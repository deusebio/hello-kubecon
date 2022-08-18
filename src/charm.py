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

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus

from charms.logging.v0.classes import WithLogging
from time import sleep

class HelloKubeconCharm(CharmBase, WithLogging):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.gosherve_pebble_ready, self._on_gosherve_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_config_changed(self, event):
        name = self.config["name"]
        self.logger.info(f"The provided config is: {name}")
        self.unit.status = MaintenanceStatus(f"Updating the configuration")
        sleep(5)
        self.logger.info(f"Configuration updated!")
        pass

    def _on_gosherve_pebble_ready(self, event):
        """Define and start a workload using the Pebble API."""
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Define an initial Pebble layer configuration
        pebble_layer = {
            "summary": "gosherve layer",
            "description": "pebble config layer for gosherve",
            "services": {
                "gosherve": {
                    "override": "replace",
                    "summary": "gosherve",
                    "command": "/gosherve",
                    "startup": "enabled",
                    "environment": {
                        "REDIRECT_MAP_URL": "https://jnsgr.uk/demo-routes"
                    },
                }
            },
        }
        # Add intial Pebble config layer using the Pebble API
        container.add_layer("gosherve", pebble_layer, combine=True)
        # Autostart any services that were defined with startup: enabled
        container.autostart()
        # Learn more about statuses in the SDK docs:
        # https://juju.is/docs/sdk/constructs#heading--statuses
        self.logger.info("The Pebble Connection has been made - Enrico")
        self.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(HelloKubeconCharm)
