from __future__ import print_function

from collections import namedtuple
import os
from subprocess import CalledProcessError

from click.testing import CliRunner
from docker.errors import APIError
from mock import call, patch, ANY

from ..cli.jb import DEVLANDIA_DIR, cli


CORE_DIR = os.path.join(DEVLANDIA_DIR, 'environments/core')

Container = namedtuple('Container', ['name'])


def invoke(*args, **kwargs):
    kwargs['catch_exceptions'] = False
    return CliRunner().invoke(cli, *args, **kwargs)


@patch('jbcli.cli.jb.get_deployment_secrets', new=lambda: {'test_secret': 'true'})
class TestCli(object):
    def test_base(self):
        result = invoke()
        assert 'Juicebox CLI app' in result.output
        assert result.exit_code == 0

    def test_bad_command(self):
        result = invoke(['cookies'])
        assert result.exit_code == 2
        assert 'No such command "cookies"' in result.output

    @patch('jbcli.cli.jb.apps')
    def test_create_full(self, app_mock):
        result = invoke(['create', 'cookies'])
        assert app_mock.mock_calls == []
        assert result.output == 'yo juicebox will take care of all your needs now.\n'
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_package_single(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        result = invoke(['package', 'cookies'])

        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv/bin/python manage.py packagejuiceboxapp cookies')
        ]
        assert 'Packaging cookies' in result.output
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_package_single_venv3(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        result = invoke(['package', 'cookies', '--runtime', 'venv3'])

        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv3/bin/python manage.py packagejuiceboxapp cookies')
        ]
        assert 'Packaging cookies' in result.output
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_package_to_bucket(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        result = invoke(['package', 'cookies', '--bucket', 'test_bucket'])

        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv/bin/python manage.py packagejuiceboxapp cookies --bucket=test_bucket')
        ]
        assert 'Packaging cookies' in result.output
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_package_to_bucket_venv3(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        result = invoke(['package', 'cookies', '--bucket', 'test_bucket', '--runtime', 'venv3'])

        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run(
                '/venv3/bin/python manage.py packagejuiceboxapp cookies --bucket=test_bucket')
        ]
        assert 'Packaging cookies' in result.output
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_package_not_running(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False
        result = invoke(['package', 'cookies'])
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert 'Juicebox is not running or you\'re not in a home directory.' in result.output
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    def test_package_not_running_venv3(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False
        result = invoke(['package', 'cookies', '--runtime', 'venv3'])
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
        result = invoke(['package', 'cookies', 'chocolate_chip'])

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
    def test_package_multiple_venv3(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        result = invoke(['package', 'cookies', 'chocolate_chip', '--runtime', 'venv3'])

        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv3/bin/python manage.py packagejuiceboxapp cookies'),
            call.run(
                '/venv3/bin/python manage.py packagejuiceboxapp chocolate_chip')
        ]
        assert 'Packaging cookies' in result.output
        assert 'Packaging chocolate_chip' in result.output
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_package_fail(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        dockerutil_mock.run.side_effect = APIError('Fail')
        result = invoke(['package', 'cookies'])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv/bin/python manage.py packagejuiceboxapp cookies')
        ]

        assert 'Packaging cookies...' in result.output
        assert 'Failed to package: cookies.' in result.output

        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    def test_package_fail_venv3(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        dockerutil_mock.run.side_effect = APIError('Fail')
        result = invoke(['package', 'cookies', '--runtime', 'venv3'])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv3/bin/python manage.py packagejuiceboxapp cookies')
        ]

        assert 'Packaging cookies...' in result.output
        assert 'Failed to package: cookies.' in result.output

        assert result.exit_code == 1

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess')
    @patch('jbcli.cli.jb.os')
    def test_add_single(self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(['add', 'cookies'])

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

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess')
    @patch('jbcli.cli.jb.os')
    def test_add_single_api(self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock):
        """Adding an app by calling the jb api """
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        apiutil_mock.load_app.return_value = True
        apiutil_mock.get_admin_token.return_value = 'foo'

        result = invoke(['add', 'cookies'])

        assert 'Adding cookies...' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert apiutil_mock.mock_calls == [
            call.load_app(u'cookies')
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u'cookies')]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]
        assert proc_mock.mock_calls == [
            call.check_call(['git', 'clone', 'git cookies', 'apps/cookies'])
        ]
        assert 'Adding cookies' in result.output

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess')
    @patch('jbcli.cli.jb.os')
    def test_add_single_venv3(self, os_mock, proc_mock, apps_mock, dockerutil_mock,
                        apiutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(['add', 'cookies', '--runtime', 'venv3'])

        assert 'Adding cookies...' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv3/bin/python manage.py loadjuiceboxapp cookies')
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u'cookies')]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]
        assert proc_mock.mock_calls == [
            call.check_call(['git', 'clone', 'git cookies', 'apps/cookies'])
        ]
        assert 'Adding cookies' in result.output

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess')
    @patch('jbcli.cli.jb.os')
    def test_add_single_api_venv3(self, os_mock, proc_mock, apps_mock,
                            dockerutil_mock, apiutil_mock):
        """Adding an app by calling the jb api """
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        apiutil_mock.load_app.return_value = True
        apiutil_mock.get_admin_token.return_value = 'foo'

        result = invoke(['add', 'cookies', '--runtime', 'venv3' ])

        assert 'Adding cookies...' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert apiutil_mock.mock_calls == [
            call.load_app(u'cookies')
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u'cookies')]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]
        assert proc_mock.mock_calls == [
            call.check_call(['git', 'clone', 'git cookies', 'apps/cookies'])
        ]
        assert 'Adding cookies' in result.output

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.os')
    def test_upload(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True

        result = invoke(['upload', '--app=foo', 'cookies.csv'])

        assert 'Uploading...' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.ensure_home().__nonzero__(),
            call.run('/venv/bin/python manage.py upload --app=foo cookies.csv')
        ]

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.os')
    def test_upload_venv3(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True

        result = invoke(['upload', '--app=foo', 'cookies.csv', '--runtime', 'venv3'])

        assert 'Uploading...' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.ensure_home().__nonzero__(),
            call.run('/venv3/bin/python manage.py upload --app=foo cookies.csv')
        ]

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.os')
    def test_add_app_exists(self, os_mock, dockerutil_mock, apiutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = True
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(['add', 'cookies'])

        assert 'App cookies already exists.' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv/bin/python manage.py loadjuiceboxapp cookies')
        ]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.os')
    def test_add_app_exists_venv3(self, os_mock, dockerutil_mock, apiutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = True
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(['add', 'cookies', '--runtime', 'venv3'])

        assert 'App cookies already exists.' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv3/bin/python manage.py loadjuiceboxapp cookies')
        ]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]

    @patch('jbcli.cli.jb.dockerutil')
    def test_add_not_running(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False

        result = invoke(['add', 'cookies'])

        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert 'Juicebox is not running.  Please run jb start.' in result.output
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    def test_add_not_running_venv3(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False

        result = invoke(['add', 'cookies', '--runtime', 'venv3'])

        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert 'Juicebox is not running.  Please run jb start.' in result.output
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess')
    @patch('jbcli.cli.jb.os')
    def test_add_desktop(self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock):
        os_mock.path.isdir.return_value = False
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        dockerutil_mock.is_running.return_value = True
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(['add', 'cookies', '--add-desktop'])

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

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess')
    @patch('jbcli.cli.jb.os')
    def test_add_desktop_venv3(self, os_mock, proc_mock, apps_mock, dockerutil_mock,
                         apiutil_mock):
        os_mock.path.isdir.return_value = False
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        dockerutil_mock.is_running.return_value = True
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(['add', 'cookies', '--add-desktop', '--runtime', 'venv3'])

        assert 'Adding cookies...' in result.output
        assert 'Downloading app cookies from Github.' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv3/bin/python manage.py loadjuiceboxapp cookies')
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u'cookies')]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]
        assert proc_mock.mock_calls == [
            call.check_call(['git', 'clone', 'git cookies', 'apps/cookies']),
            call.check_call(['github', 'apps/cookies'])
        ]

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess')
    @patch('jbcli.cli.jb.os')
    def test_add_multiple(self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock):
        os_mock.path.isdir.return_value = False
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        dockerutil_mock.is_running.return_value = True
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(['add', 'cookies', 'chocolate_chip'])

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

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess')
    @patch('jbcli.cli.jb.os')
    def test_add_multiple_venv3(self, os_mock, proc_mock, apps_mock, dockerutil_mock,
                          apiutil_mock):
        os_mock.path.isdir.return_value = False
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        dockerutil_mock.is_running.return_value = True
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(['add', 'cookies', 'chocolate_chip', '--runtime', 'venv3'])

        assert 'Adding cookies...' in result.output
        assert 'Adding chocolate_chip'
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv3/bin/python manage.py loadjuiceboxapp cookies'),
            call.run(
                '/venv3/bin/python manage.py loadjuiceboxapp chocolate_chip')
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
            call.check_call(
                ['git', 'clone', 'git cookies', 'apps/chocolate_chip']),
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

        result = invoke(['add', 'cookies'])

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
    def test_add_clone_fail_venv3(self, os_mock, proc_mock, apps_mock,
                            dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        proc_mock.side_effect = CalledProcessError(2, 'cmd', 'Ugh Cake')

        result = invoke(['add', 'cookies', '--runtime', 'venv3'])

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

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess.check_call')
    @patch('jbcli.cli.jb.os')
    def test_add_run_fail(self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.run.side_effect = APIError('Fail')
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(['add', 'cookies'])

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

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess.check_call')
    @patch('jbcli.cli.jb.os')
    def test_add_run_fail_venv3(self, os_mock, proc_mock, apps_mock, dockerutil_mock,
                          apiutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.run.side_effect = APIError('Fail')
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(['add', 'cookies', '--runtime', 'venv3'])

        assert 'Adding cookies...' in result.output
        assert 'Downloading app cookies from Github.' in result.output
        assert 'Failed to add cookies to the Juicebox VM' in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv3/bin/python manage.py loadjuiceboxapp cookies')
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u'cookies')]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]
        assert proc_mock.mock_calls == [
            call.check_call(['git', 'clone', 'git cookies', 'apps/cookies'])
        ]

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess.check_call')
    @patch('jbcli.cli.jb.os')
    def test_add_desktop_fail(self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        proc_mock.side_effect = [
            True, CalledProcessError(2, 'cmd', 'Ugh Cake')
        ]

        result = invoke(['add', 'cookies', '--add-desktop'])
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

    @patch('jbcli.cli.jb.jbapiutil')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.subprocess.check_call')
    @patch('jbcli.cli.jb.os')
    def test_add_desktop_fail_venv3(self, os_mock, proc_mock, apps_mock,
                              dockerutil_mock, apiutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = 'git cookies'
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        proc_mock.side_effect = [
            True, CalledProcessError(2, 'cmd', 'Ugh Cake')
        ]

        result = invoke(['add', 'cookies', '--add-desktop', '--runtime', 'venv3'])
        assert 'Adding cookies...' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv3/bin/python manage.py loadjuiceboxapp cookies')
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

        result = invoke(['remove', 'cookies', '--yes'])

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
    @patch('jbcli.cli.jb.shutil')
    @patch('jbcli.cli.jb.os')
    def test_remove_single_venv3(self, os_mock, shutil_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True

        result = invoke(['remove', 'cookies', '--yes', '--runtime', 'venv3'])

        assert 'Removing cookies...' in result.output
        assert 'Successfully deleted cookies' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv3/bin/python manage.py deletejuiceboxapp cookies')
        ]
        assert shutil_mock.mock_calls == [call.rmtree('apps/cookies')]
        assert os_mock.mock_calls == [call.path.isdir('apps/cookies')]

    @patch('jbcli.cli.jb.dockerutil')
    def test_remove_not_running(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False

        result = invoke(['remove', 'cookies', '--yes'])

        assert 'Juicebox is not running.  Run jb start.' in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
        ]
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    def test_remove_not_running(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False

        result = invoke(['remove', 'cookies', '--yes', '--runtime', 'venv3'])

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

        result = invoke(['remove', 'cookies', '--yes'])

        assert 'Juicebox is not running.  Run jb start.' in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home()
        ]
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    def test_remove_not_home_venv3(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = False

        result = invoke(['remove', 'cookies', '--yes', '--runtime', 'venv3'])

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

        result = invoke(['remove', 'cookies', 'cake', '--yes'])

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

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.shutil')
    @patch('jbcli.cli.jb.os')
    def test_remove_multiple_venv3(self, os_mock, shutil_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True

        result = invoke(['remove', 'cookies', 'cake', '--yes', '--runtime', 'venv3'])

        assert 'Removing cookies...' in result.output
        assert 'Removing cake...' in result.output
        assert 'Successfully deleted cookies' in result.output
        assert 'Successfully deleted cake' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run('/venv3/bin/python manage.py deletejuiceboxapp cookies'),
            call.run('/venv3/bin/python manage.py deletejuiceboxapp cake')
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
        result = invoke(['watch'])

        assert process_mock.mock_calls == [
            call(target=dockerutil_mock.jb_watch, kwargs={
                 'app': '', "should_reload": False}),
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
        result = invoke(['watch', '--app', 'test'])

        assert process_mock.mock_calls == [
            call(target=dockerutil_mock.jb_watch, kwargs={
                 'app': 'test', "should_reload": False}),
            call().start(),
            call().join()
        ]

        assert result.exit_code == 0

    @patch('jbcli.cli.jb.Process')
    @patch('jbcli.cli.jb.time')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.create_browser_instance')
    def test_watch_with_reload(self, browser_mock, dockerutil_mock, time_mock, process_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(['watch', '--reload'])
        assert process_mock.mock_calls == [
            call(target=dockerutil_mock.jb_watch, kwargs={
                 'app': '', "should_reload": True}),
            call().start(),
            call().join()
        ]
        assert browser_mock.called == True
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.Process')
    @patch('jbcli.cli.jb.time')
    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.create_browser_instance')
    def test_watch_with_specific_app_and_reload(self, browser_mock, dockerutil_mock, time_mock, process_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(['watch', '--app', 'test', '--reload'])
        assert process_mock.mock_calls == [
            call(target=dockerutil_mock.jb_watch, kwargs={
                 'app': 'test', "should_reload": True}),
            call().start(),
            call().join()
        ]
        assert browser_mock.called == True
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.Process')
    @patch('jbcli.cli.jb.time')
    @patch('jbcli.cli.jb.dockerutil')
    def test_watch_full(self, dockerutil_mock, time_mock, process_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(['watch', '--includejs'])

        assert process_mock.mock_calls == [
            call(target=dockerutil_mock.jb_watch,
                 kwargs={'app': '', "should_reload": False}),
            call().start(),
            call(target=dockerutil_mock.js_watch),
            call().start(),
            call().join(),
            call().join()
        ]

        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_stop(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(CORE_DIR)
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        dockerutil_mock.halt.return_value = None
        result = invoke(['stop'])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.ensure_home(),
            call.is_running(),
            call.halt()
        ]

    @patch('jbcli.cli.jb.dockerutil')
    def test_stop_clean(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(CORE_DIR)
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        dockerutil_mock.destroy.return_value = None
        result = invoke(['stop', '--clean'])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.ensure_home(),
            call.is_running(),
            call.destroy()
        ]

    @patch('jbcli.cli.jb.dockerutil')
    def test_start(self, dockerutil_mock, monkeypatch):
        """Starting brings docker-compose up in the environment of the cwd."""
        monkeypatch.chdir(CORE_DIR)
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        result = invoke(['start', '--noupgrade'], catch_exceptions=False)
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag=None),
            call.up(env=ANY)
        ]

    @patch('jbcli.cli.jb.dockerutil')
    def test_start_noupgrade(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(CORE_DIR)
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        result = invoke(['start', '--noupgrade'])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag=None),
            call.up(env=ANY)
        ]

    @patch('jbcli.cli.jb.dockerutil')
    def test_start_noupdate(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(CORE_DIR)
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        result = invoke(['start', '--noupdate', '--noupgrade'])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.up(env=ANY)
        ]
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_start_already_running(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        result = invoke(['start', '--noupgrade'])

        assert 'An instance of Juicebox is already running' in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.os')
    def test_clone(self, os_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.side_effect = [True, False]
        apps_mock.clone.return_value = 'git cookies'
        dockerutil_mock.is_running.return_value = True
        result = invoke(['clone', 'cookies', 'chocolate_chip'])

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

        result = invoke(['clone', 'cookies', 'chocolate_chip'])

        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert result.exit_code == 1
        assert 'Juicebox is not running.  Run jb start.' in result.output

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.os')
    def test_clone_from_nonexist(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        result = invoke(['clone', 'cookies', 'chocolate_chip'])

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

        result = invoke(['clone', 'cookies', 'chocolate_chip'])

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

        result = invoke(['clone', 'cookies', 'chocolate_chip'])

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

        result = invoke(['clone', 'cookies', 'chocolate_chip'])

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
    @patch('jbcli.cli.jb.apps')
    @patch('jbcli.cli.jb.os')
    def test_clone_venv3(self, os_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.side_effect = [True, False]
        apps_mock.clone.return_value = 'git cookies'
        dockerutil_mock.is_running.return_value = True
        result = invoke(['clone', 'cookies', 'chocolate_chip', '--runtime', 'venv3'])

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
            call.run(
                '/venv3/bin/python manage.py loadjuiceboxapp chocolate_chip')
        ]
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_clone_running_fail_venv3(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False

        result = invoke(['clone', 'cookies', 'chocolate_chip', '--runtime', 'venv3'])

        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert result.exit_code == 1
        assert 'Juicebox is not running.  Run jb start.' in result.output

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.os')
    def test_clone_from_nonexist_venv3(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        result = invoke(['clone', 'cookies', 'chocolate_chip', '--runtime', 'venv3'])

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
    def test_clone_to_exists_venv3(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.side_effect = [True, True]
        dockerutil_mock.is_running.return_value = True

        result = invoke(['clone', 'cookies', 'chocolate_chip', '--runtime', 'venv3'])

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
    def test_clone_failed_venv3(self, os_mock, apps_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        os_mock.path.isdir.side_effect = [True, False]
        apps_mock.clone.side_effect = ValueError('Cake Bad')

        result = invoke(['clone', 'cookies', 'chocolate_chip', '--runtime', 'venv3'])

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
    def test_clone_run_failed_venv3(self, os_mock, apps_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        apps_mock.clone.return_value = True
        os_mock.path.isdir.side_effect = [True, False]

        result = invoke(['clone', 'cookies', 'chocolate_chip', '--runtime', 'venv3'])

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
            call.run(
                '/venv3/bin/python manage.py loadjuiceboxapp chocolate_chip')
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
        os_mock.path.exists.return_value = True
        os_mock.symlink.return_value = False

        result = invoke(['yo_upgrade'])

        # TODO: Improve these tests
        assert proc_mock.mock_calls == [
            call.check_call(['npm', 'install', '--package-lock=false', 'generator-juicebox']),
            call.check_call().__unicode__()
        ]
        # assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_test_app(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        result = invoke(['test_app', 'jb3demo'])
        assert dockerutil_mock.mock_calls == [call.is_running(),
                                              call.run(
                                                  'sh -c "cd apps/jb3demo; pwd; /venv/bin/python -m unittest discover tests"')]

        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_test_app_fail(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.run.side_effect = APIError('Fail')
        result = invoke(['test_app', 'jb3demo'])
        assert dockerutil_mock.mock_calls == [call.is_running(),
                                              call.run(
                                                  'sh -c "cd apps/jb3demo; pwd; /venv/bin/python -m unittest discover tests"')]

        assert 'Could not run tests' in result.output
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    def test_test_app_venv3(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        result = invoke(['test_app', 'jb3demo', '--runtime', 'venv3'])
        assert dockerutil_mock.mock_calls == [call.is_running(),
                                              call.run(
                                                  'sh -c "cd apps/jb3demo; pwd; /venv3/bin/python -m unittest discover tests"')]

        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_test_app_fail_venv3(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.run.side_effect = APIError('Fail')
        result = invoke(['test_app', 'jb3demo', '--runtime', 'venv3'])
        assert dockerutil_mock.mock_calls == [call.is_running(),
                                              call.run(
                                                  'sh -c "cd apps/jb3demo; pwd; /venv3/bin/python -m unittest discover tests"')]

        assert 'Could not run tests' in result.output
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    def test_clear_cache(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True

        result = invoke(['clear_cache'])
        assert dockerutil_mock.mock_calls == [call.is_running(),
                                              call.run('/venv/bin/python manage.py clear_cache '
                                                       '--settings=fruition.settings.docker')]

        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_clear_cache_not_running(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False

        result = invoke(['clear_cache'])
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    def test_clear_cache_venv3(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True

        result = invoke(['clear_cache', '--runtime', 'venv3'])
        assert dockerutil_mock.mock_calls == [call.is_running(),
                                              call.run(
                                                  '/venv3/bin/python manage.py clear_cache '
                                                  '--settings=fruition.settings.docker')]

        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    def test_clear_cache_not_running_venv3(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False

        result = invoke(['clear_cache', '--runtime', 'venv3'])
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert result.exit_code == 1

    @patch('jbcli.cli.jb.dockerutil')
    def test_jb_pull(self, dockerutil_mock):
        result = invoke(['pull'])
        assert dockerutil_mock.mock_calls == [
            call.pull(None)
        ]
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.click')
    @patch('jbcli.cli.jb.dockerutil')
    def test_clear_cache_fail(self, dockerutil_mock, click_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.run.side_effect = APIError('Failure')
        result = invoke(['clear_cache'])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run('/venv/bin/python manage.py clear_cache --settings=fruition.settings.docker')
        ]
        assert click_mock.mock_calls == [
            call.get_current_context(),
            call.get_current_context().abort()
        ]
        assert 'Could not clear cache' in result.output

    @patch('jbcli.cli.jb.click')
    @patch('jbcli.cli.jb.dockerutil')
    def test_clear_cache_fail_venv3(self, dockerutil_mock, click_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.run.side_effect = APIError('Failure')
        result = invoke(['clear_cache', '--runtime', 'venv3'])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run(
                '/venv3/bin/python manage.py clear_cache --settings=fruition.settings.docker')
        ]
        assert click_mock.mock_calls == [
            call.get_current_context(),
            call.get_current_context().abort()
        ]
        assert 'Could not clear cache' in result.output

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.subprocess')
    def test_jb_manage_running_no_env(self, subprocess_mock, dockerutil_mock):
        """When a container is running and no --env is given,
        we run the command in the existing container.
        """
        dockerutil_mock.is_running.return_value = Container(name='stable_juicebox_1')
        dockerutil_mock.check_home.return_value = None
        subprocess_mock.check_call.return_value = None
        result = invoke(['manage', 'test',  '--failfast', '--keepdb'])
        assert subprocess_mock.mock_calls == [
            call.check_call([
                'docker', 'exec', '-it', 'stable_juicebox_1',
                '/venv/bin/python', 'manage.py', 'test', '--failfast', '--keepdb'])
        ]
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.click')
    @patch('jbcli.cli.jb.dockerutil')
    def test_jb_manage_not_running_no_env(self, dockerutil_mock, click_mock):
        """When no container is running, and no --env is given, we give up."""
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.check_home.return_value = None
        result = invoke(['manage', 'test'])
        assert 'Juicebox not running and no --env given' in result.output

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.subprocess')
    def test_jb_manage_running_matching_env(self, subprocess_mock, dockerutil_mock):
        """When an --env is given, and it matches a running JB container,
        we use the running container.
        """
        dockerutil_mock.is_running.return_value = Container(name='core_juicebox_1')
        dockerutil_mock.check_home.return_value = None
        subprocess_mock.check_call.return_value = None

        result = invoke(['manage', '--env', 'core', 'test'])
        assert subprocess_mock.mock_calls == [
            call.check_call([
                'docker', 'exec', '-it', 'core_juicebox_1',
                '/venv/bin/python', 'manage.py', 'test'])
        ]
        assert result.exit_code == 0

    @patch('jbcli.cli.jb.dockerutil')
    @patch('jbcli.cli.jb.subprocess')
    def test_jb_manage_running_not_matching_env(self, subprocess_mock, dockerutil_mock):
        """When an --env is given, and there is no matching container, we run a new one.
        """
        dockerutil_mock.is_running.return_value = Container(name='core_juicebox_1')
        dockerutil_mock.check_home.return_value = None
        subprocess_mock.check_call.side_effect = Exception("don't run this!")
        dockerutil_mock.run_jb.return_value = None

        result = invoke(['manage', '--env', 'stable', 'test'])
        assert dockerutil_mock.run_jb.mock_calls == [
            call(['/venv/bin/python', 'manage.py', 'test'], env=ANY)
        ]
        name, args, kwargs = dockerutil_mock.run_jb.mock_calls[0]
        assert kwargs['env']['test_secret'] == 'true'
        assert result.exit_code == 0
