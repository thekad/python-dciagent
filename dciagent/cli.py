#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
Unified command line interface for the DCI agents.

This script acts a single point of entry to execute all possible agents and
other utilities from DCI:

    * dci-rhel-agent
    * dci-openstack-agent
    * dci-openshift-agent
    * dci-openshift-app-agent
    * dci-pipeline

"""

import argparse
import distutils.util as dutils
import importlib
import os
import sys

import dciagent


def main():
    "dci-agent-ctl"

    ap = argparse.ArgumentParser(
        prog=main.__doc__,
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s {}".format(dciagent.__version__),
    )
    ap.add_argument(
        "-C",
        "--config-dir",
        help="override path to configuration directory. (env: $DCI_CONFIG_DIR)",
        default=os.getenv("DCI_CONFIG_DIR"),
    )
    ap.add_argument(
        "-A",
        "--auth-file",
        help="override path to dcirc.rc file. (env: $DCI_AUTH_FILE)",
        default=os.getenv("DCI_AUTH_FILE"),
    )
    ap.add_argument(
        "-P",
        "--playbook",
        help="override path to default agent playbook. (env: $DCI_PLAYBOOK)",
        default=os.getenv("DCI_PLAYBOOK", None),
    )
    ap.add_argument(
        "-R",
        "--prefix",
        help="prepend this string when auto-discovering config files"
        ". (env: $DCI_PREFIX)",
        default=os.getenv("DCI_PREFIX", ""),
    )
    ap.add_argument(
        "-I",
        "--inventory",
        help="override path to inventory file. (env: $DCI_INVENTORY)",
        default=os.getenv("DCI_INVENTORY"),
    )
    ap.add_argument(
        "-H",
        "--hooks-dir",
        help="override path to hooks directory. (env: $DCI_HOOKS_DIR)",
        default=os.getenv("DCI_HOOKS_DIR"),
    )
    ap.add_argument(
        "-V",
        "--verbosity",
        action="count",
        help="specify multiple times to up verbosity. (env: $DCI_VERBOSITY)",
        default=0,
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="only print the commands to be run, don't actually run them"
        ". (env: $DCI_DRY_RUN)",
        default=dutils.strtobool(os.getenv("DCI_DRY_RUN", "false")),
    )
    ap.add_argument(
        "--skip-validation",
        action="store_true",
        help="UNSAFE: do not validate the parameters before calling the playbook"
        ". (env: $DCI_SKIP_VALIDATION)",
        default=dutils.strtobool(os.getenv("DCI_SKIP_VALIDATION", "false")),
    )

    # sub-commands
    sp = ap.add_subparsers(help="Agent to run")
    subs = {}
    for sub in ("dummy", "openshift"):
        m = importlib.import_module("dciagent.agents.{}".format(sub))
        subs[sub] = sp.add_parser(
            sub,
            help=m.Agent.__doc__,  # long help is the module docstring
            description=m.__doc__,  # short usage is the class' docstring
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        m.Agent._setup_subparser(
            subs[sub]
        )  # setup the sub-command extra arguments (if any)
        subs[sub].set_defaults(
            Class=m.Agent
        )  # sets the appropriate routing to the sub-command's class

    # parse arguments and run
    args = ap.parse_args()
    try:
        agent = args.Class(**vars(args))
        sys.exit(agent.run())
    # should trigger when you don't pass a sub-command
    except AttributeError as ae:
        print(ae)
        ap.print_help()


if __name__ == "__main__":
    main()
