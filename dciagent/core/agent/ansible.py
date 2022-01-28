# Copyright (C) 2021 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os.path
import shlex

import dciagent.core.agent as agent
import dciagent.core.errors as errors


class Agent(agent.Base):
    executable = "ansible-playbook"
    default_ansible_config = "/etc/ansible/ansible.cfg"
    default_ansible_inventory = "/etc/ansible/hosts"
    default_playbook = None
    environment = {}
    ansible_config = agent.Argument(
        "override path to ansible.cfg",
        short="-c",
        long="--ansible-config",
        env="ANSIBLE_CONFIG",
    )
    ansible_limit = agent.Argument(
        "limit playbook execution to the given subset",
        short="-l",
        long="--ansible-limit",
        env="ANSIBLE_LIMIT",
    )
    ansible_tags = agent.Argument(
        "only execute the tasks marked with this list of tags",
        short="-t",
        long="--ansible-tags",
        env="ANSIBLE_TAGS",
    )
    ansible_skip_tags = agent.Argument(
        "skip the tasks marked with this list of tags",
        long="--ansible-skip-tags",
        env="ANSIBLE_SKIP_TAGS",
    )
    ansible_args = agent.Argument(
        "any extra arguments to be passed to ansible-playbook 'as is'",
        long="--ansible-args",
        env="ANSIBLE_ARGS",
    )
    ansible_extra_vars = agent.Argument(
        "any extra variables to be passed to the ansible playbook run",
        short="-e",
        long="--ansible-extra-vars",
        env="ANSIBLE_EXTRA_VARS",
        action="append",
    )
    ansible_inventory = agent.Argument(
        "path to the ansible inventory",
        short="-i",
        long="--ansible-inventory",
        env="ANSIBLE_INVENTORY",
    )
    playbook = agent.Argument(
        "path to the ansible playbook(s) to execute",
        nargs="?",
        dest="playbook",
        env="ANSIBLE_PLAYBOOK",
    )

    def __init__(self, prog, desc, version):
        super().__init__(prog, desc, version)

    def _normalize(self):
        super()._normalize()

        # if no playbook given, use default
        if self.playbook is None:
            if self.default_playbook is not None:
                self.playbook = self.default_playbook

        # if no inventory given, use default
        if self.ansible_inventory is None:
            if self.default_ansible_inventory is not None:
                self.ansible_inventory = self.default_ansible_inventory

        # if no config given, use the default
        if self.ansible_config is None:
            if self.default_ansible_config is not None:
                self.ansible_config = self.default_ansible_config

    def _build_env(self):
        cfg = self.ansible_config

        if cfg is not None:
            self.environment = {"ANSIBLE_CONFIG": cfg}

    def _validate(self):
        super()._validate()

        playbook = self.playbook
        if playbook is None:
            raise (errors.ValidationError("Please provide a path to a playbook."))
        if not os.path.isfile(playbook):
            raise (
                errors.ValidationError(
                    "Cannot read ansible playbook {}".format(playbook)
                )
            )

        inventory = self.ansible_inventory
        if not os.path.isfile(inventory):
            raise (
                errors.ValidationError(
                    "Cannot read ansible inventory file {}".format(inventory)
                )
            )

        cfg = self.ansible_config
        if cfg is None:
            raise (
                errors.ValidationError("Please provide a valid path to the ansible.cfg")
            )
        else:
            if not os.path.isfile(cfg):
                raise (
                    errors.ValidationError("Cannot read ansible config {}".format(cfg))
                )

    def _build_command(self):
        self.command_line = [
            self.executable,
            "--inventory",
            self.ansible_inventory,
        ]

        if self.ansible_limit is not None:
            self.command_line.extend(["--limit", shlex.quote(self.ansible_limit)])

        if self.ansible_tags is not None:
            self.command_line.extend(["--tags", shlex.quote(self.ansible_tags)])

        if self.ansible_skip_tags is not None:
            self.command_line.extend(
                ["--skip-tags", shlex.quote(self.ansible_skip_tags)]
            )

        if self.ansible_extra_vars is not None:
            for extra_var in self.ansible_extra_vars:
                self.command_line.extend(["--extra-vars", shlex.quote(extra_var)])

        if self.ansible_args is not None:
            self.command_line.extend(shlex.split(self.ansible_args))

        if self.verbosity > 0:
            verbosity = "-{}".format("v" * self.verbosity)
            self.command_line.append(verbosity)

        self.command_line.append(self.playbook)
