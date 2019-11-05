"""Handles commands involving Juicebox packaged applications
"""
from builtins import str
import logging
import os
import shutil
import tempfile
from uuid import uuid4

import click

from .. import conf
from .format import echo_warning, echo_success
from .subprocess import check_call, CalledProcessError

LOG = logging.getLogger(__name__)
IGNORE_PATTERNS = shutil.ignore_patterns('*.pyc', '.git', 'tmp')


def make_github_repo_url(app):
    """Builds a Github ssh transport url including the GITHUB_ORGANIZATION,
    GITHUB_REPO_PREFIX, and app name.

    :param app: The Juicebox packaged application name
    :type app: str
    """
    return 'git@github.com:{0}/{1}{2}.git'.format(
        conf.GITHUB_ORGANIZATION,
        conf.GITHUB_REPO_PREFIX,
        app)


def make_github_repo_link(app):
    """Builds a Github HTTPS transport url including the GITHUB_ORGANIZATION,
    GITHUB_REPO_PREFIX, and app name.

    :param app: The Juicebox packaged application name
    :type app: str
    """
    return 'https://github.com/{0}/{1}{2}'.format(
        conf.GITHUB_ORGANIZATION,
        conf.GITHUB_REPO_PREFIX,
        app)


def clone(name, source, dest, init_vcs=True, track_vcs=True):
    """Create a Juicebox packaged application

    :param name: The packaged application name
    :type name: str
    :param source: The application name we are cloning
    :type source: str
    :param dest: The directory in which to create the packaged application
    :type dest: str
    :param init_vcs: Dictates if we will setup git for the packaged application
    :type init_vcs: bool
    :param track_vcs: Dictates if we will establish a remote tracking branch
                      (Only valid if init_vcs is also True)
    :type track_vcs: bool
    """

    # TODO: Call the Juicebox App API to get a unique ID
    # and have Git repositories created.

    try:
        shutil.copytree(source, dest, ignore=IGNORE_PATTERNS)
    except shutil.ExecError:
        echo_warning('Cloning failed on the copy step')
        return False

    replacements = {'slug:': name, 'label:': name, 'id:': str(uuid4())[:8]}
    dest_app_yaml = os.path.join(dest, 'app.yaml')
    replace_in_yaml(dest_app_yaml, replacements)

    if init_vcs:
        perform_init_vcs(name, dest, track_vcs)
    return True


def perform_init_vcs(name, app_dir, track_vcs=True):
    """ Initializes a Git repo, setups a track branch, pushes to it, and
    sets up the repo in github desktop

    :param name: The packaged application name
    :type name: str
    :param app_dir: The directory in which to create the repository
    :type app_dir: str
    :param track_vcs: Dictates if we will establish a remote tracking branch
                      (Only valid if init_vcs is also True)
    :type track_vcs: bool
    """
    github_repo_url = make_github_repo_url(name)
    github_repo_link = make_github_repo_link(name)
    try:
        click.echo('Initializing Git repository')
        os.chdir(app_dir)
        check_call(['git', 'init'])
        check_call(['git', 'add', '.'])
        check_call(['git', 'commit', '-m', 'Initial commit'])
    except CalledProcessError as exc_info:
        click.echo()
        echo_warning('Failed to initialize Git repository.')
        return

    if track_vcs:
        try:
            click.echo('Setting up remote tracking branch')
            check_call(['git', 'remote', 'add', 'origin', github_repo_url])
            click.echo('Pushing to origin')
            check_call(['git', 'push', '-u', 'origin', 'master'])
            click.echo('View in a browser at {}'.format(github_repo_link))
        except CalledProcessError as exc_info:
            LOG.error(str(exc_info))
            click.echo()
            errmsg = """We had trouble connecting your repo to Github!
Your repo is expected to be at {0}
Please ensure you have the appropriate permissions to push.

To connect your repo manually, you can run the following:

$ cd {1}
$ git remote add origin {2}
$ git push -u origin master
            """.format(app_dir, github_repo_link, github_repo_url)

            echo_warning(errmsg)
        try:
            check_call(['github', '{}'.format(app_dir)])
        except CalledProcessError as exc_info:
            LOG.error(str(exc_info))
            click.echo()
            echo_warning('Failed to add to github desktop')
        except OSError as exc_info:
            LOG.error(str(exc_info))
            click.echo()
            echo_warning('Failed to add to github desktop')


def replace_in_yaml(file_path, replacements):
    """ Replaces FLAT keys in a yaml file

    :param file_path: Path to the file we are working on
    :type file_path: str
    :param replacements: YAML key and value
    :type replacements: dict

    Example replacements:
        {'slug:': name,
         'label:': name,
         'id:': str(uuid4())[:8]}

    NOTICE: That you must include the : in the YAML key name
    """
    # Create temp file
    handle, abs_path = tempfile.mkstemp()
    with open(abs_path, 'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                for key in list(replacements.keys()):
                    if key in line:
                        line = u'{} {}\n'.format(key, replacements[key])
                new_file.write(line)
    os.close(handle)
    # Remove original file
    os.remove(file_path)
    # Move new file
    shutil.move(abs_path, file_path)
