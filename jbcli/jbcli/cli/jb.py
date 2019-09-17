from __future__ import print_function

import os
import sys
import shutil
import time
from string import join
from multiprocessing import Process

import botocore
import click
import docker.errors
from botocore import exceptions
from PyInquirer import prompt

from ..utils import apps, dockerutil, jbapiutil, subprocess
from ..utils.format import echo_highlight, echo_warning, echo_success, human_readable_timediff
from ..utils.juice_log_searcher import JuiceboxLoggingSearcher
from ..utils.secrets import get_paramstore
from ..utils.reload import create_browser_instance
from ..utils.storageutil import stash

"""
This is the code for the jb cli command.
"""


@click.group()
@click.version_option()
def cli():
    """
    Juicebox CLI app
    """
    pass


@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@cli.command()
def create(*args, **kwargs):
    """ Replaced by yo juicebox
    """
    echo_warning('yo juicebox will take care of all your needs now.')


@cli.command()
@click.argument('applications', nargs=-1, required=True)
@click.option('--bucket', help='Pass the necessary S3 bucket', default=None)
def package(applications, bucket):
    """Package a juicebox app (or list of apps) for deployment
    """
    if dockerutil.is_running() and dockerutil.ensure_home():
        failed_apps = []
        for app in applications:
            try:
                echo_highlight('Packaging {}...'.format(app))
                if bucket is not None:
                    dockerutil.run(
                        '/venv/bin/python manage.py packagejuiceboxapp {} --bucket={}'.format(
                            app, bucket))
                else:
                    dockerutil.run(
                        '/venv/bin/python manage.py packagejuiceboxapp {}'.format(
                            app))

            except docker.errors.APIError:
                print(docker.errors.APIError.message)
                failed_apps.append(app)
        if failed_apps:
            echo_warning(
                'Failed to package: {}.'.format(', '.join(failed_apps)))
            click.get_current_context().abort()
    else:
        echo_warning(
            'Juicebox is not running or you\'re not in a home directory.')
        click.get_current_context().abort()


@cli.command()
@click.argument('datafile', nargs=1, required=True)
@click.option('--app', help='The app to upload data to', required=True)
def upload(datafile, app):
    """Upload data to a juicebox app 
    """
    if dockerutil.is_running() and dockerutil.ensure_home():
        failed_apps = []
        try:
            echo_highlight('Uploading...'.format(app))
            dockerutil.run(
                '/venv/bin/python manage.py upload --app={} {}'.format(
                    app, datafile))

        except docker.errors.APIError:
            print(docker.errors.APIError.message)
            failed_apps.append(app)
    else:
        echo_warning(
            'Juicebox is not running or you\'re not in a home directory.')
        click.get_current_context().abort()


@cli.command()
@click.argument('applications', nargs=-1, required=True)
@click.option('--add-desktop/--no-add-desktop', default=False,
              help='Optionally add to Github Desktop')
def add(applications, add_desktop):
    """Checkout a juicebox app (or list of apps) and load it
    """
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
                            '/venv/bin/python manage.py loadjuiceboxapp {}'.format(
                                app))
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
def clone(existing_app, new_app, init, track):
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
                    '/venv/bin/python manage.py loadjuiceboxapp {}'.format(
                        new_app))
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
def remove(applications):
    """Remove a juicebox app (or list of apps) from your local environment
    """

    try:
        if dockerutil.is_running() and dockerutil.ensure_home():
            failed_apps = []

            for app in applications:
                try:
                    if os.path.isdir('apps/{}'.format(app)):
                        echo_highlight('Removing {}...'.format(app))
                        shutil.rmtree('apps/{}'.format(app))
                        dockerutil.run(
                            '/venv/bin/python manage.py deletejuiceboxapp {}'.format(
                                app))
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


@click.argument('tag', nargs=1, required=True)
@cli.command()
def select(tag):
    """Select tagged image to use
    """
    found = False
    if dockerutil.ensure_test_core():
        tags = dockerutil.image_list(print_flag=False, showall=True)
        for tagset in tags:
            if tag in tagset[0]:

                found = True
                stash.put('jb_select', tag)
                dockerutil.pull(tag)
                with open("./docker-compose.yml", "rt") as dc:
                    with open("out.txt", "wt") as out:
                        for line in dc:
                            if 'juicebox-devlandia:' in line:
                                oldTag = line.rpartition(':')[2]
                                out.write(line.replace(oldTag, tag) + '\"\n')
                            else:
                                out.write(line)
                shutil.move('./out.txt', './docker-compose.yml')

        if not found:
            echo_warning('That tag doesn\'t exist.')
    else:
        echo_warning('This can only be done in the test or core environments.')


@cli.command()
@click.option('--noupdate', default=False,
              help='Do not automatically update Docker image on start',
              is_flag=True)
@click.option('--noupgrade', default=False,
              help='Do not automatically update jb and generators on start',
              is_flag=True)
