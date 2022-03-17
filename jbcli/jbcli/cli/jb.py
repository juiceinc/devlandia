"""This is the code for the jb cli command."""

from __future__ import print_function

import atexit
import errno
import fcntl
import os
import shutil
import socket
import struct
import sys
import time
from collections import OrderedDict
from multiprocessing import Process
from subprocess import Popen
import re

import click
import docker.errors
import yaml
from PyInquirer import prompt
from six.moves.urllib.parse import urlparse, urlunparse

from ..utils import apps, dockerutil, jbapiutil, subprocess, auth, format
from ..utils.format import echo_highlight, echo_warning, echo_success
from ..utils.reload import create_browser_instance
from ..utils.secrets import get_deployment_secrets
from ..utils.storageutil import Stash

MY_DIR = os.path.abspath(os.path.dirname(__file__))
DEVLANDIA_DIR = os.path.abspath(os.path.join(MY_DIR, "..", "..", ".."))
JBCLI_DIR = os.path.abspath(os.path.join(DEVLANDIA_DIR, "jbcli"))

stash = Stash("~/.config/juicebox/devlandia.toml")


def normalize(name):
    return name.replace("_", "-")


@click.group(context_settings={"token_normalize_func": normalize})
@click.version_option()
def cli():
    """
    Juicebox CLI app
    """
    pass


@cli.command()
@click.argument("applications", nargs=-1, required=True)
@click.option(
    "--add-desktop/--no-add-desktop",
    default=False,
    help="Optionally add to Github Desktop",
)
@click.option(
    "--runtime",
    default="venv",
    help="Which runtime to use, defaults to venv, the only other option is venv3",
)
def add(applications, add_desktop, runtime):
    """Checkout a juicebox app (or list of apps) and load it, can check out
    a specific branch by using `appslug@branchname`
    """
    os.chdir(DEVLANDIA_DIR)
    try:
        if not dockerutil.is_running():
            echo_warning("Juicebox is not running.  Please run jb start.")
            click.get_current_context().abort()

        failed_apps = []

        for app in applications:
            branch = False
            if "@" in app:
                app_split = app.split("@")
                app = app_split[0]
                branch = app_split[1]
            app_dir = "apps/{}".format(app)
            if os.path.isdir(app_dir):
                # App already exists, update it.
                echo_highlight(f"App {app} already exists.")

            else:
                # App doesn't exist, clone it
                echo_highlight(f"Adding {app}...")
                echo_highlight(f"Downloading app {app} from Github.")
                github_repo_url = apps.make_github_repo_url(app)

                try:
                    if not branch:
                        subprocess.check_call(
                            ["git", "clone", github_repo_url, app_dir]
                        )
                    else:
                        subprocess.check_call(
                            ["git", "clone", "-b", branch, github_repo_url, app_dir]
                        )
                except subprocess.CalledProcessError:
                    failed_apps.append(app)
                    continue

                if add_desktop:
                    try:
                        subprocess.check_call(["github", app_dir])
                    except subprocess.CalledProcessError:
                        echo_warning(f"Failed to add {app} to Github Desktop.")
            try:
                if not jbapiutil.load_app(app):
                    dockerutil.run(
                        f"/{runtime}/bin/python manage.py loadjuiceboxapp {app}"
                    )
                    echo_success(f"{app} was added successfully.")

            except docker.errors.APIError as e:
                echo_warning(f"Failed to add {app} to the Juicebox VM.")
                failed_apps.append(app)
                print(e.explanation)

        if failed_apps:
            click.echo()
            echo_warning(f'Failed to load: {", ".join(failed_apps)}.')
            click.get_current_context().abort()
    except docker.errors.APIError as de:
        echo_warning(de.message)


