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

"""
Module defining base agents
"""

import os.path
import subprocess

import dciagent.errors as errors
import dciagent.context as ctx
import dciagent.printer as printer


class Base(object):
    verbosity = 0
    dry_run = False
    skip_validation = False
    command_line = []

    def __init__(self, **kwargs):
        self.verbosity = kwargs.get("verbosity", False)
        self.dry_run = kwargs.get("dry_run", False)
        self.skip_validation = kwargs.get("skip_validation", False)

    @classmethod
    def _setup_subparser(cls, subparser):
        "Sets common argument parser options"
        pass

    def _build_command(self):
        """
        This method should build the command_line list that will be the final
        command to be run
        """

        raise NotImplementedError("Define the _build_command() method in your agent")

    def _build_env(self):
        pass

    def _validate(self):
        pass

    def set_up(self):
        pass

    def tear_down(self):
        pass

    def run(self):
        "Validates the data and executes the playbook"

        if not self.skip_validation:
            self._validate()

        self.set_up()
        self._build_command()
        self._build_env()

        if self.verbosity > 0:
            if len(self.environment) > 0:
                printer.header("Running with the following extra environment:")
                for k, v in self.environment.items():
                    val = v
                    if 'password' in k.lower() or 'secret' in k.lower():
                        val = "<redacted>"
                    print("{}={}".format(k, val))

        rc = 0
        try:
            if self.dry_run:
                printer.header("Dry-run mode, should execute the command:")
                print(" ".join(self.command_line))
            else:
                if len(self.command_line) > 0:
                    with ctx.env(**self.environment):
                        p = subprocess.Popen(self.command_line)
                        p.communicate()
                        rc = p.returncode
        finally:
            self.tear_down()

        return rc


class Ansible(Base):
    playbook = None
    executable = "/usr/bin/ansible-playbook"
    environment = {}
    default_ansible_cfg = "/etc/ansible/ansible.cfg"
    limit = None
    tags = None
    skip_tags = None
    extra_args = None

    @classmethod
    def _setup_subparser(cls, subparser):
        subparser.add_argument(
            "--cfg",
            help="override path to ansible.cfg. (env: $DCI_ANSIBLE_CFG)",
            default=os.getenv("DCI_ANSIBLE_CFG"),
        )
        subparser.add_argument(
            "--limit",
            help="limit ansible run to the given subset. (env: $DCI_ANSIBLE_LIMIT)",
            default=os.getenv("DCI_ANSIBLE_LIMIT"),
        )
        subparser.add_argument(
            "--tags",
            help="ansible tags to execute . (env: $DCI_ANSIBLE_TAGS)",
            default=os.getenv("DCI_ANSIBLE_TAGS"),
        )
        subparser.add_argument(
            "--skip-tags",
            help="ansible tags to skip. (env: $DCI_ANSIBLE_SKIP_TAGS)",
            default=os.getenv("DCI_ANSIBLE_SKIP_TAGS"),
        )
        subparser.add_argument(
            "--extra-args",
            help="extra arguments passed on to the ansible playbook. "
            "(env: $DCI_ANSIBLE_EXTRA_ARGS)",
            default=os.getenv("DCI_ANSIBLE_EXTRA_ARGS"),
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.playbook = kwargs.get("playbook")
        if self.playbook is None:
            self.playbook = os.path.realpath(self.default_playbook)

        self.ansible_cfg = kwargs.get("ansible_cfg")
        if self.ansible_cfg is None:
            if "default_ansible_cfg" in dir(self):
                self.ansible_cfg = os.path.realpath(self.default_ansible_cfg)
        else:
            self.ansible_cfg = os.path.realpath(self.ansible_cfg)

        self.limit = kwargs.get("limit")
        self.tags = kwargs.get("tags")
        self.skip_tags = kwargs.get("skip_tags")
        self.extra_args = kwargs.get("extra_args")


class DCIAnsible(Ansible):
    prefix = ""
    inventory = None
    settings = None
    config_dir = None
    default_auth_file = "dcirc.sh"
    default_inventory = "hosts"
    default_settings = "settings.yml"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.prefix = kwargs.get("prefix", "")

        self.playbook = kwargs.get("playbook")
        if self.playbook is None:
            self.playbook = os.path.realpath(self.default_playbook)

        self.config_dir = kwargs.get("config_dir")
        if self.config_dir is None:
            self.config_dir = os.path.realpath(self.default_config_dir)

        self.auth_file = kwargs.get("auth_file")
        if self.auth_file is None:
            if "default_auth_file" in dir(self):
                self.auth_file = os.path.realpath(
                    os.path.join(
                        self.config_dir,
                        "{}{}".format(self.prefix, self.default_auth_file),
                    )
                )
        else:
            self.auth_file = os.path.realpath(self.auth_file)

        self.settings = kwargs.get("settings")
        if self.settings is None:
            if "default_settings" in dir(self):
                self.settings = os.path.realpath(
                    os.path.join(
                        self.config_dir,
                        "{}{}".format(self.prefix, self.default_settings),
                    )
                )
        else:
            self.settings = os.path.realpath(self.settings)

        self.inventory = kwargs.get("inventory")
        if self.inventory is None:
            if "default_inventory" in dir(self):
                self.inventory = os.path.realpath(
                    os.path.join(
                        self.config_dir,
                        "{}{}".format(self.prefix, self.default_inventory),
                    )
                )
        else:
            self.inventory = os.path.realpath(self.inventory)

        self.hooks_dir = kwargs.get("hooks_dir")
        if self.hooks_dir is not None:
            self.hooks_dir = os.path.realpath(self.hooks_dir)

    def _validate(self):
        "Validates the playbook arguments"

        # if the command is executed on the host, use full paths and ensure the
        # paths exist
        if not os.path.isfile(self.playbook):
            raise errors.ValidationError(
                "Playbook {} does not exist".format(self.playbook)
            )

        if self.settings is not None:
            if not os.path.isfile(self.settings):
                raise errors.ValidationError(
                    "Settings file {} does not exist".format(self.settings)
                )

        if self.inventory is not None:
            if not os.path.isfile(self.inventory):
                raise errors.ValidationError(
                    "Inventory file {} does not exist".format(self.inventory)
                )

        if self.config_dir is not None:
            if not os.path.isdir(self.config_dir):
                raise errors.ValidationError(
                    "Configuration directory {} does not exist".format(self.config_dir)
                )

    def _read_credentials(self):
        """
        Reads the dcirc.sh file and returns a dictionary with the variables and
        values
        """

        # read into a clean (or as close as possible) environment
        pipe = subprocess.Popen(
            ". {}; env".format(self.auth_file),
            stdout=subprocess.PIPE,
            shell=True,
            env={},
            universal_newlines=True,
        )
        data = pipe.communicate()[0]
        env = {}
        for line in data.splitlines():
            if line.startswith("DCI"):
                k, v = line.split("=")
                env[k] = v

        return env
