"""Provides a wrapper around subprocess calls to issue Docker commands.
"""
from __future__ import print_function

from glob import glob
import json
import time
import types
from operator import itemgetter
import datetime
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from watchdog.observers import Observer
from tabulate import tabulate

import re
import sys
import os
import shutil

import click
import docker.errors
from .jbapiutil import load_app
from .subprocess import check_call, check_output
from .reload import refresh_browser

from .format import echo_warning, echo_success, human_readable_timediff

client = docker.from_env()


class WatchHandler(FileSystemEventHandler):
    def __init__(self, should_reload=False):
        self.should_reload = should_reload

    def on_modified(self, event):
        if sys.platform == "win32":
            path = re.split(r"[\\/]", event.src_path)
        else:
            path = event.src_path.split("/")

        # Path looks like
        # ['apps', 'privileging', 'stacks', 'overview', 'templates.html']
        app = path[1]
        filename = path[-1]
        is_python_change = filename.endswith(".py") and isinstance(
            event, FileModifiedEvent
        )

        if "builds" not in path and ".idea" not in path and ".git" not in path:
            click.echo(f"Change detected in {app}.")
            if is_python_change:
                # We don't need to reload the app just refresh
                # the browser after juicebox service restarts
                if self.should_reload:
                    refresh_browser(5)
            else:
                # Try to load app via api, fall back to calling docker.exec_run
                if not load_app(app):
                    run(f"/venv/bin/python manage.py loadjuiceboxapp {app}")
                echo_success(f"{app} was added successfully.")
                if self.should_reload:
                    refresh_browser()

        else:
            click.echo(f"Change to {event.src_path} ignored")

        click.echo("Waiting for changes...")


def _intersperse(el, l):
    return [y for x in zip([el] * len(l), l) for y in x]


def docker_compose(args, env=None, ganesha=False, custom=False):
    # Since our docker-compose.selfserve.yml file is the first one we pass,
    # we need to pass `--project-name` and `--project-directory`.
    compose_files = ["common-services.yml"]
    compose_files.extend(glob("docker-compose-*.yml"))
    if ganesha:
        compose_files.append("docker-compose.ganesha.yml")
    if custom:
        compose_files.append("docker-compose.custom.yml")
    else:
        compose_files.append("docker-compose.selfserve.yml")
    file_args = _intersperse("-f", compose_files)
    print(f"Running docker-compose with {file_args} files")
    env_name = os.path.basename(os.path.abspath("."))
    cmd = ["docker-compose", "--project-directory", ".", "--project-name", env_name]
    return check_call(cmd + file_args + args, env=env)


def up(env=None, ganesha=False, custom=False):
    """Starts and optionally creates a Docker environment based on
    docker-compose.selfserve.yml"""
    docker_compose(["up"], env=env, ganesha=ganesha, custom=custom)


def run_jb(cmd, env=None, service="juicebox"):
    is_ganesha = service == "ganesha"
    docker_compose(["run", service] + cmd, env=env, ganesha=is_ganesha)


def destroy():
    """Removes all containers and networks defined in docker-compose.selfserve.yml"""
    docker_compose(["down"])


def halt():
    """Halts all containers defined in docker-compose file."""
    docker_compose(["stop"])


def is_running(service="juicebox", custom=False):
    """Checks whether or not a Juicebox container is currently running.

    :rtype: ``bool``
    """
    click.echo("Checking to see if Juicebox is running...")
    containers = client.containers.list()
    for container in containers:
        print(f"Checking images: {container.name}")
        if service in container.name:
            return container


def ensure_root():
    """Verifies that we are in the devlandia root directory

    :rtype: ``bool``
    """
    if not os.path.isdir("jbcli"):
        # We're not in the devlandia root
        echo_warning(
            "Please run this command from inside the Devlandia root " "directory."
        )
        click.get_current_context().abort()
    return True


def ensure_virtualenv():
    """Verifies that a virtualenv is active

    :rtype: ``bool``
    """
    if not os.environ.get("VIRTUAL_ENV", None):
        echo_warning("Please make sure your virtual env is active.")
        click.get_current_context().abort()
    return True


def ensure_home():
    """Verifies that we are in a Juicebox directory

    :rtype: ``bool``
    """
    if check_home() is None:
        # We're not in the environment home
        echo_warning(
            "Please run this command from inside the desired environment in "
            "Devlandia."
        )
        click.get_current_context().abort()
    return True


def check_home():
    if os.path.isfile("docker-compose.selfserve.yml") and os.path.isdir("apps"):
        return os.path.dirname(os.path.abspath(os.path.curdir))


def run(command):
    """Runs a command directly in the docker container."""
    print("running command", command)
    containers = client.containers.list()
    for container in containers:
        # changed here to allow support for hstm environments too, just gets
        #  any juicebox container
        if "juicebox" in container.name:
            juicebox = client.containers.get(container.name)
            command_run = juicebox.exec_run(command, stream=True)
            for output in command_run:
                if isinstance(output, types.GeneratorType):
                    for o in output:
                        if o is not None:
                            print(o)
                elif output is not None:
                    print(output)