@cli.command()
@click.argument("existing_app", required=True)
@click.argument("new_app", required=True)
@click.option("--init/--no-init", default=True, help="Initialize VCS repository")
@click.option("--track/--no-track", default=True, help="Track remote VCS repository")
@click.option(
    "--runtime",
    help="Which runtime to use, defaults to venv, the only other option is venv3",
    default="venv",
)
def clone(existing_app, new_app, init, track, runtime):
    """Clones an existing application to a new one. Make sure you have a
    Github repo setup for the new app.
    """
    try:
        if dockerutil.is_running():
            existing_app_dir = "apps/{}".format(existing_app)
            new_app_dir = "apps/{}".format(new_app)

            if not os.path.isdir(existing_app_dir):
                echo_warning("App {} does not exist.".format(existing_app))
                click.get_current_context().abort()
            if os.path.isdir(new_app_dir):
                echo_warning("App {} already exists.".format(new_app))
                click.get_current_context().abort()

            echo_highlight("Cloning from {} to {}...".format(existing_app, new_app))

            try:
                result = apps.clone(
                    new_app,
                    existing_app_dir,
                    new_app_dir,
                    init_vcs=init,
                    track_vcs=track,
                )
            except (OSError, ValueError):
                echo_warning("Cloning failed")
                click.get_current_context().abort()
            if not result:
                click.get_current_context().abort()

            try:
                dockerutil.run(
                    "/{}/bin/python manage.py loadjuiceboxapp {}".format(
                        runtime, new_app
                    )
                )
            except docker.errors.APIError:
                echo_warning("Failed to load: {}.".format(new_app))
                click.get_current_context().abort()
        else:
            echo_warning("Juicebox is not running.  Run jb start.")
            click.get_current_context().abort()
    except docker.errors.APIError as de:
        echo_warning(de.message)


@cli.command()
@click.argument("applications", nargs=-1, required=True)
@click.confirmation_option(
    "--yes", is_flag=True, prompt="Are you sure you want to delete?"
)
@click.option(
    "--runtime",
    help="Which runtime to use, defaults to venv, the only other option is venv3"
    "option.",
    default="venv",
)
def remove(applications, runtime):
    """Remove a juicebox app (or list of apps) from your local environment"""
    os.chdir(DEVLANDIA_DIR)
    try:
        if dockerutil.is_running() and dockerutil.ensure_home():
            failed_apps = []

            for app in applications:
                try:
                    if os.path.isdir("apps/{}".format(app)):
                        echo_highlight("Removing {}...".format(app))
                        shutil.rmtree("apps/{}".format(app))
                        dockerutil.run(
                            "/{}/bin/python manage.py deletejuiceboxapp {}".format(
                                runtime, app
                            )
                        )
                        echo_success("Successfully deleted {}".format(app))
                    else:
                        echo_warning("App {} didn't exist.".format(app))
                except docker.errors.APIError:
                    print(docker.errors.APIError.message)
                    failed_apps.append(app)
            if failed_apps:
                click.echo()
                echo_warning("Failed to remove: {}.".format(", ".join(failed_apps)))
                click.get_current_context().abort()
        else:
            echo_warning("Juicebox is not running.  Run jb start.")
            click.get_current_context().abort()
    except docker.errors.APIError:
        click.echo()
        echo_warning("Juicebox is not running.  Run jb start.")
        click.get_current_context().abort()


@click.option("--includejs", default=False, help="Watch for js changes", is_flag=True)
@click.option("--app", default="", help="Watch a specific app.")
@click.option(
    "--reload", default=False, help="Refresh browser after file changes.", is_flag=True
)
@cli.command()
def watch(includejs=False, app="", reload=False):
    """Watch for changes in apps and js and reload/rebuild"""
    procs = []
    jb_watch_proc = Process(
        target=dockerutil.jb_watch, kwargs={"app": app, "should_reload": reload}
    )
    jb_watch_proc.start()
    procs.append(jb_watch_proc)

    if reload:
        create_browser_instance()

    if includejs:
        js_watch_proc = Process(target=dockerutil.js_watch)
        js_watch_proc.start()
        procs.append(js_watch_proc)

    for proc in procs:
        proc.join()