@click.pass_context
def start(ctx, noupdate, noupgrade):
    """Configure the environment and start Juicebox
    """
    dockerutil.ensure_home()

    if not noupgrade:
        cwd = os.getcwd()
        os.chdir(os.path.join(cwd, '..', '..'))
        ctx.invoke(upgrade)
        os.chdir(cwd)

    if not dockerutil.is_running():
        try:
            if not noupdate:
                dockerutil.pull(tag=None)
            dockerutil.up(env=populate_env_with_secrets())
        except botocore.exceptions.ClientError as e:
            if "Signature expired" in e.message:
                click.echo(
                    "Encountered Signature expired exception.  Attempting to restart Docker, please wait...")
                subprocess.check_call(
                    ['killall', '-HUP' 'com.docker.hyperkit'])
                time.sleep(30)
                start(noupdate=noupdate)
            else:
                raise
    else:
        echo_warning('An instance of Juicebox is already running')


def populate_env_with_secrets():
    env = os.environ.copy()
    env['JB_GOOGLE_CLOUD_PRIVKEY'] = get_paramstore('jbo-google-cloud-privkey')
    env['JB_GITHUB_FETCHAPP_CREDS'] = get_paramstore('opslord-github-credentials')
    return env


@cli.command()
@click.option('--noupdate', default=False,
              help='Do not automatically update Docker image on start',
              is_flag=True)
@click.option('--noupgrade', default=False,
              help='Do not automatically update jb and generators on start',
              is_flag=True)
@click.pass_context
def freshstart(ctx, noupdate, noupgrade):
    """Configure the environment and start Juicebox
    """
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    os.chdir(path)
    click.echo("Welcome to devlandia!")
    click.echo('Gathering data on available environments...\n')
    # get a list of all the current images
    stuff = dockerutil.image_list(print_flag=False, semantic=False)
    # these are the tags we want to look for in the list of images
    interesting_tags = ['develop', 'stable']

    test_tag = stash.get('jb_select')
    if test_tag and test_tag not in interesting_tags:
        interesting_tags.append(test_tag)
        
    # Generate suffixes for each environment that contain information on what image is
    # associated with a tag, and when those images were published
    extra_lookup = {}
    stuff.sort(key=lambda x: x[2])
    for prev_row, row in zip(stuff, stuff[1:]):
        tag = row[0]
        prevtag = prev_row[0]
        readable_timediff = human_readable_timediff(row[2])
        if tag in interesting_tags:
            if tag == 'stable':
                extra_lookup['stable'] = 'stable - ({}) published {}'.format(prevtag, readable_timediff)
            if tag == test_tag:
                extra_lookup['test'] = 'test - ({}) published {} (change this with jb select)'.format(test_tag, readable_timediff)
            if tag == 'develop':
                extra_lookup['dev'] = 'dev - (develop) published {}'.format(readable_timediff)
                extra_lookup['core'] = 'core - (develop) published {}'.format(readable_timediff)
    if 'test' not in extra_lookup:
        extra_lookup['test'] = 'test - set with `jb select`'

    click.echo()

    env_choices = [{'name': extra_lookup.get('stable', 'stable'), 'value': 'stable'},
                   {'name': extra_lookup.get('dev', 'dev'), 'value': 'dev'},
                   {'name': extra_lookup.get('core', 'core'), 'value': 'core'},
                   {'name': extra_lookup.get('test', 'test'), 'value': 'test'},
                   'hstm-stable', 'hstm-dev', 'hstm-core', 'hstm-test']
    questions = [
        {
            'type': 'list',
            'name': 'Environment',
            'message': 'what environment would you like to start?',
            'choices': env_choices
        }
    ]

    response = prompt(questions)
    env = response['Environment']
    click.echo(response)

    if not noupgrade:
        ctx.invoke(upgrade)
        os.chdir("./environments/{}".format(env))
    else:
        os.chdir("./environments/{}".format(env))

    ctx.forward(start)


@cli.command()
@click.pass_context
def stop(ctx):
    """Stop a running juicebox in this environment
    """
    dockerutil.ensure_home()

    if not dockerutil.is_running():
        echo_highlight('Juicebox is not running')
    else:
        dockerutil.halt()
        echo_highlight('Juicebox is no longer running.')


@cli.command()
def yo_upgrade():
    """ Attempt to upgrade yo juicebox to the current version
    """
    dockerutil.ensure_root()
    dockerutil.ensure_virtualenv()

    try:
        # Get the latest generator-juicebox
        output = subprocess.check_call(
            ['npm', 'install', '--package-lock=false', 'generator-juicebox'])
        click.echo(output)
        echo_success('Updated yo juicebox successfully')

        # Ensure the yo-rc.json file exists.
        yo_rc_path = os.path.join(os.getcwd(), '.yo-rc.json')
        if not os.path.exists(yo_rc_path):
            with open(yo_rc_path, 'wb') as f:
                f.write('{}')
        echo_success('Ensured .yo-rc.json exists')

        # Ensure that the yo command line tool is symlinked
        yo_symlink_path = os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'yo')
        npm_yo_path = os.path.join(os.getcwd(), 'node_modules', '.bin', 'yo')
        if sys.platform == 'win32':
            print("The `yo` command is available at {}".format(npm_yo_path))
        else:
            if not os.path.exists(yo_symlink_path):
                print("trying to symlink existing path", npm_yo_path, "to", yo_symlink_path)
                os.symlink(npm_yo_path, yo_symlink_path)
                echo_success('Ensured you can run yo juicebox')
    except subprocess.CalledProcessError:
        echo_warning('Failed to upgrade yo')
        click.get_current_context().abort()


