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


# imp was deprecated in Python 3.3
try:
    import importlib
    import importlib.util
    imp = None
except ImportError:
    importlib = None

# We only want to use importlib if it has everything we need.
try:
    importlib_util_find_spec = importlib.util.find_spec
except Exception:
    import imp
    importlib_util_find_spec = None

# What is the .pyc magic number for this version of Python?
try:
    PYC_MAGIC_NUMBER = importlib.util.MAGIC_NUMBER
except AttributeError:
    PYC_MAGIC_NUMBER = imp.get_magic()


def invalidate_import_caches():
    """Invalidate any import caches that may or may not exist."""
    if importlib and hasattr(importlib, "invalidate_caches"):
        importlib.invalidate_caches()


def import_local_file(modname, modfile=None):
    """Import a local file as a module.

    Opens a file in the current directory named `modname`.py, imports it
    as `modname`, and returns the module object.  `modfile` is the file to
    import if it isn't in the current directory.

    """
    try:
        from importlib.machinery import SourceFileLoader
    except ImportError:
        SourceFileLoader = None

    if modfile is None:
        modfile = modname + '.py'
    if SourceFileLoader:
        # pylint: disable=no-value-for-parameter, deprecated-method
        mod = SourceFileLoader(modname, modfile).load_module()
    else:
        for suff in imp.get_suffixes():                 # pragma: part covered
            if suff[0] == '.py':
                break

        with open(modfile, 'r') as f:
            # pylint: disable=undefined-loop-variable
            mod = imp.load_module(modname, f, modfile, suff)

    return mod