@click.option("--showall", default=False, help="Show all tagged images", is_flag=True)
@click.option(
    "--semantic", default=False, help="Show all semantic versions.", is_flag=True
)
@cli.command()
def ls(showall=False, semantic=False):
    """List available containers"""
    try:
        echo_success("The following tagged images are available:")
        dockerutil.image_list(showall=showall, semantic=semantic)
    except subprocess.CalledProcessError:
        echo_warning("You must login to the registry first.")


def populate_env_with_secrets():
    env = get_deployment_secrets()
    env.update(os.environ)
    return env


def cleanup_ssh():
    compose_fn = os.path.join(DEVLANDIA_DIR, "docker-compose-ssh.yml")
    try:
        os.remove(compose_fn)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def get_host_ip():
    try:
        ifname = b"docker0"
        SIOCGIFADDR = 0x8915
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        interface = struct.pack("256s", ifname[:15])
        addr = fcntl.ioctl(s.fileno(), SIOCGIFADDR, interface)[20:24]
        return socket.inet_ntoa(addr)
    except Exception as e:
        print(
            "[get_host_ip] Couldn't get docker0 address, falling back to slow method", e
        )
        out = dockerutil.client.containers.run(
            "ubuntu:18.04", "getent hosts host.docker.internal"
        )
        # returns output like:
        #   192.168.1.1    host.docker.internal
        #   192.168.1.2    host.docker.internal
        return out.splitlines()[0].split()[0].decode("ascii")


def activate_ssh(environ):
    """
    Start the SSH tunnels, and manipulate the environment variables so that
    they are pointing at the right ports.
    """

    redshifts = {}
    # these local ports are arbitrary
    for envvar, localport in [
        ("JB_REDSHIFT_CONNECTION", 5439),
        ("JB_HSTM_REDSHIFT_CONNECTION", 5438),
        ("JB_PREVERITY_REDSHIFT_CONNECTION", 5437),
    ]:
        if envvar not in environ:
            continue
        # python's urlparse makes it difficult to just change the port, but
        # that's what we're doing here:
        url = urlparse(environ[envvar])
        old_netloc = url.netloc
        old_netloc_without_port = old_netloc.rsplit(":", 1)[0]
        new_netloc = f"{old_netloc_without_port}:{localport}"
        new_conn_string = urlunparse(url._replace(netloc=new_netloc))
        redshifts[envvar] = (url, localport, new_conn_string)

    ssh_links = [
        ["-L", f"0.0.0.0:{port}:{url.hostname}:5439"]
        for (url, port, _) in redshifts.values()
    ]
    ssh_links = [leaf for tree in ssh_links for leaf in tree]  # flatten

    command = [
        "ssh",
        "-T",
        "-N",
        "-o",
        "ServerAliveInterval 30",
        "-o",
        "ServerAliveCountMax 3",
        "-o",
        "StrictHostKeyChecking=accept-new",
        *ssh_links,
        "vpn2.juiceboxdata.com",
    ]
    process = Popen(command)

    def cleanup():
        process.kill()
        print("waiting for SSH tunnels to stop...")
        while process.poll() is None:
            time.sleep(0.2)
        print("exit status:", process.poll())
        cleanup_ssh()

    atexit.register(cleanup)

    compose_fn = os.path.join(DEVLANDIA_DIR, "docker-compose-ssh.yml")
    host_addr = get_host_ip()
    content = {
        "version": "3.2",
        "services": {
            "juicebox": {
                "extra_hosts": [
                    f"{url.hostname}:{host_addr}" for (url, _, _) in redshifts.values()
                ],
                # We want to make sure that the environment variables we're going to set
                # will be passed through to the container.
                "environment": list(redshifts.keys()),
            }
        },
    }
    with open(compose_fn, "w") as compose_file:
        compose_file.write(yaml.safe_dump(content))
    # We *could* just write the new connection strings into the YAML content above,
    # but that would mean leaving secrets around on disk, so we'll just put them into
    # the environment instead:
    return {
        envvar: new_conn_string
        for (envvar, (_, _, new_conn_string)) in redshifts.items()
    }


