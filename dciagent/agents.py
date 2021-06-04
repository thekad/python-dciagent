#
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
Module defining all agents
"""

import os.path
import subprocess

import ansible_runner


class BaseAgent(object):
    debug = False

    def __init__(self, debug):
        self.debug = debug

    def run(self, *args, **kwargs):
        raise NotImplementedError("This agent hasn't been implemented yet")


class AnsibleAgent(BaseAgent):
    playbook = None
    inventory = None
    settings = None

    def __init__(self, config, playbook):
        BaseAgent.__init__(self, config["debug"])
        self.playbook = os.path.abspath(playbook)

        # auto-discover configuration files
        prefix = ""
        if config["prefix"] is not None:
            prefix = config["prefix"]

        if config["config_dir"] is None:
            config_dir = self.default_config_dir
        else:
            config_dir = config["config_dir"]

        if config["settings"] is not None:
            self.settings = config["settings"]
        else:
            self.settings = os.path.join(
                config_dir, "{}{}".format(prefix, "settings.yml")
            )

        if config["inventory"] is not None:
            self.inventory = config["inventory"]
        else:
            self.inventory = os.path.join(config_dir, "{}{}".format(prefix, "hosts"))

    def validate(self):
        if not os.path.isfile(self.playbook):
            raise (
                IOError("Ansible playbook file {} doesn't exist".format(self.playbook))
            )
        if not os.path.isfile(self.settings):
            raise (
                IOError("Ansible settings file {} doesn't exist".format(self.settings))
            )
        if not os.path.isfile(self.inventory):
            raise (
                IOError(
                    "Ansible inventory file {} doesn't exist".format(self.inventory)
                )
            )

    def get_runner_config(self):
        runner_config = ansible_runner.RunnerConfig(
            private_data_dir="/tmp",
            playbook=self.playbook,
            inventory=self.inventory,
            verbosity=3 if self.debug else 1,
            # cmdline="-e @{}".format(self.settings),
        )
        runner_config.prepare()
        return runner_config

    def run(self):
        runner_config = self.get_runner_config()
        cmd = runner_config.generate_ansible_command()
        print("Running ansible command: {}".format(" ".join(cmd)))
        r = ansible_runner.Runner(config=runner_config)
        r.run()


class OCPAgent(AnsibleAgent):
    default_config_dir = "/etc/dci-openshift-agent"

    def __init__(self, *args, **kwargs):
        AnsibleAgent.__init__(self, *args, **kwargs)


class PodmanAgent(AnsibleAgent):
    image = "quay.io/thekad/alpine-ansible:3"
    playbook_dir = None

    def __init__(self, config, playbook, image, extra_ansible_opts, extra_podman_opts):
        self.playbook_dir = os.path.dirname(os.path.abspath(playbook))
        AnsibleAgent.__init__(self, config, playbook)
        self.playbook = os.path.basename(playbook)
        if image is not None:
            self.image = image

    def run(self):
        args = [
            "podman",
            "run",
            "--rm",
            "-it",
            "--volume",
            "{}:/playbooks:z".format(self.playbook_dir),
            self.image,
        ]
        runner_config = self.get_runner_config()
        args.extend(runner_config.generate_ansible_command())
        print(" ".join(args))
        subprocess.run(args)


class RHELAgent(PodmanAgent):
    default_config_dir = "/etc/dci-rhel-agent"

    def __init__(self, *args, **kwargs):
        PodmanAgent.__init__(self, *args, **kwargs)
