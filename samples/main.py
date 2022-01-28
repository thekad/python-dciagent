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
A DCI ansible control command for the OpenShift agent
"""

import sys

import dciagent.core.agent.dci as dci


class Agent(dci.Agent):
    "dci-openshift-agent-ctl"

    default_playbook = "/usr/share/dci-openshift-agent/dci-openshift-agent.yml"
    default_config_dir = "/etc/dci-openshift-agent"
    default_ansible_config = "/usr/share/dci-openshift-agent/ansible.cfg"
    default_inventory = "hosts"

    def __init__(self, **kwargs):
        super().__init__(self.__doc__, __doc__, "0.1", **kwargs)


def main():
    agent = Agent()
    return agent.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