@cli.command()
@click.argument("env", nargs=1, required=False)
@click.option(
    "--noupdate",
    default=False,
    help="Do not automatically update Docker image on start",
    is_flag=True,
)
@click.option(
    "--noupgrade",
    default=False,
    help="Do not automatically update jb and generators on start",
    is_flag=True,
)
@click.option(
    "--ssh", default=False, is_flag=True, help="run an SSH tunnel for redshift"
)
@click.option("--ganesha", default=False, is_flag=True, help="Enable ganesha")
@click.option("--hstm", default=False, is_flag=True, help="Enable hstm")
@click.option(
    "--core",
    default=False,
    is_flag=True,
    help="Use local fruition checkout with this image "
    "(core and hstm-core environments do this automatically)",
)
@click.option(
    "--dev-recipe",
    default=False,
    is_flag=True,
    help="Use local recipe checkout, requires running a core environment",
)
@click.option(
    "--snapshot",
    default=False,
    is_flag=True,
    help="Start local snapshot server for local snapshot related development",
)
@click.pass_context
def start(
    ctx, env, noupdate, noupgrade, ssh, ganesha, hstm, core, dev_recipe, snapshot
):
    """Configure the environment and start Juicebox"""
    auth.has_current_session()
    if dockerutil.is_running():
        echo_warning("An instance of Juicebox is already running")
        echo_warning("Run `jb stop` to stop this instance.")
        return

    # A dictionary of environment names and tags to use
    tag_replacements = OrderedDict()
    tag_replacements["core"] = "develop-py3"
    tag_replacements["dev"] = "develop-py3"
    tag_replacements["stable"] = "master-py3"
    tag_replacements["hstm-dev"] = "hstm-qa"
    tag_replacements["hstm-newcore"] = "develop-py3"

    env = get_environment_interactively(env, tag_replacements)

    core_path = "readme"
    core_end = "unused"
    workflow = "dev"
    recipe_path = "recipereadme"
    recipe_end = "unused"

    # "core" devlandia uses editable fruition code
    is_core = "core" in env or core
    is_hstm = env.startswith("hstm-") or hstm

    if is_core:
        if os.path.exists("fruition"):
            core_path = "fruition"
            core_end = "code"
            workflow = "core"
        else:
            print(
                "Could not find Local Fruition Checkout, please check that it is symlinked to the top level of "
                "Devlandia"
            )
            sys.exit(1)

    # "dev_recipe" devlandia uses editable recipe code
    if dev_recipe:
        if is_core:
            if os.path.exists("recipe"):
                recipe_path = "recipe"
                recipe_end = "code/recipe"
            else:
                print(
                    "Could not find local recipe checkout, please check that it is symlinked to the top level of "
                    "Devlandia"
                )
                sys.exit(1)
        else:
            print("The dev-recipe flag requires running a core environment")
            sys.exit(1)

    # Replace the enviroment with the tagged Juicebox image
    # that is running in that environment
    tag = tag_replacements[env] if env in tag_replacements.keys() else env

    if noupdate:
        image_query = check_outdated_image(tag)
        if image_query == "yes":
            noupdate = False
    if not noupgrade:
        ctx.invoke(upgrade)
    with open(".env", "w") as env_dot:
        env_dot.write(
            f"DEVLANDIA_PORT=8000\n"
            f"TAG={tag}\n"
            f"FRUITION={core_path}\n"
            f"FILE={core_end}\n"
            f"WORKFLOW={workflow}\n"
            f"RECIPE={recipe_path}\n"
            f"RECIPEFILE={recipe_end}\n"
        )

    environ = populate_env_with_secrets()

    if not noupdate:
        dockerutil.pull(tag=tag)
    if snapshot:
        activate_snapshot()
    if is_hstm:
        activate_hstm()
        print("Activating HSTM")
    cleanup_ssh()
    if ssh:
        environ.update(activate_ssh(environ))
    dockerutil.up(env=environ, ganesha=ganesha)


