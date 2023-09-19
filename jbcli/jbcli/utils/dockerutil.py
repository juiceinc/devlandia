"""Provides a wrapper around subprocess calls to issue Docker commands.
"""
from __future__ import print_function

import platform
from glob import glob
import json
import structlog
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
toplog = structlog.get_logger()

class WatchHandler(FileSystemEventHandler):
    def __init__(self, should_reload=False, custom=False):
        self.should_reload = should_reload
        self.custom = custom

    def on_modified(self, event, env=None):
        if sys.platform == "win32":
            path = re.split(r"[\\/]", event.src_path)
        else:
            path = event.src_path.split("/")

        if path[0] != 'apps':
            while path and path[0] != 'devlandia':
                path.pop(0)
            path.pop(0)

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
                    refresh_browser(5, custom=self.custom)
            else:
                # Try to load app via api, fall back to calling docker.exec_run
                echo_warning(f"{app} is loading...")
                if not load_app(app, custom=self.custom):
                    run(f"/venv/bin/python manage.py loadjuiceboxapp {app}", env=env)
                echo_success(f"{app} was added successfully.")
                if self.should_reload:
                    refresh_browser(custom=self.custom)

        else:
            click.echo(f"Change to {event.src_path} ignored")

        click.echo("Waiting for changes...")


def _intersperse(el, l):
    return [y for x in zip([el] * len(l), l) for y in x]


def docker_compose(args, env=None, ganesha=False, custom=False, arch=None, emulate=False):
    # Since our docker-compose.selfserve.yml file is the first one we pass,
    # we need to pass `--project-name` and `--project-directory`.
    log = toplog.bind(function="docker-compose")
    log.info(f"Running docker-compose with {args}")
    compose_files = []
    if ganesha:
        compose_files.append("docker-compose.ganesha.yml")
    if arch == "x86_64":
        compose_files = ["common-services.yml"]
        if custom:
            compose_files.append("docker-compose.custom.yml")
        else:
            compose_files.append("docker-compose.selfserve.yml")
    elif arch in ["arm", "i386"]:
        compose_files = ["common-services.arm.yml", "docker-compose.arm.yml"]
        if custom:
            compose_files.remove("docker-compose.arm.yml")
            compose_files.append("docker-compose.arm.custom.yml")
        if emulate and not custom:
            compose_files.remove("docker-compose.arm.yml")
            compose_files.append("docker-compose.selfserve.yml")


    compose_files.extend(glob("docker-compose-*.yml"))
    if "docker-compose-ssh.yml" in compose_files and 'stop' in args:
        compose_files.remove("docker-compose-ssh.yml")
    if ganesha:
        compose_files.append("docker-compose.ganesha.yml")
    file_args = _intersperse("-f", compose_files)
    log.info(f"Running docker-compose with {file_args} files")
    env_name = os.path.basename(os.path.abspath("."))
    cmd = ["docker-compose", "--project-directory", ".", "--project-name", env_name]
    return check_call(cmd + file_args + args, env=env)


def up(env=None, ganesha=False, arch=None, custom=False, emulate=False):
    """Starts and optionally creates a Docker environment based on
    docker-compose.yml"""
    docker_compose(["up"], env=env, ganesha=ganesha, arch=arch, custom=custom, emulate=emulate)


def run_jb(cmd, env=None, service="juicebox"):
    is_ganesha = service == "ganesha"
    docker_compose(["run", service] + cmd, env=env, ganesha=is_ganesha)


def destroy(arch=None, custom=False, ganesha=False):
    """Removes all containers and networks defined in docker-compose.selfserve.yml"""
    docker_compose(["down"], arch=arch, custom=custom, ganesha=ganesha)


def halt(arch=None, custom=False):
    """Halts all containers defined in docker-compose file."""
    docker_compose(["stop"], custom=custom, arch=arch)


def is_running():
    """Checks whether or not a Juicebox container is currently running.

    :rtype: ``bool``
    """
    custom, selfserve = False, False
    click.echo("Checking to see if Juicebox is running...")
    containers = client.containers.list()
    print(containers)
    for container in containers:
        print(f"Checking images: {container.name}")
        if "juicebox_custom" in container.name:
            custom = True
        if "juicebox_selfserve" in container.name:
            selfserve = True
    return [custom, selfserve]


