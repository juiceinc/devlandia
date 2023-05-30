import subprocess
import sys
from subprocess import CalledProcessError
from .format import echo_warning

__all__ = ['CalledProcessError', 'check_call', 'check_output', 'popen']

try:
    import win32api
except:
    win32api = None


def check_call(args, env=None):
    if win32api is not None:
        args[0] = win32api.FindExecutable(args[0])[1]
    try:
        subprocess.check_call(args, env=env)
    except subprocess.CalledProcessError as e:
        echo_warning(f"Error:\n      {e}\n")
        sys.exit(1)


def check_output(args, env=None):
    if win32api is not None:
        args[0] = win32api.FindExecutable(args[0])[1]
    return subprocess.check_output(args, env=env)


def popen(args, env=None):
    if win32api is not None:
        args[0] = win32api.FindExecutable(args[0])[1]
    return subprocess.Popen(args, env=env, shell=True)
