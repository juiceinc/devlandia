from __future__ import absolute_import
from __future__ import print_function

import subprocess
from subprocess import CalledProcessError

__all__ = ['CalledProcessError', 'check_call', 'check_output']

try:
    import win32api
except:
    win32api = None

def check_call(args, env=None):
    if win32api is not None:
        args[0] = win32api.FindExecutable(args[0])[1]
    return subprocess.check_call(args, env=env)

def check_output(args, env=None):
    if win32api is not None:
        args[0] = win32api.FindExecutable(args[0])[1]
    return subprocess.check_output(args, env=env)