def ensure_root():
    """Verifies that we are in the devlandia root directory

    :rtype: ``bool``
    """
    if not os.path.isdir("jbcli"):
        # We're not in the devlandia root
        echo_warning(
            "Please run this command from inside the Devlandia root directory."
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


def run(command, env):
    """Runs a command directly in the docker container."""
    print("running command", command)
    if env is not None:
        juicebox = client.containers.get(f"devlandia_juicebox_{env}_1")
        command_run = juicebox.exec_run(command, stream=True)
        for output in command_run:
            if isinstance(output, types.GeneratorType):
                for o in output:
                    if o is not None:
                        print(o)
            elif output is not None:
                print(output)

def parse_dc_file(tag, emulate=False, custom=False, ganesha=False):
    """Parse the docker-compose.selfserve.yml file to build a full path for image
    based on current environment and tag.

    :param emulate: boolean to indicate if we want to download an x86 image even if we're on an arm prcocessor
    :param tag: The tag of the image we want to pull down
    :return: Full path to ECR image with tag.
    :rtype: ``string``
    """
    log = toplog.bind(function="parse_dc_file")
    pull_file = None

    processor = platform.processor()
    log.info(f"{processor} architecture detected.")
    if processor == "x86_64":
        if not os.path.isfile(f"{os.getcwd()}/docker-compose.selfserve.yml"):
            return
        else:
            pull_file = "docker-compose.selfserve.yml"
    elif processor == "arm":
        if not os.path.isfile(f"{os.getcwd()}/docker-compose.arm.yml"):
            return
        if emulate:
            pull_file = "docker-compose.selfserve.yml"
        if custom:
            pull_file = "docker-compose.arm.custom.yml"
        else:
            pull_file = "docker-compose.arm.yml"
    elif processor == "i386":
        check_call(["/usr/bin/arch", "-arm64", "/bin/zsh", "--login"])
        if not os.path.isfile(f"{os.getcwd()}/docker-compose.arm.yml"):
            return
        else:
            pull_file = "docker-compose.arm.yml"
    if not os.path.isfile(f"{os.getcwd()}/docker-compose.selfserve.yml"):
        return
    base_ecr = "423681189101.dkr.ecr.us-east-1.amazonaws.com/"
    dc_list = []
    log.info(f"{pull_file} selected")
    with open(pull_file) as dc:
        for line in dc:
            if base_ecr in line:
                dc_list.append(line.split(":"))
                for pair in dc_list:
                    pair = [i.strip().strip('"') for i in pair]
                    if "juicebox-dev" in pair[1]:
                        if platform.processor() == "x86_64":
                            full_path = f"{base_ecr}juicebox-devlandia:"
                        elif platform.processor() == "arm":
                            if emulate:
                                full_path = f"{base_ecr}juicebox-devlandia:"
                            else:
                                full_path = f"{base_ecr}juicebox-devlandia-arm:"
                        elif platform.processor() == "i386":
                            full_path = f"{base_ecr}juicebox-devlandia-arm:"

                    return full_path + (tag if tag is not None else pair[2])


def pull(tag, emulate=False):
    """Pulls down latest image of the tag that's passed

    :param emulate: flag for changing behavior on arm processors
    :param tag: Tag of image to download from the current environment
    """
    if ensure_home() is not True:
        return
    full_path = parse_dc_file(tag=tag, emulate=emulate)
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


def jb_watch(app="", should_reload=False, custom=False):
    """Run the Juicebox project watcher"""
    running = is_running()
    if custom and running[0] and ensure_home():
        handle_event(should_reload, custom, app)
    elif not custom and running[1] and ensure_home():
        handle_event(should_reload, custom, app)
    else:
        echo_warning("Failed to start project watcher.")
        click.get_current_context().abort()


def handle_event(should_reload, custom, app):
    click.echo("I'm watching you Wazowski...always watching...always.")

    event_handler = WatchHandler(should_reload, custom=custom)
    observer_setup(event_handler, app, custom)


def observer_setup(event_handler, app, custom=False):
    observer = Observer()
    directory = "fruition_custom" if custom else "fruition"
    observer.schedule(event_handler, path=f"apps/{app}", recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def js_watch(custom=False):
    running = is_running()
    if running[0] and custom and ensure_home():
        run("./node_modules/.bin/webpack --mode=development --progress --colors --watch", env='custom')
    elif running[1] and not custom and ensure_home():
        run("./node_modules/.bin/webpack --mode=development --progress --colors --watch", env='selfserve')

def list_local():
    return check_output(["docker", "image", "list"])
