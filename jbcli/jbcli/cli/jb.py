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
from multiprocessing import Process
from subprocess import Popen

import click
import docker.errors
from collections import OrderedDict
from PyInquirer import prompt, Separator
from six.moves.urllib.parse import urlparse, urlunparse
import yaml

from ..utils import apps, dockerutil, jbapiutil, subprocess, auth
from ..utils.format import echo_highlight, echo_warning, echo_success
from ..utils.secrets import get_deployment_secrets
from ..utils.reload import create_browser_instance


MY_DIR = os.path.abspath(os.path.dirname(__file__))
DEVLANDIA_DIR = os.path.abspath(os.path.join(MY_DIR, '..', '..', '..'))
JBCLI_DIR = os.path.abspath(os.path.join(DEVLANDIA_DIR, 'jbcli'))

def normalize(name):
    return name.replace("_","-")

@click.group(context_settings={"token_normalize_func": normalize})
@click.version_option()
def cli():
    """
    Juicebox CLI app
    """
    pass

@cli.command()
@click.argument('applications', nargs=-1, required=True)
@click.option('--add-desktop/--no-add-desktop', default=False,
              help='Optionally add to Github Desktop')
@click.option('--runtime', default='venv', help='Which runtime to use, defaults to venv, the only other option is venv3')
def add(applications, add_desktop, runtime):
    """Checkout a juicebox app (or list of apps) and load it
    """
    os.chdir(DEVLANDIA_DIR)
    try:
        if dockerutil.is_running():
            failed_apps = []

            for app in applications:
                app_dir = 'apps/{}'.format(app)
                if os.path.isdir(app_dir):
                    # App already exists, update it.
                    echo_highlight('App {} already exists.'.format(app))

                else:
                    # App doesn't exist, clone it
                    echo_highlight('Adding {}...'.format(app))
                    echo_highlight(
                        'Downloading app {} from Github.'.format(app))
                    github_repo_url = apps.make_github_repo_url(app)

                    try:
                        subprocess.check_call(['git', 'clone', github_repo_url,
                                               app_dir])
                    except subprocess.CalledProcessError:
                        failed_apps.append(app)
                        continue

                    if add_desktop:
                        try:
                            subprocess.check_call(['github', app_dir])
                        except subprocess.CalledProcessError:
                            echo_warning(
                                'Failed to add {} to Github Desktop.'.format(
                                    app))
                try:
                    if not jbapiutil.load_app(app):
                        dockerutil.run(
                            '/{}/bin/python manage.py loadjuiceboxapp {}'.format(
                                runtime, app))
                        echo_success('{} was added successfully.'.format(app))

                except docker.errors.APIError as e:
                    echo_warning(
                        'Failed to add {} to the Juicebox VM.'.format(app))
                    failed_apps.append(app)
                    print(e.explanation)

            if failed_apps:
                click.echo()
                echo_warning(
                    'Failed to load: {}.'.format(', '.join(failed_apps)))
                click.get_current_context().abort()
        else:
            echo_warning('Juicebox is not running.  Please run jb start.')
            click.get_current_context().abort()
    except docker.errors.APIError as de:
        echo_warning(de.message)


@cli.command()
@click.argument('existing_app', required=True)
@click.argument('new_app', required=True)
@click.option('--init/--no-init', default=True,
              help='Initialize VCS repository')
@click.option('--track/--no-track', default=True,
              help='Track remote VCS repository')
@click.option('--runtime', help='Which runtime to use, defaults to venv, the only other option is venv3', default='venv')
def clone(existing_app, new_app, init, track, runtime):
    """ Clones an existing application to a new one. Make sure you have a
    Github repo setup for the new app.
    """
    try:
        if dockerutil.is_running():
            existing_app_dir = 'apps/{}'.format(existing_app)
            new_app_dir = 'apps/{}'.format(new_app)

            if not os.path.isdir(existing_app_dir):
                echo_warning('App {} does not exist.'.format(existing_app))
                click.get_current_context().abort()
            if os.path.isdir(new_app_dir):
                echo_warning('App {} already exists.'.format(new_app))
                click.get_current_context().abort()

            echo_highlight('Cloning from {} to {}...'.format(existing_app,
                                                             new_app))

            try:
                result = apps.clone(new_app, existing_app_dir, new_app_dir,
                                    init_vcs=init, track_vcs=track)
            except (OSError, ValueError):
                echo_warning('Cloning failed')
                click.get_current_context().abort()
            if not result:
                click.get_current_context().abort()

            try:
                dockerutil.run(
                    '/{}/bin/python manage.py loadjuiceboxapp {}'.format(
                        runtime, new_app))
            except docker.errors.APIError:
                echo_warning('Failed to load: {}.'.format(new_app))
                click.get_current_context().abort()
        else:
            echo_warning('Juicebox is not running.  Run jb start.')
            click.get_current_context().abort()
    except docker.errors.APIError as de:
        echo_warning(de.message)


