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
This is the Red Hat Open Shift DCI Agent.
"""

import distutils.util as dutils
import os
import shutil
import tempfile

import dciagent.agents
import dciagent.printer as printer


class Agent(dciagent.agents.DCIAnsible):
    "The DCI OpenShift agent"

    default_playbook = "/usr/share/dci-openshift-agent/dci-openshift-agent.yml"
    default_config_dir = "/etc/dci-openshift-agent"
    default_ansible_cfg = "/usr/share/dci-openshift-agent/ansible.cfg"
    cleanup = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cleanup = not kwargs.get("no_cleanup")

    @classmethod
    def _setup_subparser(cls, subparser):
        super()._setup_subparser(subparser)
        subparser.add_argument(
            "--no-cleanup",
            help="Do not cleanup the temporary directory after run"
            ". (env: $DCI_OCP_NO_CLEANUP)",
            action="store_true",
            default=dutils.strtobool(os.getenv("DCI_OCP_NO_CLEANUP", "false")),
        )

    def _build_env(self):
        self.environment = {
            "ANSIBLE_CONFIG": self.ansible_cfg,
            "ANSIBLE_LOG_PATH": os.path.join(self.tempdir, "ansible.log"),
            "JUNIT_OUTPUT_DIR": self.tempdir,
            "JUNIT_TEST_CASE_PREFIX": "test_",
            "JUNIT_TASK_CLASS": "yes",
        }
        self.environment.update(self._read_credentials())

    def set_up(self):
        self.tempdir = tempfile.mkdtemp(prefix="dci-ocp-")

    def tear_down(self):
        if self.cleanup:
            shutil.rmtree(self.tempdir)
        else:
            printer.header(
                "Skipping removal of temp directory: {}".format(self.tempdir)
            )

    def _build_command(self):
        "Builds the command to be executed"

        self.command_line = [
            self.executable,
            "--inventory",
            self.inventory,
            "--extra-vars",
            "JOB_ID_FILE={}".format(
                os.path.join(self.tempdir, "dci-openshift-agent.job")
            ),
            "--extra-vars",
            "@{}".format(self.settings),
        ]

        if self.limit is not None:
            self.command_line.extend(["--limit", self.limit])

        if self.tags is not None:
            self.command_line.extend(["--tags", self.tags])

        if self.skip_tags is not None:
            self.command_line.extend(["--skip-tags", self.skip_tags])

        if self.verbosity > 0:
            self.command_line.append("-{}".format("v" * self.verbosity))

        # always append playbook at the end
        self.command_line.append(self.playbook)
