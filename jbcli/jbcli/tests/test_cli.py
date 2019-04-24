from __future__ import print_function

import sys
from subprocess import CalledProcessError

from click.testing import CliRunner
from docker.errors import APIError
from mock import call, patch, Mock
from watchdog.events import FileSystemEventHandler

import jbcli
from ..cli.jb import cli
from ..utils.dockerutil import WatchHandler


class TestDocker:
    def test_base(self):
        runner = CliRunner()
        result = runner.invoke(cli)

        assert 'Juicebox CLI app' in result.output
        assert result.exit_code == 0

    def test_bad_command(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['cookies'])

        assert result.exit_code == 2
        assert 'No such command "cookies"' in result.output

    @patch('jbcli.cli.jb.apps')
    def test_create_full(self, app_mock):
        runner = CliRunner()
        result = runner.invoke(cli, ['create', 'cookies'])
        assert app_mock.mock_calls == []
        assert result.output == 'yo juicebox will take care of all your needs now.\n'
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_package_single(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        runner = CliRunner()
        result = runner.invoke(cli, ['package', 'cookies'])

        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv/bin/python manage.py packagejuiceboxapp cookies')
        ]
        assert 'Packaging cookies' in result.output
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_package_to_bucket(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        runner = CliRunner()
        result = runner.invoke(cli, ['package', 'cookies', '--bucket', 'test_bucket'])

        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv/bin/python manage.py packagejuiceboxapp cookies --bucket=test_bucket')
        ]
        assert 'Packaging cookies' in result.output
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_package_not_running(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False
        runner = CliRunner()
        result = runner.invoke(cli, ['package', 'cookies'])
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert 'Juicebox is not running or you\'re not in a home directory.' in result.output
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    def test_package_multiple(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        runner = CliRunner()
        result = runner.invoke(cli, ['package', 'cookies', 'chocolate_chip'])

        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv/bin/python manage.py packagejuiceboxapp cookies'),
            call.run('/venv/bin/python manage.py packagejuiceboxapp chocolate_chip')
        ]
        assert 'Packaging cookies' in result.output
        assert 'Packaging chocolate_chip' in result.output
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_package_fail(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        dockerutil_mock.run.side_effect = APIError('Fail')
        runner = CliRunner()
        result = runner.invoke(cli, ['package', 'cookies'])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv/bin/python manage.py packagejuiceboxapp cookies')
        ]

        assert 'Packaging cookies...' in result.output
        assert 'Failed to package: cookies.' in result.output

        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess')
    @patch('jbcli.cli.jb.os')
    def test_add_single(self, os_mock, proc_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = 'git cookies'

        runner = CliRunner()
        result = runner.invoke(cli, ['add', 'cookies'])

        assert 'Adding cookies...' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv/bin/python manage.py loadjuiceboxapp cookies')
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u'cookies')]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]
        assert proc_mock.mock_calls == [
            call.check_call(['git', 'clone', 'git cookies', 'apps/cookies'])
        ]
        assert 'Adding cookies' in result.output

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.os')
    def test_add_app_exists(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = True

        runner = CliRunner()
        result = runner.invoke(cli, ['add', 'cookies'])

        assert 'App cookies already exists.' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv/bin/python manage.py loadjuiceboxapp cookies')
        ]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]

    @patch('jbcli.cli.jb.dockerutil')
    def test_add_not_running(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False

        runner = CliRunner()
        result = runner.invoke(cli, ['add', 'cookies'])

        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert 'Juicebox is not running.  Please run jb start.' in result.output
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess')
    @patch('jbcli.cli.jb.os')
    def test_add_desktop(self, os_mock, proc_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        dockerutil_mock.is_running.return_value = True
        runner = CliRunner()
        result = runner.invoke(cli, ['add', 'cookies', '--add-desktop'])

        assert 'Adding cookies...' in result.output
        assert 'Downloading app cookies from Github.' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv/bin/python manage.py loadjuiceboxapp cookies')
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u'cookies')]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]
        assert proc_mock.mock_calls == [
            call.check_call(['git', 'clone', 'git cookies', 'apps/cookies']),
            call.check_call(['github', 'apps/cookies'])
        ]

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess')
    @patch('jbcli.cli.jb.os')
    def test_add_multiple(self, os_mock, proc_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        dockerutil_mock.is_running.return_value = True
        runner = CliRunner()
        result = runner.invoke(cli, ['add', 'cookies', 'chocolate_chip'])

        assert 'Adding cookies...' in result.output
        assert 'Adding chocolate_chip'
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv/bin/python manage.py loadjuiceboxapp cookies'),
            call.run('/venv/bin/python manage.py loadjuiceboxapp chocolate_chip')
        ]
        assert apps_mock.mock_calls == [
            call.make_github_repo_url(u'cookies'),
            call.make_github_repo_url(u'chocolate_chip')
        ]
        assert os_mock.mock_calls == [
            call.path.isdir('apps/cookies'),
            call.path.isdir('apps/chocolate_chip')
        ]
        assert proc_mock.mock_calls == [
            call.check_call(['git', 'clone', 'git cookies', 'apps/cookies']),
            call.check_call(['git', 'clone', 'git cookies', 'apps/chocolate_chip']),
        ]

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess.check_call')
    @patch('jbcli.cli.jb.os')
    def test_add_clone_fail(self, os_mock, proc_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        proc_mock.side_effect = CalledProcessError(2, 'cmd', 'Ugh Cake')

        runner = CliRunner()
        result = runner.invoke(cli, ['add', 'cookies'])

        assert 'Adding cookies...' in result.output
        assert 'Failed to load: cookies.' in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u'cookies')]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]
        assert proc_mock.mock_calls == [
            call.check_call(['git', 'clone', 'git cookies', 'apps/cookies'])
        ]

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess.check_call')
    @patch('jbcli.cli.jb.os')
    def test_add_run_fail(self, os_mock, proc_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.run.side_effect = APIError('Fail')
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = 'git cookies'

        runner = CliRunner()
        result = runner.invoke(cli, ['add', 'cookies'])

        assert 'Adding cookies...' in result.output
        assert 'Downloading app cookies from Github.' in result.output
        assert 'Failed to add cookies to the Juicebox VM' in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv/bin/python manage.py loadjuiceboxapp cookies')
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u'cookies')]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]
        assert proc_mock.mock_calls == [
            call.check_call(['git', 'clone', 'git cookies', 'apps/cookies'])
        ]

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess.check_call')
    @patch('jbcli.cli.jb.os')
    def test_add_desktop_fail(self, os_mock, proc_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        proc_mock.side_effect = [
            True, CalledProcessError(2, 'cmd', 'Ugh Cake')
        ]

        runner = CliRunner()
        result = runner.invoke(cli, ['add', 'cookies', '--add-desktop'])
        assert 'Adding cookies...' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv/bin/python manage.py loadjuiceboxapp cookies')
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u'cookies')]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]
        assert proc_mock.mock_calls == [
            call(['git', 'clone', 'git cookies', 'apps/cookies']),
            call(['github', 'apps/cookies'])
        ]
        assert 'Failed to add cookies to Github Desktop' in result.output
        assert 'Downloading app cookies from Github' in result.output
        assert 'cookies was added successfully' in result.output

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.shutil')
    @patch('jbcli.cli.jb.os')
    def test_remove_single(self, os_mock, shutil_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True

        runner = CliRunner()
        result = runner.invoke(cli, ['remove', 'cookies', '--yes'])

        assert 'Removing cookies...' in result.output
        assert 'Successfully deleted cookies' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv/bin/python manage.py deletejuiceboxapp cookies')
        ]
        assert shutil_mock.mock_calls == [call.rmtree('apps/cookies')]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]

    @patch('jbcli.cli.jb.dockerutil')
    def test_remove_not_running(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False

        runner = CliRunner()
        result = runner.invoke(cli, ['remove', 'cookies', '--yes'])

        assert 'Juicebox is not running.  Run jb start.' in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
        ]
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    def test_remove_not_home(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = False

        runner = CliRunner()
        result = runner.invoke(cli, ['remove', 'cookies', '--yes'])

        assert 'Juicebox is not running.  Run jb start.' in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home()
        ]
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.shutil')
    @patch('jbcli.cli.jb.os')
    def test_remove_multiple(self, os_mock, shutil_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True

        runner = CliRunner()
        result = runner.invoke(cli, ['remove', 'cookies', 'cake', '--yes'])

        assert 'Removing cookies...' in result.output
        assert 'Removing cake...' in result.output
        assert 'Successfully deleted cookies' in result.output
        assert 'Successfully deleted cake' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv/bin/python manage.py deletejuiceboxapp cookies'),
            call.run('/venv/bin/python manage.py deletejuiceboxapp cake')
        ]
        assert shutil_mock.mock_calls == [
            call.rmtree('apps/cookies'),
            call.rmtree('apps/cake')
        ]
        assert os_mock.mock_calls == [
            call.path.isdir('apps/cookies'),
            call.path.isdir('apps/cake')
        ]

    @patch('jbcli.cli.jb.Process')
    @patch('jbcli.cli.jb.time')
    @patch('jbcli.cli.jb.dockerutil')
    def test_watch(self, dockerutil_mock, time_mock, process_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        runner = CliRunner()
        result = runner.invoke(cli, ['watch'])

        assert process_mock.mock_calls == [
            call(target=dockerutil_mock.jb_watch, kwargs={'app': ''}),
            call().start(),
            call().join()
        ]

        assert result.exit_code == 0

    @patch('jbcli.cli.jb.Process')
    @patch('jbcli.cli.jb.time')
    @patch('jbcli.cli.jb.dockerutil')
    def test_watch_for_specific_app(self, dockerutil_mock, time_mock, process_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        runner = CliRunner()
        result = runner.invoke(cli, ['watch', '--app', 'test'])

        assert process_mock.mock_calls == [
            call(target=dockerutil_mock.jb_watch, kwargs={'app': 'test'}),
            call().start(),
            call().join()
        ]

        assert result.exit_code == 0

    @patch('jbcli.cli.jb.Process')
    @patch('jbcli.cli.jb.time')
    @patch('jbcli.cli.jb.dockerutil')
    def test_watch_full(self, dockerutil_mock, time_mock, process_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        runner = CliRunner()
        result = runner.invoke(cli, ['watch', '--includejs'])

        assert process_mock.mock_calls == [
            call(target=dockerutil_mock.jb_watch, kwargs={'app': ''}),
            call().start(),
            call(target=dockerutil_mock.js_watch),
            call().start(),
            call().join(),
            call().join()
        ]

        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_stop(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        dockerutil_mock.halt.return_value = None
        runner = CliRunner()
        result = runner.invoke(cli, ['stop'])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.ensure_home(),
            call.is_running(),
            call.halt()
        ]

    @patch('jbcli.cli.jb.dockerutil')
    def test_start(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        runner = CliRunner()
        result = runner.invoke(cli, ['start', '--noupgrade'])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.ensure_home(),
            call.is_running(),
            call.pull(tag=None),
            call.up()
        ]

    @patch('jbcli.cli.jb.dockerutil')
    def test_start_noupgrade(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        runner = CliRunner()
        result = runner.invoke(cli, ['start', '--noupgrade'])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.ensure_home(),
            call.is_running(),
            call.pull(tag=None),
            call.up()
        ]

    @patch('jbcli.cli.jb.dockerutil')
    def test_start_noupdate(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        runner = CliRunner()
        result = runner.invoke(cli, ['start', '--noupdate', '--noupgrade'])
        assert dockerutil_mock.mock_calls == [
            call.ensure_home(),
            call.is_running(),
            call.up()
        ]
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_start_already_running(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        runner = CliRunner()
        result = runner.invoke(cli, ['start', '--noupgrade'])

        assert 'An instance of Juicebox is already running' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.ensure_home(),
            call.is_running()
        ]

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.os')
    def test_clone(self, os_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.side_effect = [True, False]
        apps_mock.clone.return_value = 'git cookies'
        dockerutil_mock.is_running.return_value = True
        runner = CliRunner()
        result = runner.invoke(cli, ['clone', 'cookies', 'chocolate_chip'])

        assert apps_mock.mock_calls == [
            call.clone(u'chocolate_chip', 'apps/cookies',
                       'apps/chocolate_chip', init_vcs=True, track_vcs=True)
        ]
        assert os_mock.mock_calls == [
            call.path.isdir('apps/cookies'),
            call.path.isdir('apps/chocolate_chip')
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv/bin/python manage.py loadjuiceboxapp chocolate_chip')
        ]
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_clone_running_fail(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False

        runner = CliRunner()
        result = runner.invoke(cli, ['clone', 'cookies', 'chocolate_chip'])

        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert result.exit_code == 1
        assert 'Juicebox is not running.  Run jb start.' in result.output

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.os')
    def test_clone_from_nonexist(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        runner = CliRunner()
        result = runner.invoke(cli, ['clone', 'cookies', 'chocolate_chip'])

        assert os_mock.mock_calls == [
            call.path.isdir('apps/cookies'),
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
        ]
        assert result.exit_code == 1
        assert 'App cookies does not exist.' in result.output

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.os')
    def test_clone_to_exists(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.side_effect = [True, True]
        dockerutil_mock.is_running.return_value = True

        runner = CliRunner()
        result = runner.invoke(cli, ['clone', 'cookies', 'chocolate_chip'])

        assert os_mock.mock_calls == [
            call.path.isdir('apps/cookies'),
            call.path.isdir('apps/chocolate_chip')
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert result.exit_code == 1
        assert 'App chocolate_chip already exists.' in result.output

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.os')
    def test_clone_failed(self, os_mock, apps_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        os_mock.path.isdir.side_effect = [True, False]
        apps_mock.clone.side_effect = ValueError('Cake Bad')

        runner = CliRunner()
        result = runner.invoke(cli, ['clone', 'cookies', 'chocolate_chip'])

        assert apps_mock.mock_calls == [
            call.clone(u'chocolate_chip', 'apps/cookies',
                       'apps/chocolate_chip', init_vcs=True, track_vcs=True)
        ]
        assert os_mock.mock_calls == [
            call.path.isdir('apps/cookies'),
            call.path.isdir('apps/chocolate_chip')
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
        ]
        assert result.exit_code == 1
        assert 'Cloning failed' in result.output

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.os')
    def test_clone_run_failed(self, os_mock, apps_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        apps_mock.clone.return_value = True
        os_mock.path.isdir.side_effect = [True, False]

        runner = CliRunner()
        result = runner.invoke(cli, ['clone', 'cookies', 'chocolate_chip'])

        assert apps_mock.mock_calls == [
            call.clone(u'chocolate_chip', 'apps/cookies',
                       'apps/chocolate_chip', init_vcs=True, track_vcs=True)
        ]
        assert os_mock.mock_calls == [
            call.path.isdir('apps/cookies'),
            call.path.isdir('apps/chocolate_chip')
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv/bin/python manage.py loadjuiceboxapp chocolate_chip')
        ]
        assert 'Cloning from cookies to chocolate_chip' in result.output

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.subprocess')
    @patch('jbcli.cli.jb.os')
    def test_yo_upgrade(self, os_mock, proc_mock, dockerutil_mock):
        dockerutil_mock.ensure_root.return_value = True
        dockerutil_mock.ensure_virtualenv.return_value = True
        os_mock.environ.return_value = False
        os_mock.path.join.return_value = ''
        os_mock.getcwd.return_value = ''
        os_mock.path.exists.return_value = False
        os_mock.symlink.return_value = False

        runner = CliRunner()
        result = runner.invoke(cli, ['yo_upgrade'])

        # TODO: Improve these tests
        assert proc_mock.mock_calls == [
            call.check_call(['npm', 'install', '--package-lock=false', 'generator-juicebox']),
            call.check_call().__unicode__()
        ]
        # assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_test_app(self, dockerutil_mock):
        runner = CliRunner()
        dockerutil_mock.is_running.return_value = True
        result = runner.invoke(cli, ['test_app', 'jb3demo'])
        assert dockerutil_mock.mock_calls == [call.is_running(),
                                              call.run(
                                                  'sh -c "cd apps/jb3demo; pwd; /venv/bin/python -m unittest discover tests"')]

        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_test_app_fail(self, dockerutil_mock):
        runner = CliRunner()
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.run.side_effect = APIError('Fail')
        result = runner.invoke(cli, ['test_app', 'jb3demo'])
        assert dockerutil_mock.mock_calls == [call.is_running(),
                                              call.run(
                                                  'sh -c "cd apps/jb3demo; pwd; /venv/bin/python -m unittest discover tests"')]

        assert 'Could not run tests' in result.output
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    def test_clear_cache(self, dockerutil_mock):
        runner = CliRunner()
        dockerutil_mock.is_running.return_value = True

        result = runner.invoke(cli, ['clear_cache'])
        assert dockerutil_mock.mock_calls == [call.is_running(),
                                              call.run('/venv/bin/python manage.py clear_cache '
                                                       '--settings=fruition.settings.docker')]

        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_clear_cache_not_running(self, dockerutil_mock):
        runner = CliRunner()
        dockerutil_mock.is_running.return_value = False

        result = runner.invoke(cli, ['clear_cache'])
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    def test_jb_pull(self, dockerutil_mock):
        runner = CliRunner()

        result = runner.invoke(cli, ['pull'])
        assert dockerutil_mock.mock_calls == [
            call.pull(None)
        ]
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.click')
    @patch('jbcli.cli.jb.dockerutil')
    def test_clear_cache_fail(self, dockerutil_mock, click_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.run.side_effect = APIError('Failure')
        runner = CliRunner()
        result = runner.invoke(cli, ['clear_cache'])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv/bin/python manage.py clear_cache --settings=fruition.settings.docker')
        ]
        assert click_mock.mock_calls == [
            call.get_current_context(),
            call.get_current_context().abort()
        ]
        assert 'Could not clear cache' in result.output

    @patch('jbcli.cli.jb.dockerutil')
    def test_jb_manage_single(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        runner = CliRunner()
        result = runner.invoke(cli, ['manage', 'test'])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv/bin/python manage.py test')
        ]
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_jb_manage_args(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        runner = CliRunner()
        result = runner.invoke(cli, ['manage', 'test', '--failfast', '--keepdb'])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv/bin/python manage.py test --failfast --keepdb')
        ]
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.click')
    @patch('jbcli.cli.jb.dockerutil')
    def test_jb_manage_not_running(self, dockerutil_mock, click_mock):
        dockerutil_mock.is_running.return_value = False
        runner = CliRunner()
        result = runner.invoke(cli, ['manage', 'test'])
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert click_mock.mock_calls == [
            call.get_current_context(),
            call.get_current_context().abort()
        ]
        assert 'Juicebox not running.  Run jb start' in result.output

    @patch('jbcli.cli.jb.click')
    @patch('jbcli.cli.jb.dockerutil')
    def test_jb_manage_api_exception(self, dockerutil_mock, click_mock):
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.run.side_effect = APIError('Fail')
        runner = CliRunner()
        result = runner.invoke(cli, ['manage', 'test'])
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert click_mock.mock_calls == [
            call.get_current_context(),
            call.get_current_context().abort()
        ]