@cli.command()
@click.argument('applications', nargs=-1, required=True)
@click.confirmation_option('--yes', is_flag=True,
                           prompt='Are you sure you want to delete?')
@click.option('--runtime', help='Which runtime to use, defaults to venv, the only other option is venv3'
                                'option.', default='venv')
def remove(applications, runtime):
    """Remove a juicebox app (or list of apps) from your local environment
    """
    os.chdir(DEVLANDIA_DIR)
    try:
        if dockerutil.is_running() and dockerutil.ensure_home():
            failed_apps = []

            for app in applications:
                try:
                    if os.path.isdir('apps/{}'.format(app)):
                        echo_highlight('Removing {}...'.format(app))
                        shutil.rmtree('apps/{}'.format(app))
                        dockerutil.run(
                            '/{}/bin/python manage.py deletejuiceboxapp {}'.format(
                                runtime, app))
                        echo_success('Successfully deleted {}'.format(app))
                    else:
                        echo_warning('App {} didn\'t exist.'.format(app))
                except docker.errors.APIError:
                    print(docker.errors.APIError.message)
                    failed_apps.append(app)
            if failed_apps:
                click.echo()
                echo_warning(
                    'Failed to remove: {}.'.format(', '.join(failed_apps)))
                click.get_current_context().abort()
        else:
            echo_warning('Juicebox is not running.  Run jb start.')
            click.get_current_context().abort()
    except docker.errors.APIError:
        click.echo()
        echo_warning('Juicebox is not running.  Run jb start.')
        click.get_current_context().abort()


@click.option('--includejs', default=False, help='Watch for js changes',
              is_flag=True)
@click.option('--app', default='', help='Watch a specific app.')
@click.option('--reload', default=False, help='Refresh browser after file changes.',
              is_flag=True)
@cli.command()
def watch(includejs=False, app='', reload=False):
    """ Watch for changes in apps and js and reload/rebuild"""
    procs = []
    jb_watch_proc = Process(target=dockerutil.jb_watch, kwargs={'app': app, 'should_reload': reload})
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


@click.option('--showall', default=False, help='Show all tagged images',
              is_flag=True)
@click.option('--semantic', default=False, help='Show all semantic versions.',
              is_flag=True)
@cli.command()
def ls(showall=False, semantic=False):
    """List available containers
    """
    try:
        echo_success('The following tagged images are available:')
        dockerutil.image_list(showall=showall, semantic=semantic)
    except subprocess.CalledProcessError:
        echo_warning('You must login to the registry first.')

def populate_env_with_secrets():
    env = get_deployment_secrets()
    env.update(os.environ)
    return env


def cleanup_ssh(env):
    compose_fn = os.path.join(DEVLANDIA_DIR, 'docker-compose-ssh.yml')
    try:
        os.remove(compose_fn)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def get_host_ip():
    # On linux, `host.docker.internal` doesn't work,
    # but we have a nice way to find the address w/ the docker0 interface.
    try:
        ifname = b'docker0'
        SIOCGIFADDR = 0x8915
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        interface = struct.pack('256s', ifname[:15])
        addr = fcntl.ioctl(s.fileno(), SIOCGIFADDR, interface)[20:24]
        return socket.inet_ntoa(addr)
    except Exception as e:
        print("[get_host_ip] Couldn't get docker0 address, falling back to slow method", e)
        out = dockerutil.client.containers.run(
            'ubuntu:18.04', 'getent hosts host.docker.internal')
        # returns output like:
        #   192.168.1.1    host.docker.internal
        #   192.168.1.2    host.docker.internal
        return out.splitlines()[0].split()[0].decode('ascii')