@click.argument("days", nargs=1, required=False)
@cli.command()
def interval(days):
    """Set a new value (in days) for the frequency to check docker images for updates."""
    if days:
        stash.put("interval", days)
    else:
        prompt_interval()


def prompt_interval():
    question = [
        {
            "type": "input",
            "name": "interval",
            "message": "How often do you want to be prompted about out of date images (in days)?",
        }
    ]
    answer = prompt(question)["interval"]
    stash.put("interval", answer)


def check_outdated_image(env):
    print("Checking Image age")
    interval_val = 1
    try:
        interval_val = stash.get("interval")
        if interval_val is None:
            echo_warning("Docker image prompt interval not set.")
            prompt_interval()
            interval_val = stash.get("interval")
    except Exception as e:
        pass

    # grab list of docker images from check_call, turn into list of objects, do silly
    # things with regex and return local image age

    local_images = dockerutil.list_local().decode("utf-8")
    lines = local_images.split("\n")
    keys = re.split(r"\s{2,}", lines[0])
    image_list = [dict(zip(keys, re.split(r"\s{2,}", i))) for i in lines[1:-1]]
    local_age = False
    for image in image_list:
        if env in image["TAG"]:
            local_age = image["CREATED"].split()[:-1]
            if local_age[1] in ["an", "a"]:
                if len(local_age) > 2:
                    del local_age[1]
                local_age[0] = "1"
                local_age[1] += "s"

    # if no local image, continue
    if local_age:
        # get list of remote images and find the relavent one and extract the date
        remote_images = dockerutil.image_list(
            showall=True, print_flag=False, semantic=False
        )
        tag_dict = {}
        for row in remote_images:
            (
                tag,
                pushed,
                human_readable,
                tag_priority,
                is_semantic_tag,
                stable_version,
            ) = row
            tag_dict[tag] = f"({tag}) published {human_readable}"
        remote_age = tag_dict[env].split()[2:-1]

        # when it's just one hour / day it's formatted like "an hour/ a day" so we need to sanitize here
        if remote_age[0] in ["an", "a"]:
            remote_age[0] = "1"
            remote_age[1] += "s"

        # compare local and remote
        age_diff = format.compare_human_readable(local_age, remote_age)
        if int(age_diff.days) < int(interval_val):
            return f"image {age_diff} older than remote"
        question = [
            {
                "type": "list",
                "name": "age_diff",
                "message": f"local image is {age_diff} older than remote image, "
                f"would you like to update?",
                "choices": ["no", "yes"],
            }
        ]
        answer = prompt(question)
        return answer["age_diff"]


def get_environment_interactively(env, tag_lookup):
    os.chdir(DEVLANDIA_DIR)
    if env:
        return env

    click.echo("Welcome to devlandia!")
    click.echo("Gathering data on available environments...\n")
    # get a list of all the current images
    tags = dockerutil.image_list(showall=True, print_flag=False, semantic=False)
    # these are the tags we want to look for in the list of images

    # Generate suffixes for each environment that contain information on what image is
    # associated with a tag, and when those images were published

    tag_dict = {}
    for row in tags:
        tag, pushed, human_readable, tag_priority, is_semantic_tag, stable_version = row
        tag_dict[tag] = f"({tag}) published {human_readable}"

    env_choices = [
        {"name": k + " - " + tag_dict[v], "value": k} for k, v in tag_lookup.items()
    ]

    questions = [
        {
            "type": "list",
            "name": "env",
            "message": "What environment would you like to use?",
            "choices": env_choices,
        }
    ]

    env = prompt(questions).get("env")

    if not env:
        echo_highlight("No environment selected.")
        click.get_current_context().abort()

    return env


