# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Add things to old Pythons so I can pretend they are newer."""

# This file's purpose is to provide modules to be imported from here.
# pylint: disable=unused-import

import os
import sys

try:
    os.PathLike
except AttributeError:
    # This is Python 2 and 3
    path_types = (bytes, str)
else:
    # 3.6+
    path_types = (bytes, str, os.PathLike)
