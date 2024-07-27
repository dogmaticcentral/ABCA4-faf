_copyright__ = """

    Copyright 2024 Ivana Mihalek

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/
    
    The License is noncommercial - you may not use this material for commercial purposes.

"""
__license__ = "CC BY-NC 4.0"

import logging
import os
import shlex
import subprocess
import sys
from sys import version_info

logger = logging.getLogger(__name__)


def set_env(env_variables, unset_env_vars, env_vars_extend):
    env = None
    if not (env_variables or unset_env_vars or env_vars_extend):  return env
    env = os.environ.copy()  # the inherited environment
    if env_variables:
        for env_var_name, new_value in env_variables.items():
            env[env_var_name] = new_value
    if unset_env_vars:
        for env_var_name in unset_env_vars:
            if env_var_name in env: del env[env_var_name]
    if env_vars_extend:
        for env_var_name, additional_value in env_vars_extend.items():
            if env_var_name in env:
                env[env_var_name] = f"{env[env_var_name]}:{additional_value}"
            else:
                env[env_var_name] = additional_value
    return env


def run_subprocess(cmd_string, env_variables=None, unset_env_vars=None, env_vars_extend=None,
                   noexit=False, stdoutfnm=None, errorfnm=None, logspecial=None, cwd=None):
    # we take a space-separated string as the input, but subprocess.run() likes
    # to have it as list, so we do split()
    # capture_output exists in  python  > 3.7, but let's jut keep this piece of code now that we have it

    # in a couple of places in subprocess.py we see the snippet
    # if env is None:
    #    env = os.environ
    # so if we pass None as env it will not obliterate the os.environ, but use it
    env = set_env(env_variables, unset_env_vars, env_vars_extend)
    # from https://docs.python.org/3/library/subprocess.html#security-considerations
    # Unlike some other popen functions, this implementation will never implicitly call a system shell.
    # This means that all characters, including shell metacharacters, can safely be passed to child processes.
    # If the shell is invoked explicitly, via shell=True, it is the application’s responsibility to ensure that all
    # whitespace and metacharacters are quoted appropriately to avoid shell injection vulnerabilities.
    # If shell is False, the first argument to run must be a list, e.g. ["ls", "-l", "/dev/null"]
    # (careful if ever attempting to set shell=True here - the argument with spaces would have to be quoted)
    stdout_to = open(stdoutfnm, "a+") if stdoutfnm else subprocess.PIPE
    stderr_to = open(errorfnm, "a+") if errorfnm else subprocess.PIPE
    if version_info >= (3, 7):
        # if  capture_output=False stderr is not captured (and neither is stdout)
        ret = subprocess.run(shlex.split(cmd_string), stdout=stdout_to, stderr=stderr_to, env=env, cwd=cwd)
    else:
        ret = subprocess.run(shlex.split(cmd_string), stdout=stdout_to, stderr=stderr_to, env=env)
    if stdoutfnm: stdout_to.close()
    if errorfnm: stderr_to.close()

    try:
        ret.check_returncode()  # if the return code is non-zero, raises a CalledProcessError.
    except subprocess.CalledProcessError as e:
        errmsg = f"\nin {os.getcwd()}\nwhile running {cmd_string}\n{e}\n"
        if ret.stderr: errmsg += ret.stderr.decode('utf-8') + "\n"
        if not logspecial:
            logger.error(errmsg)
        elif type(logspecial) == logging.Logger:
            logspecial.error(errmsg)
        elif logspecial == sys.stdout or logspecial == sys.stdin:
            print(errmsg, file=logspecial)
        else:
            print(errmsg, file=sys.stderr)

        if noexit:
            return False
        else:
            exit(1)

    return ret.stdout.decode('utf-8').strip() if ret.stdout else None