@cli.command()
@click.pass_context
def upgrade(ctx):
    """ Attempt to upgrade jb command line """
    dockerutil.ensure_root()

    try:
        subprocess.check_call(['git', 'pull'])
        subprocess.check_call(['pip', 'install', '-r', 'requirements.txt'])
    except subprocess.CalledProcessError:
        echo_warning('Failed to `git pull`')
        click.get_current_context().abort()


@cli.command()
@click.argument('name')
def test_app(name):
    """ Run gabbi tests against the application. REQUIRES A LOCAL RUNNING COPY
    OF JUICEBOX.
    """
    try:
        if dockerutil.is_running():
            app_dir = 'apps/{}'.format(name)
            dockerutil.run(
                'sh -c "cd {}; pwd; /venv/bin/python -m unittest discover tests"'.format(
                    app_dir))
    except docker.errors.APIError:
        echo_warning('Could not run tests')
        click.get_current_context().abort()


@cli.command()
def clear_cache():
    """Clears cache"""
    try:
        if dockerutil.is_running():
            dockerutil.run(
                '/venv/bin/python manage.py clear_cache --settings=fruition.settings.docker')
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
def manage(args):
    """Allows you to run arbitrary management commands."""
    try:
        if dockerutil.is_running():
            cmdline = ['/venv/bin/python', 'manage.py'] + list(args)
            click.echo('Invoking inside container: %s' % ' '.join(cmdline))
            dockerutil.run(join(cmdline))
        else:
            echo_warning('Juicebox not running.  Run jb start')
            click.get_current_context().abort()
    except docker.errors.APIError:
        echo_warning('Could not clear cache')
        click.get_current_context().abort()


@cli.command()
@click.option(
    '--username',
    required=True,
    envvar='LP_USERNAME',
    help=
    'Username for lp.juiceboxdata.com, must be passed or defined in '
    'environment variable LP_USERNAME for core environments and '
    'HSL_USERNAME for hstm environments'
)
@click.option(
    '--password',
    required=True,
    envvar='LP_PASSWORD',
    help=
    'Password for lp.juiceboxdata.com, must be passed or defined in '
    'environment variable LP_PASSWORD for core environments and '
    'HSL_PASSWORD for hstm environments'
)
@click.option(
    '--env',
    prompt='Environment',
    default='legacy-prod',
    type=click.Choice(
        ['legacy-staging', 'legacy-prod', 'prod', 'hstm-qa', 'hstm-prod']),
    help='Environment to search, one of dev, staging, prod')
@click.option(
    '--data_service_log',
    prompt='Log type',
    type=click.Choice(['performance', 'params', 'recipe']),
    default='performance',
    help='Data service log type, one of performance, params, recipe')
@click.option(
    '--lookback_window',
    prompt='Number of days',
    default=10,
    help='Number of days to look at')
@click.option(
    '--limit', prompt='Limit', default=100, help='Number of records to return')
@click.option(
    '--service_pattern',
    prompt='Service pattern regular expression',
    default='.*',
    help='Data service regex to filter on')
@click.option(
    '--user_pattern',
    prompt='User regular expression',
    default='.*',
    help='User regex to filter on')
@click.option(
    '--output',
    prompt='A filename to write the output to',
    default='',
    help='A filename to write the output to')
def search(username, password, env, data_service_log,
           lookback_window, limit, service_pattern, user_pattern,
           output):
    """Query elasticsearch and show results

    Environment variables LP_USERNAME and LP_PASSWORD must be set.
    For healthstream account HSL_USERNAME and HSL_PASSWORD must be set.
    """
    if not username or not password:
        print("Logging proxy username and password must be defined")

    params = {
        'username': username,
        'password': password,
        'env': env,
        'data_service_log': data_service_log,
        'lookback_window': lookback_window,
        'limit': limit,
        'service_pattern': service_pattern,
        'user_pattern': user_pattern
    }
    dataset = JuiceboxLoggingSearcher().dataset(**params)

    print(
        'Running\njb search --env {env} --data_service_log {data_service_log} '
        '--lookback_window {lookback_window} --limit {limit} '
        '--service_pattern "{service_pattern}" '
        '--user_pattern "{user_pattern}" --output "{output}"\n\n'
            .format(output=output, **params))

    if output:
        print('Writing {}'.format(output))
        with open(output, 'w') as outf:
            outf.write(dataset.tsv)
    else:
        print(dataset.tsv)

    if lookback_window > 90:
        print("There is only 90 days of history retained")
