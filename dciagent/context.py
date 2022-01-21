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

import contextlib
import os


@contextlib.contextmanager
def env(**new):
    # take a snapshot of the variables affected by the new context
    orig = {key: os.getenv(key) for key in new}

    # patch with the environment with the new values
    os.environ.update(new)

    try:
        yield
    finally:
        # restore previous environment
        for key, value in orig.items():
            if value is None:
                del os.environ[key]  # delete if it wasn't present
            else:
                os.environ[key] = value  # or update to original value if it was
