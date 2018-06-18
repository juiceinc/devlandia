"""Provides a wrapper around subprocess calls to issue Docker commands.
"""
from __future__ import print_function

import json
import time
from operator import itemgetter
import datetime
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from tabulate import tabulate
import maya
import re
import sys
import os

import click
import docker.errors
from .subprocess import check_call, check_output

from .format import echo_warning

client = docker.from_env()


class WatchHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if sys.platform == 'win32':
            path = re.split(r'[\\/]', event.src_path)
        else:
            path = event.src_path.split('/')
        click.echo('Change detected in app: {}.'.format(path))
        run('/venv/bin/python manage.py loadjuiceboxapp ' + path[3])
        click.echo('Waiting for changes...')


def up():
    """Starts and optionally creates a Docker environment based on
    docker-compose.yml """
    check_call(['docker-compose', 'up'])


def destroy():
    """Removes all containers and networks defined in docker-compose.yml"""
    check_call(['docker-compose', 'down'])


def halt():
    """Halts all containers defined in docker-compose file."""
    check_call(['docker-compose', 'stop'])


def is_running():
    """Checks whether or not a Juicebox container is currently running.

    :rtype: ``bool``
    """
    running = False
    click.echo('Checking to see if Juicebox is running...')
    containers = client.containers.list(all=True)
    if containers:
        for container in containers:

            if 'juicebox' in container.name and get_state(
                    container.name) == 'running':
                running = True
    return running


def ensure_root(output=True):
    """Verifies that we are in the devlandia root directory

    :rtype: ``bool``
    """
    if not os.path.isdir('environments'):
        # We're not in the devlandia root
        echo_warning(
            'Please run this command from inside the Devlandia root '
            'directory.')
        click.get_current_context().abort()
    return True


def ensure_virtualenv(output=True):
    """Verifies that a virtualenv is active

    :rtype: ``bool``
    """
    if not os.environ.get('VIRTUAL_ENV', None):
        echo_warning('Please make sure your virtual env is active.')
        click.get_current_context().abort()
    return True


def ensure_home(output=True):
    """Verifies that we are in a Juicebox directory

    :rtype: ``bool``
    """
    if not os.path.isfile('docker-compose.yml') or not os.path.isdir('../../apps'):
        # We're not in the environment home
        echo_warning(
            'Please run this command from inside the desired environment in '
            'Devlandia.')
        click.get_current_context().abort()
    if 'hstm-' in os.getcwd():
        os.environ['AWS_PROFILE'] = 'hstm'
    return True


def ensure_test_core():
    """Verifies that we are in the Juicebox test directory

    :rtype: ``bool``
    """
    if 'test' in os.getcwd() or 'core' in os.getcwd():
        return True
    return False


def run(command):
    """Runs a command directly in the docker container.
    """
    print("running command", command)
    containers = client.containers.list()
    for container in containers:
        # changed here to allow support for hstm environments too, just gets
        #  any juicebox container
        if 'juicebox' in container.name:
            juicebox = client.containers.get(container.name)
            command_run = juicebox.exec_run(command, stream=True)
            for output in command_run:
                print(output)


def parse_dc_file(tag):
    """Parse the docker-compose.yml file to build a full path for image
    based on current environment and tag.

    :param tag: The tag of the image we want to pull down
    :return: Full path to ECR image with tag.
    :rtype: ``string``
    """
    base_ecr = '423681189101.dkr.ecr.us-east-1.amazonaws.com/'
    dc_list = []
    if os.path.isfile(os.getcwd() + '/docker-compose.yml'):
        with open("docker-compose.yml") as dc:
            for line in dc:
                if base_ecr in line:
                    dc_list.append(line.split(':'))
                    for pair in dc_list:
                        pair = [i.strip().strip('\"') for i in pair]

                        if 'controlcenter-dev' in pair[1]:
                            full_path = base_ecr + 'controlcenter-dev:'
                        elif 'juicebox-dev' in pair[1]:
                            full_path = base_ecr + 'juicebox-devlandia:'

                        if tag is not None:
                            full_path = full_path + tag
                        else:
                            full_path = full_path + pair[2]
                        return full_path


def pull(tag):
    """Pulls down latest image of the tag that's passed

    :param tag: Tag of image to download from the current environment
    """
    if ensure_home(output=False) is True:
        full_path = parse_dc_file(tag=tag)
        abs_path = os.path.abspath(os.getcwd())
        os.chdir('../..')
        docker_login = check_output([
            'aws', 'ecr', 'get-login', '--registry-ids', '423681189101',
            '--no-include-email'])
        docker_login = docker_login.split()
        check_call(docker_login)
        check_call(['docker', 'pull', full_path])
        os.chdir(abs_path)


def image_list(showall=False, print_flag=True, semantic=False):
    """Lists available tagged images"""
    imageList = []
    cmd = "aws ecr describe-images --registry-id 423681189101 --repository-name juicebox-devlandia"
    images = json.loads(check_output(cmd.split()))
    for image in images['imageDetails']:
        if 'imageTags' in image:
            for tag in image['imageTags']:

                pushed = maya.MayaDT.from_datetime(
                    datetime.datetime.fromtimestamp(
                        int(image['imagePushedAt']))).add(hours=5)

                if not showall and not semantic:
                    if pushed >= maya.when('30 days ago'):
                        imageList.append(
                            [tag, image['imageDigest'][7:], pushed.slang_time()])
                elif showall and not semantic:
                    imageList.append(
                        [tag, image['imageDigest'][7:], pushed.slang_time()])
                elif semantic and not showall:
                    if '.' in tag:
                        imageList.append([tag, image['imageDigest'][7:],
                                          pushed.slang_time()])

    if print_flag:
        print(tabulate(sorted(imageList, key=itemgetter(0)), headers=['Image Name', 'Digest',
                                           'Time Tagged']))

    return imageList


def get_state(container_name):
    """Get status of juicebox container

    :param container_name: Container name to get the state of. :returns:
    String of the state of the given container name.  ``exited``,
    ``running``, ``notfound``. :rtype: ``string``
    """
    return client.containers.get(container_name).status


def jb_watch():
    """Run the Juicebox project watcher"""
    if is_running() and ensure_home():
        click.echo('I\'m watching you Wazowski...always watching...always.')
        event_handler = WatchHandler()
        observer = Observer()
        observer.schedule(event_handler, path='../../apps/', recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        echo_warning('Failed to start project watcher.')
        click.get_current_context().abort()


def js_watch():
    if is_running() and ensure_home():
        run('./node_modules/.bin/webpack --progress --colors --watch')
