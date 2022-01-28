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
import shutil
import subprocess
import tempfile

import dciagent.core.agent as agent
import dciagent.core.printer as printer
import dciagent.core.agent.ansible


class Agent(dciagent.core.agent.ansible.Agent):
    default_auth_file = "dcirc.sh"
    default_inventory = "hosts"
    default_settings_file = "settings.yml"
    default_config_dir = None
    prefix = agent.Argument(
        "prefix all auto-discovered settings with this string",
        "-P",
        "--prefix",
        default="",
        env="DCI_PREFIX",
    )
    config_dir = agent.Argument(
        "override DCI agent configuration directory",
        short="-C",
        long="--config-dir",
        env="DCI_CONFIG_DIR",
    )
    auth_file = agent.Argument(
        "override DCI agent authentication file i.e. dcirc.sh",
        short="-A",
        long="--auth-file",
        env="DCI_AUTH_FILE",
    )
    settings_file = agent.Argument(
        "override DCI agent settings file i.e. settings.yml",
        short="-S",
        long="--settings-file",
        env="DCI_SETTINGS_FILE",
    )
    no_cleanup = agent.Argument(
        "do not remove temporary directory",
        long="--no-cleanup",
        action="store_true",
        default=False,
        env="DCI_NO_CLEANUP",
    )

    def __init__(self, prog, desc, version):
        super().__init__(prog, desc, version)
        self.tempdir = tempfile.mkdtemp(prefix="dci-")

    def _normalize(self):

        if self.config_dir is None:
            if self.default_config_dir is not None:
                self.config_dir = self.default_config_dir

        if self.auth_file is None:
            if self.default_auth_file is not None:
                self.auth_file = os.path.join(
                    self.config_dir, "{}{}".format(self.prefix, self.default_auth_file)
                )

        if self.ansible_inventory is None:
            if self.default_inventory is not None:
                self.ansible_inventory = os.path.join(
                    self.config_dir,
                    "{}{}".format(self.prefix, self.default_inventory),
                )

        if self.settings_file is None:
            if self.default_settings_file is not None:
                self.settings_file = os.path.join(
                    self.config_dir,
                    "{}{}".format(self.prefix, self.default_settings_file),
                )

        if self.ansible_extra_vars is None:
            self.ansible_extra_vars = []

        self.ansible_extra_vars.append(
            "JOB_ID_FILE={}".format(os.path.join(self.tempdir, "dci.job"))
        )
        if self.settings_file is not None:
            self.ansible_extra_vars.append("@{}".format(self.settings_file))

        # we run the super() normalize after because we have to munge the
        # values according to the given prefix
        super()._normalize()

    def _build_env(self):
        super()._build_env()
        creds = self._read_credentials()
        self.environment.update(creds)
        self.environment.update(
            {
                "ANSIBLE_LOG_PATH": os.path.join(self.tempdir, "ansible.log"),
                "JUNIT_OUTPUT_DIR": self.tempdir,
                "JUNIT_TEST_CASE_PREFIX": "test_",
                "JUNIT_TASK_CLASS": "yes",
            }
        )

    def _post(self):
        if self.no_cleanup:
            printer.header(
                "Skipping removal of temp directory: {}".format(self.tempdir)
            )
        else:
            shutil.rmtree(self.tempdir)

    def _read_credentials(self):
        """
        Reads the dcirc.sh file and returns a dictionary with the variables and
        values
        """

        pipe = subprocess.Popen(
            ". {}; env".format(self.auth_file),
            stdout=subprocess.PIPE,
            shell=True,
            env={},  # start with a clean environment
            universal_newlines=True,
        )
        data = pipe.communicate()[0]
        env = {}
        for line in data.splitlines():
            if line.startswith("DCI_"):
                k, v = line.split("=")
                env[k] = v

        return env
