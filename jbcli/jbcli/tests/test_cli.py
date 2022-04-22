from __future__ import print_function

from collections import namedtuple
import os
from subprocess import CalledProcessError

from click.testing import CliRunner
from docker.errors import APIError
from mock import call, mock_open, patch, ANY
import six

from ..cli.jb import DEVLANDIA_DIR, cli


Container = namedtuple("Container", ["name"])


def invoke(*args, **kwargs):
    kwargs["catch_exceptions"] = False
    return CliRunner().invoke(cli, *args, **kwargs)


@patch("jbcli.cli.jb.get_deployment_secrets", new=lambda: {"test_secret": "true"})
class TestCli(object):
    def test_base(self):
        result = invoke()
        assert "Juicebox CLI app" in result.output
        assert result.exit_code == 0

    def test_bad_command(self):
        result = invoke(["cookies"])
        assert result.exit_code == 2
        assert "No such command 'cookies'" in result.output

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_add_single(
        self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = "git cookies"
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies"])

        assert "Adding cookies..." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp cookies"),
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"])
        ]
        # call.path.join('/Users/david.paul/Desktop/devlandia'),
        #  call.chdir(<MagicMock name='os.path.join()' id='4513544464'>),
        #  call.path.isdir('apps/cookies')
        assert "Adding cookies" in result.output

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_add_single_api(
        self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        """Adding an app by calling the jb api"""
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = "git cookies"
        apiutil_mock.load_app.return_value = True
        apiutil_mock.get_admin_token.return_value = "foo"

        result = invoke(["add", "cookies"])

        assert "Adding cookies..." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert apiutil_mock.mock_calls == [call.load_app(u"cookies")]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"])
        ]
        assert "Adding cookies" in result.output

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_add_single_venv3(
        self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = "git cookies"
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies", "--runtime", "venv3"])

        assert "Adding cookies..." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv3/bin/python manage.py loadjuiceboxapp cookies"),
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"])
        ]
        assert "Adding cookies" in result.output

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_add_single_api_venv3(
        self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        """Adding an app by calling the jb api"""
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = "git cookies"
        apiutil_mock.load_app.return_value = True
        apiutil_mock.get_admin_token.return_value = "foo"

        result = invoke(["add", "cookies", "--runtime", "venv3"])

        assert "Adding cookies..." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert apiutil_mock.mock_calls == [call.load_app(u"cookies")]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"])
        ]
        assert "Adding cookies" in result.output

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.os")
    def test_add_app_exists(self, os_mock, dockerutil_mock, apiutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = True
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies"])

        assert "App cookies already exists." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp cookies"),
        ]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.os")
    def test_add_app_exists_venv3(self, os_mock, dockerutil_mock, apiutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = True
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies", "--runtime", "venv3"])

        assert "App cookies already exists." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv3/bin/python manage.py loadjuiceboxapp cookies"),
        ]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    def test_add_not_running(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = False

        result = invoke(["add", "cookies"])
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert "Juicebox is not running.  Please run jb start." in result.output
        assert result.exit_code == 1

    @patch("jbcli.cli.jb.dockerutil")
    def test_add_not_running_venv3(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = False

        result = invoke(["add", "cookies", "--runtime", "venv3"])

        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert "Juicebox is not running.  Please run jb start." in result.output
        assert result.exit_code == 1

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_add_desktop(
        self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        apps_mock.make_github_repo_url.return_value = "git cookies"
        dockerutil_mock.is_running.return_value = True
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies", "--add-desktop"])

        assert "Adding cookies..." in result.output
        assert "Downloading app cookies from Github." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp cookies"),
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        print(os_mock.mock_calls)
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"]),
            call.check_call(["github", "apps/cookies"]),
        ]

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_add_desktop_venv3(
        self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        apps_mock.make_github_repo_url.return_value = "git cookies"
        dockerutil_mock.is_running.return_value = True
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies", "--add-desktop", "--runtime", "venv3"])

        assert "Adding cookies..." in result.output
        assert "Downloading app cookies from Github." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv3/bin/python manage.py loadjuiceboxapp cookies"),
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"]),
            call.check_call(["github", "apps/cookies"]),
        ]

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_add_multiple(
        self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        apps_mock.make_github_repo_url.return_value = "git cookies"
        dockerutil_mock.is_running.return_value = True
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies", "chocolate_chip"])

        assert "Adding cookies..." in result.output
        assert "Adding chocolate_chip"
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp cookies"),
            call.run("/venv/bin/python manage.py loadjuiceboxapp chocolate_chip"),
        ]
        assert apps_mock.mock_calls == [
            call.make_github_repo_url(u"cookies"),
            call.make_github_repo_url(u"chocolate_chip"),
        ]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/chocolate_chip"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"]),
            call.check_call(["git", "clone", "git cookies", "apps/chocolate_chip"]),
        ]

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_add_multiple_venv3(
        self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        apps_mock.make_github_repo_url.return_value = "git cookies"
        dockerutil_mock.is_running.return_value = True
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies", "chocolate_chip", "--runtime", "venv3"])

        assert "Adding cookies..." in result.output
        assert "Adding chocolate_chip"
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv3/bin/python manage.py loadjuiceboxapp cookies"),
            call.run("/venv3/bin/python manage.py loadjuiceboxapp chocolate_chip"),
        ]
        assert apps_mock.mock_calls == [
            call.make_github_repo_url(u"cookies"),
            call.make_github_repo_url(u"chocolate_chip"),
        ]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/chocolate_chip"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"]),
            call.check_call(["git", "clone", "git cookies", "apps/chocolate_chip"]),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess.check_call")
    @patch("jbcli.cli.jb.os")
    def test_add_clone_fail(self, os_mock, proc_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = "git cookies"
        proc_mock.side_effect = CalledProcessError(2, "cmd", "Ugh Cake")

        result = invoke(["add", "cookies"])

        assert "Adding cookies..." in result.output
        assert "Failed to load: cookies." in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"])
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess.check_call")
    @patch("jbcli.cli.jb.os")
    def test_add_clone_fail_venv3(self, os_mock, proc_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = "git cookies"
        proc_mock.side_effect = CalledProcessError(2, "cmd", "Ugh Cake")

        result = invoke(["add", "cookies", "--runtime", "venv3"])

        assert "Adding cookies..." in result.output
        assert "Failed to load: cookies." in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"])
        ]

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess.check_call")
    @patch("jbcli.cli.jb.os")
    def test_add_run_fail(
        self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.run.side_effect = APIError("Fail")
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = "git cookies"
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies"])

        assert "Adding cookies..." in result.output
        assert "Downloading app cookies from Github." in result.output
        assert "Failed to add cookies to the Juicebox VM" in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp cookies"),
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"])
        ]

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess.check_call")
    @patch("jbcli.cli.jb.os")
    def test_add_run_fail_venv3(
        self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.run.side_effect = APIError("Fail")
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = "git cookies"
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies", "--runtime", "venv3"])

        assert "Adding cookies..." in result.output
        assert "Downloading app cookies from Github." in result.output
        assert "Failed to add cookies to the Juicebox VM" in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv3/bin/python manage.py loadjuiceboxapp cookies"),
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"])
        ]

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess.check_call")
    @patch("jbcli.cli.jb.os")
    def test_add_desktop_fail(
        self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = "git cookies"
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        proc_mock.side_effect = [True, CalledProcessError(2, "cmd", "Ugh Cake")]

        result = invoke(["add", "cookies", "--add-desktop"])
        assert "Adding cookies..." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp cookies"),
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call(["git", "clone", "git cookies", "apps/cookies"]),
            call(["github", "apps/cookies"]),
        ]
        assert "Failed to add cookies to Github Desktop" in result.output
        assert "Downloading app cookies from Github" in result.output
        assert "cookies was added successfully" in result.output

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess.check_call")
    @patch("jbcli.cli.jb.os")
    def test_add_desktop_fail_venv3(
        self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        apps_mock.make_github_repo_url.return_value = "git cookies"
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        proc_mock.side_effect = [True, CalledProcessError(2, "cmd", "Ugh Cake")]

        result = invoke(["add", "cookies", "--add-desktop", "--runtime", "venv3"])
        assert "Adding cookies..." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv3/bin/python manage.py loadjuiceboxapp cookies"),
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call(["git", "clone", "git cookies", "apps/cookies"]),
            call(["github", "apps/cookies"]),
        ]
        assert "Failed to add cookies to Github Desktop" in result.output
        assert "Downloading app cookies from Github" in result.output
        assert "cookies was added successfully" in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.shutil")
    @patch("jbcli.cli.jb.os")
    def test_remove_single(self, os_mock, shutil_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True

        result = invoke(["remove", "cookies", "--yes"])

        assert "Removing cookies..." in result.output
        assert "Successfully deleted cookies" in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run("/venv/bin/python manage.py deletejuiceboxapp cookies"),
        ]
        assert shutil_mock.mock_calls == [call.rmtree("apps/cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.shutil")
    @patch("jbcli.cli.jb.os")
    def test_remove_single_venv3(self, os_mock, shutil_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True

        result = invoke(["remove", "cookies", "--yes", "--runtime", "venv3"])

        assert "Removing cookies..." in result.output
        assert "Successfully deleted cookies" in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run("/venv3/bin/python manage.py deletejuiceboxapp cookies"),
        ]
        assert shutil_mock.mock_calls == [call.rmtree("apps/cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    def test_remove_not_running(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = False

        result = invoke(["remove", "cookies", "--yes"])

        assert "Juicebox is not running.  Run jb start." in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
        ]
        assert result.exit_code == 1

    @patch("jbcli.cli.jb.dockerutil")
    def test_remove_not_running_venv3(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = False

        result = invoke(["remove", "cookies", "--yes", "--runtime", "venv3"])

        assert "Juicebox is not running.  Run jb start." in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
        ]
        assert result.exit_code == 1

    @patch("jbcli.cli.jb.dockerutil")
    def test_remove_not_home(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = False

        result = invoke(["remove", "cookies", "--yes"])

        assert "Juicebox is not running.  Run jb start." in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [call.is_running(), call.ensure_home()]
        assert result.exit_code == 1

    @patch("jbcli.cli.jb.dockerutil")
    def test_remove_not_home_venv3(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = False

        result = invoke(["remove", "cookies", "--yes", "--runtime", "venv3"])

        assert "Juicebox is not running.  Run jb start." in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [call.is_running(), call.ensure_home()]
        assert result.exit_code == 1

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.shutil")
    @patch("jbcli.cli.jb.os")
    def test_remove_multiple(self, os_mock, shutil_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True

        result = invoke(["remove", "cookies", "cake", "--yes"])

        assert "Removing cookies..." in result.output
        assert "Removing cake..." in result.output
        assert "Successfully deleted cookies" in result.output
        assert "Successfully deleted cake" in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run("/venv/bin/python manage.py deletejuiceboxapp cookies"),
            call.run("/venv/bin/python manage.py deletejuiceboxapp cake"),
        ]
        assert shutil_mock.mock_calls == [
            call.rmtree("apps/cookies"),
            call.rmtree("apps/cake"),
        ]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/cake"),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.shutil")
    @patch("jbcli.cli.jb.os")
    def test_remove_multiple_venv3(self, os_mock, shutil_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True

        result = invoke(["remove", "cookies", "cake", "--yes", "--runtime", "venv3"])

        assert "Removing cookies..." in result.output
        assert "Removing cake..." in result.output
        assert "Successfully deleted cookies" in result.output
        assert "Successfully deleted cake" in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run("/venv3/bin/python manage.py deletejuiceboxapp cookies"),
            call.run("/venv3/bin/python manage.py deletejuiceboxapp cake"),
        ]
        assert shutil_mock.mock_calls == [
            call.rmtree("apps/cookies"),
            call.rmtree("apps/cake"),
        ]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/cake"),
        ]

    @patch("jbcli.cli.jb.Process")
    @patch("jbcli.cli.jb.time")
    @patch("jbcli.cli.jb.dockerutil")
    def test_watch(self, dockerutil_mock, time_mock, process_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(["watch"])

        assert process_mock.mock_calls == [
            call(
                target=dockerutil_mock.jb_watch,
                kwargs={"app": "", "should_reload": False},
            ),
            call().start(),
            call().join(),
        ]

        assert result.exit_code == 0

    @patch("jbcli.cli.jb.Process")
    @patch("jbcli.cli.jb.time")
    @patch("jbcli.cli.jb.dockerutil")
    def test_watch_for_specific_app(self, dockerutil_mock, time_mock, process_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(["watch", "--app", "test"])

        assert process_mock.mock_calls == [
            call(
                target=dockerutil_mock.jb_watch,
                kwargs={"app": "test", "should_reload": False},
            ),
            call().start(),
            call().join(),
        ]

        assert result.exit_code == 0

    @patch("jbcli.cli.jb.Process")
    @patch("jbcli.cli.jb.time")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.create_browser_instance")
    def test_watch_with_reload(
        self, browser_mock, dockerutil_mock, time_mock, process_mock
    ):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(["watch", "--reload"])
        assert process_mock.mock_calls == [
            call(
                target=dockerutil_mock.jb_watch,
                kwargs={"app": "", "should_reload": True},
            ),
            call().start(),
            call().join(),
        ]
        assert browser_mock.called == True
        assert result.exit_code == 0

    @patch("jbcli.cli.jb.Process")
    @patch("jbcli.cli.jb.time")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.create_browser_instance")
    def test_watch_with_specific_app_and_reload(
        self, browser_mock, dockerutil_mock, time_mock, process_mock
    ):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(["watch", "--app", "test", "--reload"])
        assert process_mock.mock_calls == [
            call(
                target=dockerutil_mock.jb_watch,
                kwargs={"app": "test", "should_reload": True},
            ),
            call().start(),
            call().join(),
        ]
        assert browser_mock.called == True
        assert result.exit_code == 0

    @patch("jbcli.cli.jb.Process")
    @patch("jbcli.cli.jb.time")
    @patch("jbcli.cli.jb.dockerutil")
    def test_watch_full(self, dockerutil_mock, time_mock, process_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(["watch", "--includejs"])

        assert process_mock.mock_calls == [
            call(
                target=dockerutil_mock.jb_watch,
                kwargs={"app": "", "should_reload": False},
            ),
            call().start(),
            call(target=dockerutil_mock.js_watch),
            call().start(),
            call().join(),
            call().join(),
        ]

        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    def test_stop(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        dockerutil_mock.halt.return_value = None
        result = invoke(["stop"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.ensure_home(),
            call.is_running(),
            call.halt(),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    def test_stop_clean(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        dockerutil_mock.destroy.return_value = None
        result = invoke(["stop", "--clean"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [call.ensure_home(), call.destroy()]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.auth")
    def test_start(self, auth_mock, os_mock, dockerutil_mock):
        """Starting brings docker-compose up in the environment of the cwd."""
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        os_mock.path.isdir.return_value = True
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        result = invoke(["start", "develop-py3", "--noupgrade"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="develop-py3"),
            call.up(env=ANY, ganesha=False),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    def test_start_with_custom_tag(self, auth_mock, dockerutil_mock):
        """Starting can occur with any tag."""
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        result = invoke(["start", "potato", "--noupgrade"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="potato"),
            call.up(env=ANY, ganesha=False),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    def test_start_with_tag_lookup(self, auth_mock, dockerutil_mock):
        """Starting stable uses the tag master-py3."""
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        result = invoke(["start", "stable", "--noupgrade"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="master-py3"),
            call.up(env=ANY, ganesha=False),
        ]

    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    def test_start_core_without_fruitiondir(self, auth_mock, dockerutil_mock, os_mock):
        """Starting core requires a fruition directory."""
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        os_mock.environ.return_value = False
        os_mock.path.join.return_value = ""
        os_mock.getcwd.return_value = ""
        os_mock.path.exists.return_value = False
        os_mock.symlink.return_value = False
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        result = invoke(["start", "core", "--noupgrade"])
        assert result.exit_code == 1
        print(result.output)
        assert "Could not find Local Fruition Checkout" in result.output

    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    def test_start_core_with_fruitiondir(self, auth_mock, dockerutil_mock, os_mock):
        """Starting core requires a fruition directory."""
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        os_mock.environ.return_value = False
        os_mock.path.join.return_value = ""
        os_mock.getcwd.return_value = ""
        os_mock.path.exists.return_value = True
        os_mock.symlink.return_value = False
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "core", "--noupgrade"])
        assert result.exit_code == 0
        # We link the fruition/ directory with .env
        assert m.mock_calls == [
            call('/root/.config/juicebox/devlandia.toml'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call('/root/.config/juicebox/devlandia.toml'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call('/root/.config/juicebox/devlandia.toml'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(".env", "w"),
            ANY,
            call().write(
                "DEVLANDIA_PORT=8000\nTAG=develop-py3\nFRUITION=fruition\nFILE=code\nWORKFLOW=core\nRECIPE=recipereadme\nRECIPEFILE=unused\n"
            ),
            call().write("LOCAL_SNAPSHOT_DIR=./nothing\n"),
            call().write("CONTAINER_SNAPSHOT_DIR=/nothing\n"),
            ANY,
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="develop-py3"),
            call.up(env=ANY, ganesha=False),
        ]

    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    def test_start_core_with_fruitiondir_and_recipe(
        self, auth_mock, dockerutil_mock, os_mock
    ):
        """Starting core requires a fruition directory."""
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        os_mock.environ.return_value = False
        os_mock.path.join.return_value = ""
        os_mock.getcwd.return_value = ""
        os_mock.path.exists.return_value = True
        os_mock.symlink.return_value = False
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "core", "--noupgrade", "--dev-recipe"])
        assert result.exit_code == 0
        # We link the fruition/ directory with .env
        # We ALSO link the recipe/ directory
        print(m.mock_calls)
        assert m.mock_calls == [
            call('/root/.config/juicebox/devlandia.toml'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call('/root/.config/juicebox/devlandia.toml'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call('/root/.config/juicebox/devlandia.toml'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(".env", "w"),
            ANY,
            call().write(
                "DEVLANDIA_PORT=8000\nTAG=develop-py3\nFRUITION=fruition\nFILE=code\nWORKFLOW=core\nRECIPE=recipe\nRECIPEFILE=code/recipe\n"
            ),
            call().write("LOCAL_SNAPSHOT_DIR=./nothing\n"),
            call().write("CONTAINER_SNAPSHOT_DIR=/nothing\n"),
            ANY,
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="develop-py3"),
            call.up(env=ANY, ganesha=False),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    def test_start_noupgrade(self, auth_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        result = invoke(["start", "develop-py3", "--noupgrade"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="develop-py3"),
            call.up(env=ANY, ganesha=False),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch("jbcli.cli.jb.check_outdated_image")
    def test_start_noupdate(self, image_mock, auth_mock, dockerutil_mock, monkeypatch):
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.ensure_home.return_value = True
        image_mock.answer = "no"
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        result = invoke(["start", "develop-py3", "--noupdate", "--noupgrade"])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.up(env=ANY, ganesha=False),
        ]
        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    def test_start_already_running(self, auth_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.ensure_home.return_value = True
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        result = invoke(["start", "--noupgrade"])

        assert "An instance of Juicebox is already running" in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [call.is_running()]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.os")
    def test_clone(self, os_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.side_effect = [True, False]
        apps_mock.clone.return_value = "git cookies"
        dockerutil_mock.is_running.return_value = True
        result = invoke(["clone", "cookies", "chocolate_chip"])

        assert apps_mock.mock_calls == [
            call.clone(
                u"chocolate_chip",
                "apps/cookies",
                "apps/chocolate_chip",
                init_vcs=True,
                track_vcs=True,
            )
        ]
        assert os_mock.mock_calls == [
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/chocolate_chip"),
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp chocolate_chip"),
        ]
        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    def test_clone_running_fail(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False

        result = invoke(["clone", "cookies", "chocolate_chip"])

        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert result.exit_code == 1
        assert "Juicebox is not running.  Run jb start." in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.os")
    def test_clone_from_nonexist(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        result = invoke(["clone", "cookies", "chocolate_chip"])

        assert os_mock.mock_calls == [
            call.path.isdir("apps/cookies"),
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
        ]
        assert result.exit_code == 1
        assert "App cookies does not exist." in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.os")
    def test_clone_to_exists(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.side_effect = [True, True]
        dockerutil_mock.is_running.return_value = True

        result = invoke(["clone", "cookies", "chocolate_chip"])

        assert os_mock.mock_calls == [
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/chocolate_chip"),
        ]
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert result.exit_code == 1
        assert "App chocolate_chip already exists." in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.os")
    def test_clone_failed(self, os_mock, apps_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        os_mock.path.isdir.side_effect = [True, False]
        apps_mock.clone.side_effect = ValueError("Cake Bad")

        result = invoke(["clone", "cookies", "chocolate_chip"])

        assert apps_mock.mock_calls == [
            call.clone(
                u"chocolate_chip",
                "apps/cookies",
                "apps/chocolate_chip",
                init_vcs=True,
                track_vcs=True,
            )
        ]
        assert os_mock.mock_calls == [
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/chocolate_chip"),
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
        ]
        assert result.exit_code == 1
        assert "Cloning failed" in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.os")
    def test_clone_run_failed(self, os_mock, apps_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        apps_mock.clone.return_value = True
        os_mock.path.isdir.side_effect = [True, False]

        result = invoke(["clone", "cookies", "chocolate_chip"])

        assert apps_mock.mock_calls == [
            call.clone(
                u"chocolate_chip",
                "apps/cookies",
                "apps/chocolate_chip",
                init_vcs=True,
                track_vcs=True,
            )
        ]
        assert os_mock.mock_calls == [
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/chocolate_chip"),
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp chocolate_chip"),
        ]
        assert "Cloning from cookies to chocolate_chip" in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.os")
    def test_clone_venv3(self, os_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.side_effect = [True, False]
        apps_mock.clone.return_value = "git cookies"
        dockerutil_mock.is_running.return_value = True
        result = invoke(["clone", "cookies", "chocolate_chip", "--runtime", "venv3"])

        assert apps_mock.mock_calls == [
            call.clone(
                u"chocolate_chip",
                "apps/cookies",
                "apps/chocolate_chip",
                init_vcs=True,
                track_vcs=True,
            )
        ]
        assert os_mock.mock_calls == [
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/chocolate_chip"),
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv3/bin/python manage.py loadjuiceboxapp chocolate_chip"),
        ]
        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    def test_clone_running_fail_venv3(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False

        result = invoke(["clone", "cookies", "chocolate_chip", "--runtime", "venv3"])

        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert result.exit_code == 1
        assert "Juicebox is not running.  Run jb start." in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.os")
    def test_clone_from_nonexist_venv3(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = True
        result = invoke(["clone", "cookies", "chocolate_chip", "--runtime", "venv3"])

        assert os_mock.mock_calls == [
            call.path.isdir("apps/cookies"),
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
        ]
        assert result.exit_code == 1
        assert "App cookies does not exist." in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.os")
    def test_clone_to_exists_venv3(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.side_effect = [True, True]
        dockerutil_mock.is_running.return_value = True

        result = invoke(["clone", "cookies", "chocolate_chip", "--runtime", "venv3"])

        assert os_mock.mock_calls == [
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/chocolate_chip"),
        ]
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert result.exit_code == 1
        assert "App chocolate_chip already exists." in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.os")
    def test_clone_failed_venv3(self, os_mock, apps_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        os_mock.path.isdir.side_effect = [True, False]
        apps_mock.clone.side_effect = ValueError("Cake Bad")

        result = invoke(["clone", "cookies", "chocolate_chip", "--runtime", "venv3"])

        assert apps_mock.mock_calls == [
            call.clone(
                u"chocolate_chip",
                "apps/cookies",
                "apps/chocolate_chip",
                init_vcs=True,
                track_vcs=True,
            )
        ]
        assert os_mock.mock_calls == [
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/chocolate_chip"),
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
        ]
        assert result.exit_code == 1
        assert "Cloning failed" in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.os")
    def test_clone_run_failed_venv3(self, os_mock, apps_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True
        apps_mock.clone.return_value = True
        os_mock.path.isdir.side_effect = [True, False]

        result = invoke(["clone", "cookies", "chocolate_chip", "--runtime", "venv3"])

        assert apps_mock.mock_calls == [
            call.clone(
                u"chocolate_chip",
                "apps/cookies",
                "apps/chocolate_chip",
                init_vcs=True,
                track_vcs=True,
            )
        ]
        assert os_mock.mock_calls == [
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/chocolate_chip"),
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv3/bin/python manage.py loadjuiceboxapp chocolate_chip"),
        ]
        assert "Cloning from cookies to chocolate_chip" in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_yo_upgrade(self, os_mock, proc_mock, dockerutil_mock):
        dockerutil_mock.ensure_root.return_value = True
        dockerutil_mock.ensure_virtualenv.return_value = True
        os_mock.environ.return_value = False
        os_mock.path.join.return_value = ""
        os_mock.getcwd.return_value = ""
        os_mock.path.exists.return_value = True
        os_mock.symlink.return_value = False
        proc_mock.check_call.return_value = "foo"

        result = invoke(["yo_upgrade"])

        # TODO: Improve these tests
        assert proc_mock.mock_calls == []
        # assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    def test_clear_cache(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = True

        result = invoke(["clear_cache"])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py clear_cache"),
        ]

        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    def test_clear_cache_not_running(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = False

        result = invoke(["clear_cache"])
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert result.exit_code == 1

    @patch("jbcli.cli.jb.dockerutil")
    def test_jb_pull(self, dockerutil_mock):
        result = invoke(["pull"])
        assert dockerutil_mock.mock_calls == [call.pull(None)]
        assert result.exit_code == 0

    @patch("jbcli.cli.jb.click")
    @patch("jbcli.cli.jb.dockerutil")
    def test_clear_cache_fail(self, dockerutil_mock, click_mock):
        dockerutil_mock.is_running.return_value = True
        dockerutil_mock.run.side_effect = APIError("Failure")
        result = invoke(["clear_cache"])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py clear_cache"),
        ]
        assert click_mock.mock_calls == [
            call.get_current_context(),
            call.get_current_context().abort(),
        ]
        assert "Could not clear cache" in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.subprocess")
    def test_jb_run_running_no_env(self, subprocess_mock, dockerutil_mock):
        """When a container is running and no --env is given,
        we run the command in the existing container.
        """
        dockerutil_mock.is_running.return_value = Container(name="stable_juicebox_1")
        dockerutil_mock.check_home.return_value = None
        subprocess_mock.check_call.return_value = None
        result = invoke(["run", "foo", "bar"])
        assert subprocess_mock.mock_calls == [
            call.check_call(
                ["docker", "exec", "-it", "stable_juicebox_1", "foo", "bar"]
            )
        ]
        assert result.exit_code == 0

    @patch("jbcli.cli.jb.click")
    @patch("jbcli.cli.jb.dockerutil")
    def test_jb_manage_not_running_no_env(self, dockerutil_mock, click_mock):
        """When no container is running, and no --env is given, we give up."""
        dockerutil_mock.is_running.return_value = False
        dockerutil_mock.check_home.return_value = None
        result = invoke(["manage", "test"])
        assert "Juicebox not running and no --env given" in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.subprocess")
    def test_jb_manage_running_matching_env(self, subprocess_mock, dockerutil_mock):
        """When an --env is given, and it matches a running JB container,
        we use the running container.
        """
        dockerutil_mock.is_running.return_value = Container(name="core_juicebox_1")
        dockerutil_mock.check_home.return_value = None
        subprocess_mock.check_call.return_value = None

        result = invoke(["manage", "--env", "core", "test"])
        assert subprocess_mock.mock_calls == [
            call.check_call(
                [
                    "docker",
                    "exec",
                    "-it",
                    "core_juicebox_1",
                    "/venv/bin/python",
                    "manage.py",
                    "test",
                ]
            )
        ]
        assert result.exit_code == 0
