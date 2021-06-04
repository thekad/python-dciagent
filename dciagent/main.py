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
Command line interface for the DCI agents
"""

import click

import dciagent
import dciagent.agents


@click.group(invoke_without_command=True)
@click.option(
    "-C",
    "--config-dir",
    metavar="PATH",
    envvar="DCI_CONFIG_DIR",
    help="Path to the configuration directory, default is different per agent.",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "-P",
    "--prefix",
    metavar="STRING",
    envvar="DCI_PREFIX",
    help="String to prepend to all config files to be loaded.",
)
@click.option(
    "-S",
    "--settings",
    metavar="FILE",
    envvar="DCI_SETTINGS",
    help="Path to settings file, overrides config-dir/prefix auto-discovery.",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    "-I",
    "--inventory",
    metavar="FILE",
    envvar="DCI_INVENTORY",
    help="Ansible inventory file, overrides config-dir/prefix auto-discovery.",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option("-D", "--debug", is_flag=True, help="Enable debugging output.")
@click.option("-V", "--version", is_flag=True, help="Print program version.")
@click.pass_context
def cli(ctx, config_dir, prefix, settings, inventory, debug, version):
    """Root agent control script"""

    if version:
        click.echo(dciagent.__version__)
        return
    ctx.ensure_object(dict)
    ctx.obj["config_dir"] = config_dir
    ctx.obj["prefix"] = prefix
    ctx.obj["settings"] = settings
    ctx.obj["inventory"] = inventory
    ctx.obj["debug"] = debug


@cli.command()
@click.option(
    "-i",
    "--image",
    envvar="DCI_CONTAINER_IMAGE",
    default="quay.io/thekad/alpine-ansible:3",
    help="Container image used to run the agent.",
)
@click.argument(
    "playbook",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    "-xa",
    "--extra-ansible-opts",
    envvar="DCI_EXTRA_ANSIBLE_OPTS",
    help="Extra options passed to ansible.",
)
@click.option(
    "-xp",
    "--extra-podman-opts",
    envvar="DCI_EXTRA_PODMAN_OPTS",
    help="Extra options passed to podman.",
)
@click.pass_context
def rhel(ctx, image, playbook, extra_ansible_opts, extra_podman_opts):
    "Red Hat Enterprise Linux Containerized Agent"

    a = dciagent.agents.RHELAgent(
        ctx.obj, playbook, image, extra_ansible_opts, extra_podman_opts
    )
    # a.validate()
    a.run()


@cli.command()
@click.option(
    "-xa",
    "--extra-ansible-opts",
    envvar="DCI_EXTRA_ANSIBLE_OPTS",
    help="Extra options passed to ansible.",
)
@click.argument(
    "playbook",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.pass_context
def ocp(ctx, playbook, extra_ansible_opts):
    "OpenShift Ansible Agent"

    ctx.obj["extra_ansible_opts"] = extra_ansible_opts
    a = dciagent.agents.OCPAgent(ctx.obj, playbook)
    # a.validate()
    a.run()


if __name__ == "__main__":
    cli(obj={})
