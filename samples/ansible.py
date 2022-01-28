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

import os
import sys

import dciagent.core.agent.ansible


class Agent(dciagent.core.agent.ansible.Agent):
    "ansible-ctl"

    default_playbook = os.path.join(os.path.dirname(__file__), "playbook.yml")

    def __init__(self, **kwargs):
        super().__init__(self.__doc__, __doc__, "0.1", **kwargs)


def main():
    agent = Agent()
    return agent.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