def activate_ssh(env, environ):
    """
    Start the SSH tunnels, and manipulate the environment variables so that
    they are pointing at the right ports.
    """

    redshifts = {}
    # these local ports are arbitrary
    for envvar, localport in [
        ("JB_REDSHIFT_CONNECTION", 5439),
        ("JB_HSTM_REDSHIFT_CONNECTION", 5438),
        ("JB_MANAGED_REDSHIFT_CONNECTION", 5437),
        ("JB_PREVERITY_REDSHIFT_CONNECTION", 5436)
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
        "ssh", "-T", "-N",
        "-o", "ServerAliveInterval 30", "-o", "ServerAliveCountMax 3", "-o", "StrictHostKeyChecking=accept-new",
        *ssh_links,
        "vpn2.juiceboxdata.com"
    ]
    process = Popen(command)

    def cleanup():
        process.kill()
        print("waiting for SSH tunnels to stop...")
        while process.poll() is None:
            time.sleep(0.2)
        print("exit status:", process.poll())
        cleanup_ssh(env)

    atexit.register(cleanup)

    compose_fn = os.path.join(DEVLANDIA_DIR, 'docker-compose-ssh.yml')
    host_addr = get_host_ip()
    content = {
        'version': '3.2',
        'services': {
            'juicebox': {
                'extra_hosts': [
                    f"{url.hostname}:{host_addr}"
                    for (url, _, _) in redshifts.values()
                ],
                # We want to make sure that the environment variables we're going to set
                # will be passed through to the container.
                "environment": list(redshifts.keys()),
            }
        }
    }
    with open(compose_fn, 'w') as compose_file:
        compose_file.write(yaml.safe_dump(content))
    # We *could* just write the new connection strings into the YAML content above,
    # but that would mean leaving secrets around on disk, so we'll just put them into
    # the environment instead:
    return {
        envvar: new_conn_string
        for (envvar, (_, _, new_conn_string)) in redshifts.items()
    }


@cli.command()
@click.argument('env', nargs=1, required=False)
@click.option('--noupdate', default=False,
              help='Do not automatically update Docker image on start',
              is_flag=True)
@click.option('--noupgrade', default=False,
              help='Do not automatically update jb and generators on start',
              is_flag=True)
@click.option('--ssh', default=False, is_flag=True,
              help='run an SSH tunnel for redshift')
@click.option("--ganesha", default=False, is_flag=True,
              help="Enable ganesha")
@click.option("--hstm", default=False, is_flag=True,
              help="Enable hstm")
@click.option("--core", default=False, is_flag=True,
              help="Use local fruition checkout with this image (core and hstm-core environments do this automatically)")
@click.option("--dev-recipe", default=False, is_flag=True,
              help="Use local recipe checkout, requires running a core environment")
@click.pass_context
def start(ctx, env, noupdate, noupgrade, ssh, ganesha, hstm, core, dev_recipe):
    """Configure the environment and start Juicebox"""
    if dockerutil.is_running():
        echo_warning('An instance of Juicebox is already running')
        echo_warning('Run `jb stop` to stop this instance.')
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
            print("Could not find Local Fruition Checkout, please check that it is symlinked to the top level of Devlandia")
            sys.exit(1)

    # "dev_recipe" devlandia uses editable recipe code
    if dev_recipe:
        if is_core:
            if os.path.exists("recipe"):
                recipe_path = "recipe"
                recipe_end = "code/recipe"
            else:
                print("Could not find local recipe checkout, please check that it is symlinked to the top level of Devlandia")
                sys.exit(1)
        else:
            print("The dev-recipe flag requires running a core environment")
            sys.exit(1)

    # Replace the enviroment with the tagged Juicebox image
    # that is running in that environment
    if env in tag_replacements.keys():
        tag = tag_replacements[env]
    else:
        tag = env

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
    if is_hstm:
        activate_hstm()
        print("Activating HSTM")
    cleanup_ssh(env)
    if ssh:
        environ.update(activate_ssh(env, environ))
    dockerutil.up(env=environ, ganesha=ganesha)


