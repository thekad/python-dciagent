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

import argparse
import os
import shutil
import subprocess

import dciagent.core.context as ctx
import dciagent.core.errors as errors
import dciagent.core.printer as printer


class Argument:
    """
    An abstraction to define arguments at the class level
    """

    def __init__(
        self,
        help,
        short=None,
        long=None,
        action=None,
        default=None,
        env=None,
        type=None,
        nargs=None,
        dest=None,
        metavar=None,
    ):
        if nargs is None and short is None and long is None:
            raise errors.ArgumentError(
                "Need to define one of short or long argument forms"
            )

        self.help = help
        self.short = short
        self.long = long
        self.action = action
        self.default = default
        self.env = env.upper() if env else None
        self.type = type
        self.nargs = nargs
        self.dest = dest
        self.metavar = metavar

    def arg(self):
        args = []
        if self.short is not None:
            args.append(self.short)
        if self.long is not None:
            args.append(self.long)

        help_str = "{}".format(self.help)
        if self.env is not None or self.default is not None:
            help_str += " ("
            if self.env is not None:
                help_str += " env: ${}".format(self.env)
            if self.default is not None:
                help_str += " default: {}".format(self.default)
            help_str += " )"

        kwargs = {
            "help": help_str,
            "action": self.action,
            "dest": self.dest,
        }

        if self.env is not None:
            kwargs["default"] = os.getenv(self.env, self.default)
        else:
            kwargs["default"] = self.default

        if self.type is not None:
            kwargs["type"] = self.type

        if self.nargs is not None:
            kwargs["nargs"] = self.nargs

        if self.metavar is not None:
            kwargs["metavar"] = self.metavar

        return (args, kwargs)


class Base(object):
    executable = None
    verbosity = Argument(
        "increase the verbosity",
        short="-v",
        long="--verbosity",
        default=0,
        action="count",
        env="VERBOSITY",
    )
    dry_run = Argument(
        "do not run the command line, only print it",
        long="--dry-run",
        action="store_true",
        default=False,
        env="DRY_RUN",
    )
    no_validation = Argument(
        "UNSAFE: skip various validations e.g. full path, file checks, etc",
        long="--no-validation",
        action="store_true",
        default=False,
        env="NO_VALIDATION",
    )
    command_line = []
    ap = None

    def __init__(self, prog, description, version):
        self.ap = argparse.ArgumentParser(
            prog=prog,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self.ap.add_argument(
            "-V", "--version", action="version", version="{} {}".format(prog, version)
        )

    def _build_command(self):
        """
        This method should build the command_line list that will be the final
        command to be run
        """

        raise NotImplementedError("Define the _build_command() method in your agent")

    def _cli(self, argv):
        for m in sorted(dir(self)):
            e = getattr(self, m)
            if isinstance(e, Argument):
                args, kwargs = e.arg()
                self.ap.add_argument(*args, **kwargs)

        return self.ap.parse_args(argv)

    def _load_args(self, args):
        for k, v in args.items():
            e = getattr(self, k)
            if isinstance(e, Argument):
                setattr(self, k, v)

    def _build_env(self):
        pass

    def _normalize(self):
        if self.executable is not None:
            self.executable = shutil.which(self.executable)

    def _validate(self):
        if self.executable is None:
            raise (errors.ValidationError("The defined executable does not exist"))

    def _pre(self):
        pass

    def _post(self):
        pass

    def run(self, argv):
        "Validates the data and executes the playbook"

        args = self._cli(argv)
        self._load_args(vars(args))
        self._normalize()

        if not self.no_validation:
            self._validate()

        self._pre()
        self._build_command()
        self._build_env()

        if self.verbosity > 0:
            if len(self.environment) > 0:
                with printer.section("Running with the following extra environment:"):
                    for k, v in self.environment.items():
                        val = v
                        if "password" in k.lower() or "secret" in k.lower():
                            val = "<redacted>"
                        print("{}={}".format(k, val))

        rc = 0
        try:
            if self.dry_run:
                with printer.section("Dry-run mode, should execute the command:"):
                    print(" \\\n".join(self.command_line))
            else:
                if len(self.command_line) > 0:
                    with ctx.env(**self.environment):
                        p = subprocess.Popen(self.command_line)
                        p.communicate()
                        rc = p.returncode
        finally:
            self._post()

        return rc