def activate_snapshot():
    with open(".env", "a") as env_dot:
        env_dot.write("\nJB_SNAPSHOTS_SERVICE=http://snapshot:8080/snapshot/")


@cli.command()
@click.option(
    "--clean",
    default=False,
    help="clean up docker containers (using docker-compose down)",
    is_flag=True,
)
@click.pass_context
def stop(ctx, clean):
    """Stop a running juicebox in this environment"""
    os.chdir(DEVLANDIA_DIR)
    dockerutil.ensure_home()

    if clean:
        dockerutil.destroy()
    elif dockerutil.is_running():
        dockerutil.halt()
        echo_highlight("Juicebox is no longer running.")
    else:
        echo_highlight("Juicebox is not running")


@cli.command()
@click.pass_context
def upgrade(ctx):
    """Attempt to upgrade jb command line"""
    dockerutil.ensure_root()

    try:
        subprocess.check_call(["git", "pull"])
        subprocess.check_call(["pip", "install", "-r", "requirements.txt", "-q"])
    except subprocess.CalledProcessError:
        echo_warning("Failed to `git pull`")
        click.get_current_context().abort()


@cli.command()
def clear_cache():
    """Clears cache"""
    try:
        if dockerutil.is_running():
            dockerutil.run("/venv/bin/python manage.py clear_cache")
        else:
            echo_warning("Juicebox not running.  Run jb start")
            click.get_current_context().abort()
    except docker.errors.APIError:
        echo_warning("Could not clear cache")
        click.get_current_context().abort()


@cli.command()
@click.argument("tag", required=False)
def pull(tag=None):
    """Pulls updates for the image of the environment you're currently in"""
    dockerutil.pull(tag)


@cli.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.option("--env", help="Which environment to use")
def manage(args, env):
    """Run an arbitrary manage.py command in the JB container"""
    cmd = ["/venv/bin/python", "manage.py"] + list(args)
    return _run(cmd, env)


@cli.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.option("--env", help="Which environment to use")
@click.option(
    "--service", help="Which service to run the command in", default="juicebox"
)
def run(args, env, service):
    """Run an arbitrary command in the JB container"""
    return _run(args, env, service)


def _run(args, env, service="juicebox"):
    auth.has_current_session()
    cmd = list(args)
    if env is None:
        env = dockerutil.check_home()

    container = dockerutil.is_running(service=service)
    try:
        if container:
            click.echo("running command in {}".format(container.name))
            # we don't use docker-py for this because it doesn't support the equivalent of
            # "--interactive --tty"
            subprocess.check_call(["docker", "exec", "-it", container.name] + cmd)
        elif env is not None:
            click.echo("starting new {}".format(env))
            os.chdir(DEVLANDIA_DIR)
            dockerutil.run_jb(cmd, env=populate_env_with_secrets(), service=service)
        else:
            echo_warning(
                "Juicebox not running and no --env given. "
                "Please pass --env, or start juicebox in the background first."
            )
            click.get_current_context().abort()
    except subprocess.CalledProcessError as e:
        echo_warning("command exited with {}".format(e.returncode))
        click.get_current_context().abort()


@cli.command()
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.option("--env", help="Which environment to run docker-compose for")
@click.option("--ganesha", default=False, is_flag=True, help="Enable ganesha")
def dc(args, env, ganesha):
    """Run docker-compose in a particular environment"""
    cmd = list(args)
    if env is None:
        env = dockerutil.check_home()
    os.chdir(os.path.join(DEVLANDIA_DIR, "environments", env))
    dockerutil.docker_compose(cmd, ganesha=ganesha)


def activate_hstm():
    with open(".env", "a") as env_dot:
        env_dot.write("\nJB_HSTM=on")