def get_environment_interactively(env, tag_lookup):

    os.chdir(DEVLANDIA_DIR)
    if env:
        return env

    click.echo("Welcome to devlandia!")
    click.echo('Gathering data on available environments...\n')
    # get a list of all the current images
    tags = dockerutil.image_list(showall=True, print_flag=False, semantic=False)
    # these are the tags we want to look for in the list of images

    # Generate suffixes for each environment that contain information on what image is
    # associated with a tag, and when those images were published

    tag_dict = {}
    for row in tags:
        tag, pushed, human_readable, tag_priority, is_semantic_tag, stable_version = row
        tag_dict[tag] = f"({tag}) published {human_readable}"

    env_choices = []
    for k, v in tag_lookup.items():
        env_choices.append({'name': k + " - " + tag_dict[v], 'value': k})

    questions = [
        {
            'type': 'list',
            'name': 'env',
            'message': 'What environment would you like to use?',
            'choices': env_choices
        }
    ]

    env = prompt(questions).get('env')

    if not env:
        echo_highlight('No environment selected.')
        click.get_current_context().abort()

    return env


@cli.command()
@click.option('--clean', default=False, help='clean up docker containers (using docker-compose down)',
              is_flag=True)
@click.option('--env', help='Which environment to use')
@click.pass_context
def stop(ctx, clean, env):
    """Stop a running juicebox in this environment
    """
    os.chdir(DEVLANDIA_DIR)
    dockerutil.ensure_home()

    if clean:
        dockerutil.destroy()
    elif dockerutil.is_running():
        dockerutil.halt()
        echo_highlight('Juicebox is no longer running.')
    else:
        echo_highlight('Juicebox is not running')


@cli.command()
@click.pass_context
def upgrade(ctx):
    """ Attempt to upgrade jb command line """
    dockerutil.ensure_root()

    try:
        subprocess.check_call(['git', 'pull'])
        subprocess.check_call(['pip', 'install', '-r', 'requirements.txt', '-q'])
    except subprocess.CalledProcessError:
        echo_warning('Failed to `git pull`')
        click.get_current_context().abort()


@cli.command()
@click.option('--runtime', default='venv', help='Which runtime to use, defaults to venv, the only other option is venv3')
def clear_cache(runtime):
    """Clears cache"""
    try:
        if dockerutil.is_running():
            dockerutil.run(
                '/{}/bin/python manage.py clear_cache'.format(runtime))
        else:
            echo_warning('Juicebox not running.  Run jb start')
            click.get_current_context().abort()
    except docker.errors.APIError:
        echo_warning('Could not clear cache')
        click.get_current_context().abort()


@cli.command()
@click.argument('tag', required=False)
def pull(tag=None):
    """ Pulls updates for the image of the environment you're currently in
    """
    dockerutil.pull(tag)


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.option('--env', help='Which environment to use')
def manage(args, env):
    """Run an arbitrary manage.py command in the JB container"""
    cmd = ['/venv/bin/python', 'manage.py'] + list(args)
    return _run(cmd, env)


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.option('--env', help='Which environment to use')
@click.option('--service', help='Which service to run the command in', default='juicebox')
def run(args, env, service):
    """Run an arbitrary command in the JB container"""
    return _run(args, env, service)


def _run(args, env, service='juicebox'):
    cmd = list(args)
    if env is None:
        env = dockerutil.check_home()

    container = dockerutil.is_running(service=service)
    try:
        if container:
            click.echo("running command in {}".format(container.name))
            # we don't use docker-py for this because it doesn't support the equivalent of
            # "--interactive --tty"
            subprocess.check_call(['docker', 'exec', '-it', container.name] + cmd)
        elif env is not None:
            click.echo("starting new {}".format(env))
            os.chdir(DEVLANDIA_DIR)
            dockerutil.run_jb(cmd, env=populate_env_with_secrets(), service=service)
        else:
            echo_warning(
                "Juicebox not running and no --env given. "
                "Please pass --env, or start juicebox in the background first.")
            click.get_current_context().abort()
    except subprocess.CalledProcessError as e:
        echo_warning("command exited with {}".format(e.returncode))
        click.get_current_context().abort()


@cli.command()
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.option("--env", help="Which environment to run docker-compose for")
@click.option("--ganesha", default=False, is_flag=True, help="Enable ganesha")
def dc(args, env, ganesha):
    """Run docker-compose in a particular environment"""
    cmd = list(args)
    if env is None:
        env = dockerutil.check_home()
    os.chdir(os.path.join(DEVLANDIA_DIR, 'environments', env))
    dockerutil.docker_compose(cmd, ganesha=ganesha)

def activate_hstm():
    os.environ['AWS_PROFILE'] = 'hstm'
    env_dot = open(".env", "a")
    env_dot.write(f"\nJB_HSTM=on")
    env_dot.close()
