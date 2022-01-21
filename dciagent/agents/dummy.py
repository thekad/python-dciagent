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
Just a dummy test agent entrypoint
"""

import dciagent.agents


class Agent(dciagent.agents.Ansible):
    "An example dummy agent"

    default_playbook = "samples/playbook.yml"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _build_env(self):
        self.environment = {"ANSIBLE_CFG": self.ansible_cfg}

    def _build_command(self):
        self.command_line = [
            self.executable,
            self.playbook,
        ]
        if self.verbosity > 0:
            self.command_line.append("-{}".format("v" * self.verbosity))
