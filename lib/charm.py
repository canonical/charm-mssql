#!/usr/bin/env python3

import os
import base64
import pickle

from op.charm import CharmBase, CharmEvents
from op.framework import Event, EventBase, StoredState
from op.model import ActiveStatus, BlockedStatus
from op.main import main

import logging
import subprocess
import yaml

logger = logging.getLogger()


class MSSQLReadyEvent(EventBase):
    pass


class MSSQLCharmEvents(CharmEvents):
    mssql_ready = Event(MSSQLReadyEvent)


class Charm(CharmBase):
    on = MSSQLCharmEvents()
    state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        # TODO: install hook will only be relevant as soon as LP: #1854635 will be fixed.
        self.framework.observe(self.on.install, self)
        self.framework.observe(self.on.start, self)
        self.framework.observe(self.on.stop, self)
        self.framework.observe(self.on.config_changed, self)
        self.framework.observe(self.on.db_relation_joined, self)
        self.framework.observe(self.on.db_relation_changed, self)
        self.framework.observe(self.on.mssql_ready, self)

    def on_install(self, event):
        #self._state['on_install'].append(type(event))
        #self._state['observed_event_types'].append(type(event))
        #self._write_state()
        log('Ran on_install hook')

    def on_start(self, event):
        log('Ran on_start hook')
        new_pod_spec = self.make_pod_spec()
        self.state.spec = new_pod_spec
        self._apply_spec(new_pod_spec)

    def on_stop(self, event):
        log('Ran on_stop')

    def on_config_changed(self, event):
        log('Ran on_config_changed hook')
        new_spec = self.make_pod_spec()
        if self.state.spec != new_spec:
            self._apply_spec(new_spec)
        self.framework.model.unit.status = ActiveStatus()

    def _apply_spec(self, spec):
        self.framework.model.pod.set_spec(spec)
        self.state.spec = spec

    def on_mssql_ready(self, event):
        pass

    def on_db_relation_joined(self, event):
        self._state['on_db_relation_joined'].append(type(event))
        self._state['observed_event_types'].append(type(event))
        self._state['db_relation_joined_data'] = event.snapshot()
        self._write_state()

    def on_db_relation_changed(self, event):
        if not self.state.ready:
            event.defer()
            return

    def make_pod_spec(self):
        config = self.framework.model.config
        container_config= self.sanitized_container_config()
        if container_config is None:
            return  # status already set
        ports = [{"name": "mssql", "containerPort": 1443, "protocol": "TCP"}]
        spec = {
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {
                        'apiGroups': ['apps'],
                        'resources': ['statefulsets', 'deployments'],
                        'verbs': ['*'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['pods', 'pods/exec'],
                        'verbs': ['create', 'get', 'list', 'watch', 'update',
                                  'patch'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['configmaps'],
                        'verbs': ['get', 'watch', 'list'],
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['persistentvolumeclaims'],
                        'verbs': ['create', 'delete'],
                    },
                ],
            },
            "containers": [
                {
                    "name": self.framework.model.app.name,
                    "image": config["image"],
                    "ports": ports,
                    "config": container_config,
                }
            ],
            # "restartPolicy": 'Always',
            # "terminationGracePeriodSeconds": 10,
        }
        config_with_secrets = self.full_container_config()
        if config_with_secrets is None:
            return None
        container_config.update(config_with_secrets)
        return spec

    def sanitized_container_config(self):
        """Uninterpolated container config without secrets"""
        config = self.framework.model.config
        if config["container_config"].strip() == "":
            container_config = {}
        else:
            container_config = \
                yaml.safe_load(self.framework.model.config["container_config"])
            if not isinstance(container_config, dict):
                self.framework.model.unit.status = \
                    BlockedStatus("container_config is not a YAML mapping")
                return None
        return container_config

    def full_container_config(self):
        """Uninterpolated container config with secrets"""
        config = self.framework.model.config
        container_config = self.sanitized_container_config()
        if container_config is None:
            return None
        if config["container_secrets"].strip() == "":
            container_secrets = {}
        else:
            container_secrets = yaml.safe_load(config["container_secrets"])
            if not isinstance(container_secrets, dict):
                self.framework.model.unit.status = \
                    BlockedStatus("container_secrets is not a YAML mapping")
                return None
        container_config.update(container_secrets)
        return container_config


def log(message, level=None):
    """Write a message to the juju log"""
    command = ['juju-log']
    if level:
        command += ['-l', level]
    if not isinstance(message, str):
        message = repr(message)

    # https://elixir.bootlin.com/linux/latest/source/include/uapi/linux/binfmts.h
    # PAGE_SIZE * 32 = 4096 * 32
    MAX_ARG_STRLEN = 131072
    command += [message[:MAX_ARG_STRLEN]]
    # Missing juju-log should not cause failures in unit tests
    # Send log output to stderr
    subprocess.call(command)


if __name__ == '__main__':
    main(Charm)