def parse_dc_file(tag):
    """Parse the docker-compose.selfserve.yml file to build a full path for image
    based on current environment and tag.

    :param tag: The tag of the image we want to pull down
    :return: Full path to ECR image with tag.
    :rtype: ``string``
    """
    if not os.path.isfile(f"{os.getcwd()}/docker-compose.selfserve.yml"):
        return
    base_ecr = "423681189101.dkr.ecr.us-east-1.amazonaws.com/"
    dc_list = []
    with open("docker-compose.selfserve.yml") as dc:
        for line in dc:
            if base_ecr in line:
                dc_list.append(line.split(":"))
                for pair in dc_list:
                    pair = [i.strip().strip('"') for i in pair]

                    if "controlcenter-dev" in pair[1]:
                        full_path = f"{base_ecr}controlcenter-dev:"
                    elif "juicebox-dev" in pair[1]:
                        full_path = f"{base_ecr}juicebox-devlandia:"

                    return full_path + (tag if tag is not None else pair[2])


def pull(tag):
    """Pulls down latest image of the tag that's passed

    :param tag: Tag of image to download from the current environment
    """
    if ensure_home() is not True:
        return
    full_path = parse_dc_file(tag=tag)
    abs_path = os.path.abspath(os.getcwd())
    os.chdir("../..")
    docker_login = check_output(
        [
            "aws",
            "ecr",
            "get-login",
            "--registry-ids",
            "423681189101",
            "976661725066",
            "--no-include-email",
        ]
    )
    docker_logins = docker_login.split(b"\n")
    for docker_login in docker_logins:
        if docker_login:
            check_call(docker_login.split())
    check_call(["docker", "pull", full_path])
    os.chdir(abs_path)


def image_list(showall=False, print_flag=True, semantic=False):
    """Lists available tagged images"""
    semantic_version_tag_pattern = re.compile(r"^\d+\.\d+\.\d+$")
    imageList = []
    now = datetime.datetime.now()
    cmd = "aws ecr describe-images --registry-id 423681189101 --repository-name juicebox-devlandia"
    images = json.loads(check_output(cmd.split()))
    for image in images["imageDetails"]:
        if "imageTags" in image:
            pushed = datetime.datetime.fromtimestamp(int(image["imagePushedAt"]))
            for tag in image["imageTags"]:
                human_readable = human_readable_timediff(pushed)
                is_semantic_tag = bool(semantic_version_tag_pattern.match(tag))
                if tag == "master":
                    tag_priority = 4
                elif tag == "develop":
                    tag_priority = 3
                elif is_semantic_tag:
                    tag_priority = 2
                else:
                    tag_priority = 1

                # If semantic, just return semantic tags
                meets_semantic_criteria = (semantic and is_semantic_tag) or not semantic
                # Use if showall is true, return all tags, otherwise return just last 30 days
                meets_time_criteria = showall or (
                    pushed >= now - datetime.timedelta(days=30)
                )

                if meets_semantic_criteria and meets_time_criteria:
                    row = [tag, pushed, human_readable, tag_priority, is_semantic_tag]
                    imageList.append(row)

    # Find the semantic version of stable
    imageList.sort(key=itemgetter(1))

    newImageList = []
    prevtag = None
    for row in imageList:
        tag, pushed, human_readable, tag_priority, is_semantic_tag = row
        if tag == "master":
            row = [tag, pushed, human_readable, tag_priority, is_semantic_tag, prevtag]
        else:
            row = [tag, pushed, human_readable, tag_priority, is_semantic_tag, None]
        newImageList.append(row)
        prevtag = tag

    # Sort in descending order of priority and timestamp
    def sort_order(row):
        return (row[3], row[0])

    newImageList.sort(key=sort_order, reverse=True)

    if print_flag:
        print(
            tabulate(
                newImageList,
                headers=[
                    "Image Name",
                    "Time Tagged",
                    "Relative",
                    "Priority",
                    "Is Semantic",
                    "Master Version",
                ],
            )
        )

    return newImageList


def set_tag(env, tag):
    """Set an environment to use a tagged image"""
    ensure_root()

    os.chdir(f"./environments/{env}")
    changed = False
    with open("./docker-compose.selfserve.yml", "rt") as dc:
        with open("out.txt", "wt") as out:
            for line in dc:
                if "juicebox-devlandia:" in line:
                    oldTag = line.rpartition(":")[2]
                    if oldTag[:-2] != tag:
                        out.write(line.replace(oldTag, tag) + '"\n')
                        changed = True
                else:
                    out.write(line)
    if changed:
        shutil.move("./out.txt", "./docker-compose.selfserve.yml")
    else:
        os.remove("./out.txt")

    echo_success(f"Environment {env} is using {tag}")
    os.chdir("../..")


def get_state(container_name):
    """Get status of juicebox container

    :param container_name: Container name to get the state of. :returns:
    String of the state of the given container name.  ``exited``,
    ``running``, ``notfound``. :rtype: ``string``
    """
    return client.containers.get(container_name).status


def jb_watch(app="", should_reload=False):
    """Run the Juicebox project watcher"""
    if is_running() and ensure_home():
        click.echo("I'm watching you Wazowski...always watching...always.")

        event_handler = WatchHandler(should_reload)
        observer = Observer()

        observer.schedule(event_handler, path=f"apps/{app}", recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        echo_warning("Failed to start project watcher.")
        click.get_current_context().abort()


def js_watch():
    if is_running() and ensure_home():
        run(
            "./node_modules/.bin/webpack --mode=development --progress --colors --watch"
        )


def list_local():
    return check_output(["docker", "image", "list"])
