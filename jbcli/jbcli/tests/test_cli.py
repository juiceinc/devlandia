from __future__ import print_function

from collections import namedtuple
import os
from io import StringIO
from os.path import expanduser
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
    def test_add_single_custom(
            self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = [True, False]
        apps_mock.make_github_repo_url.return_value = "git cookies"
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies"])

        assert "Adding cookies..." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp cookies", env='custom'),
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
    def test_add_single_selfserve(
            self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = [False, True]
        apps_mock.make_github_repo_url.return_value = "git cookies"
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies"])

        assert "Juicebox Custom is not running.  Please run jb start with the --custom flag." in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]
        assert apps_mock.mock_calls == []
        assert os_mock.mock_calls == [call.chdir('/Users/casey/projects/devlandia')]
        assert proc_mock.mock_calls == []
        assert "Juicebox Custom is not running.  Please run jb start with the --custom flag" in result.output

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_add_single_api_custom(
            self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        """Adding an app by calling the jb api"""
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = [True, False]
        apps_mock.make_github_repo_url.return_value = "git cookies"
        apiutil_mock.load_app.return_value = True
        apiutil_mock.get_admin_token.return_value = "foo"

        result = invoke(["add", "cookies"])

        assert "Adding cookies..." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert apiutil_mock.mock_calls == [call.load_app(u"cookies", custom=True)]
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
    def test_add_single_api_selfserve(
            self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        """Adding an app by calling the jb api"""
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = [False, True]
        apps_mock.make_github_repo_url.return_value = "git cookies"
        apiutil_mock.load_app.return_value = True
        apiutil_mock.get_admin_token.return_value = "foo"

        result = invoke(["add", "cookies"])

        assert "Juicebox Custom is not running.  Please run jb start with the --custom flag" in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert apiutil_mock.mock_calls == []
        assert apps_mock.mock_calls == []
        assert os_mock.mock_calls == [call.chdir(DEVLANDIA_DIR)]
        assert proc_mock.mock_calls == []

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.os")
    def test_add_app_exists(self, os_mock, dockerutil_mock, apiutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = [True, False]
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies"])

        assert "App cookies already exists." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp cookies", env='custom'),
        ]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    def test_add_not_running(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = [False, False]

        result = invoke(["add", "cookies"])
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert "Juicebox Custom is not running.  Please run jb start with the --custom flag." in result.output
        assert result.exit_code == 1

    @patch("jbcli.cli.jb.dockerutil")
    def test_add_custom_not_running_selfserve_running(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = [False, True]

        result = invoke(["add", "cookies"])
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert "Juicebox Custom is not running.  Please run jb start with the --custom flag." in result.output
        assert result.exit_code == 1

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_add_single(
            self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        apps_mock.make_github_repo_url.return_value = "git cookies"
        dockerutil_mock.is_running.return_value = [True, False]
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies"])

        assert "Adding cookies..." in result.output
        assert "Downloading app cookies from Github." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp cookies", env='custom'),
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        print(os_mock.mock_calls)
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"]),
        ]

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_add_branch(
            self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        apps_mock.make_github_repo_url.return_value = "git cookies"
        dockerutil_mock.is_running.return_value = [True, False]
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies@main"])

        assert "Adding cookies..." in result.output
        assert "Downloading app cookies from Github." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp cookies", env='custom'),
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "-b", "main", "git cookies", "apps/cookies"]),
        ]

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_add_branch_selfserve(
            self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = False
        apps_mock.make_github_repo_url.return_value = "git cookies"
        dockerutil_mock.is_running.return_value = [False, True]
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies@main"])

        assert "Juicebox Custom is not running.  Please run jb start with the --custom flag" in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert apps_mock.mock_calls == []
        assert os_mock.mock_calls == [call.chdir(DEVLANDIA_DIR)]
        assert proc_mock.mock_calls == []

    @patch("jbcli.cli.jb.jbapiutil")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.subprocess")
    @patch("jbcli.cli.jb.os")
    def test_add_branch_app_exists(
            self, os_mock, proc_mock, apps_mock, dockerutil_mock, apiutil_mock
    ):
        os_mock.path.isdir.return_value = True
        apps_mock.make_github_repo_url.return_value = "git cookies"
        dockerutil_mock.is_running.return_value = [True, False]
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies@main"])

        assert "App cookies already exists. Changing to branch main." in result.output
        assert "cookies was added successfully." in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp cookies", env='custom'),
        ]
        assert apps_mock.mock_calls == []
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
            call.chdir('apps/cookies'),
            call.chdir('../..')
        ]
        assert proc_mock.mock_calls == [
            call.check_call(['git', 'fetch']),
            call.check_call(['git', 'checkout', 'main'])
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
        dockerutil_mock.is_running.return_value = [True, False]
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies", "chocolate_chip"])

        assert "Adding cookies..." in result.output
        assert "Adding chocolate_chip"
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp cookies", env='custom'),
            call.run("/venv/bin/python manage.py loadjuiceboxapp chocolate_chip", env='custom'),
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
        dockerutil_mock.is_running.return_value = [True, False]
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
        dockerutil_mock.is_running.return_value = [True, True]
        apps_mock.make_github_repo_url.return_value = "git cookies"
        apiutil_mock.load_app.return_value = False
        apiutil_mock.get_admin_token.return_value = None

        result = invoke(["add", "cookies"])

        print(result.output)
        assert "Adding cookies..." in result.output
        assert "Downloading app cookies from Github." in result.output
        assert "Failed to add cookies to the Juicebox VM" in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp cookies", env='custom'),
        ]
        assert apps_mock.mock_calls == [call.make_github_repo_url(u"cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]
        assert proc_mock.mock_calls == [
            call.check_call(["git", "clone", "git cookies", "apps/cookies"])
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.shutil")
    @patch("jbcli.cli.jb.os")
    def test_remove_single_custom(self, os_mock, shutil_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = [True, False]
        dockerutil_mock.ensure_home.return_value = True

        result = invoke(["remove", "cookies", "--yes"])

        assert "Removing cookies..." in result.output
        assert "Successfully deleted cookies" in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.ensure_home(),
            call.run("/venv/bin/python manage.py deletejuiceboxapp cookies", env='custom'),
        ]
        assert shutil_mock.mock_calls == [call.rmtree("apps/cookies")]
        assert os_mock.mock_calls == [
            call.chdir(DEVLANDIA_DIR),
            call.path.isdir("apps/cookies"),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.shutil")
    @patch("jbcli.cli.jb.os")
    def test_remove_single_selfserve(self, os_mock, shutil_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = [False, True]
        dockerutil_mock.ensure_home.return_value = True

        result = invoke(["remove", "cookies", "--yes"])

        assert "Juicebox Custom is not running.  Run jb start with the --custom flag" in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert shutil_mock.mock_calls == []
        assert os_mock.mock_calls == [call.chdir(DEVLANDIA_DIR)]

    @patch("jbcli.cli.jb.dockerutil")
    def test_remove_not_running(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = [False, False]

        result = invoke(["remove", "cookies", "--yes"])

        assert "Juicebox Custom is not running.  Run jb start with the --custom flag." in result.output
        assert result.exit_code == 1
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
        ]
        assert result.exit_code == 1

    @patch("jbcli.cli.jb.dockerutil")
    def test_remove_not_home(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = [True, False]
        dockerutil_mock.ensure_home.return_value = False

        result = invoke(["remove", "cookies", "--yes"])

        assert "Please run this command from inside the desired environment in Devlandia" in result.output
        assert dockerutil_mock.mock_calls == [call.is_running(), call.ensure_home()]
        assert result.exit_code == 1

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.shutil")
    @patch("jbcli.cli.jb.os")
    def test_remove_multiple(self, os_mock, shutil_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = True
        dockerutil_mock.is_running.return_value = [True, False]
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
            call.run("/venv/bin/python manage.py deletejuiceboxapp cookies", env='custom'),
            call.run("/venv/bin/python manage.py deletejuiceboxapp cake", env='custom'),
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
    def test_watch_custom(self, dockerutil_mock, time_mock, process_mock):
        dockerutil_mock.is_running.return_value = [True, True]
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(["watch", "--custom"])

        assert process_mock.mock_calls == [
            call(
                target=dockerutil_mock.jb_watch,
                kwargs={"app": "", "should_reload": False, "custom": True},
            ),
            call().start(),
            call().join(),
        ]

        assert result.exit_code == 0

    @patch("jbcli.cli.jb.Process")
    @patch("jbcli.cli.jb.time")
    @patch("jbcli.cli.jb.dockerutil")
    def test_watch_selfserve(self, dockerutil_mock, time_mock, process_mock):
        dockerutil_mock.is_running.return_value = [True, True]
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(["watch"])

        assert process_mock.mock_calls == [
            call(
                target=dockerutil_mock.jb_watch,
                kwargs={"app": "", "should_reload": False, "custom": False},
            ),
            call().start(),
            call().join(),
        ]

        assert result.exit_code == 0

    @patch("jbcli.cli.jb.Process")
    @patch("jbcli.cli.jb.time")
    @patch("jbcli.cli.jb.dockerutil")
    def test_watch_for_specific_app(self, dockerutil_mock, time_mock, process_mock):
        dockerutil_mock.is_running.return_value = [True, False]
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(["watch", "--app", "test", "--custom"])

        assert process_mock.mock_calls == [
            call(
                target=dockerutil_mock.jb_watch,
                kwargs={"app": "test", "should_reload": False, "custom": True},
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
        dockerutil_mock.is_running.return_value = [True, True]
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(["watch", "--reload"])
        assert process_mock.mock_calls == [
            call(
                target=dockerutil_mock.jb_watch,
                kwargs={"app": "", "should_reload": True, "custom": False},
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
        dockerutil_mock.is_running.return_value = [True, False]
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(["watch", "--app", "test", "--reload", "--custom"])
        assert process_mock.mock_calls == [
            call(
                target=dockerutil_mock.jb_watch,
                kwargs={"app": "test", "should_reload": True, "custom": True},
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
        dockerutil_mock.is_running.return_value = [True, True]
        dockerutil_mock.ensure_home.return_value = True
        time_mock.sleep.side_effect = KeyboardInterrupt
        result = invoke(["watch", "--includejs", "--custom"])

        assert process_mock.mock_calls == [
            call(
                target=dockerutil_mock.jb_watch,
                kwargs={"app": "", "should_reload": False, "custom": True},
            ),
            call().start(),
            call(target=dockerutil_mock.js_watch),
            call().start(),
            call().join(),
            call().join(),
        ]

        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    def test_stop_custom(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = [True, False]
        dockerutil_mock.ensure_home.return_value = True
        dockerutil_mock.halt.return_value = None
        result = invoke(["stop", "--custom"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.ensure_home(),
            call.is_running(),
            call.halt(custom=True),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    def test_stop_selfserve(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = [False, True]
        dockerutil_mock.ensure_home.return_value = True
        dockerutil_mock.halt.return_value = None
        result = invoke(["stop"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.ensure_home(),
            call.is_running(),
            call.halt(custom=False),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    def test_stop_clean_custom(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = [True, False]
        dockerutil_mock.ensure_home.return_value = True
        dockerutil_mock.destroy.return_value = None
        result = invoke(["stop", "--clean", "--custom"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [call.ensure_home(), call.is_running(), call.destroy(custom=True)]

    @patch("jbcli.cli.jb.dockerutil")
    def test_stop_clean_selfserve(self, dockerutil_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        dockerutil_mock.is_running.return_value = [False, True]
        dockerutil_mock.ensure_home.return_value = True
        dockerutil_mock.destroy.return_value = None
        result = invoke(["stop", "--clean"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [call.ensure_home(), call.is_running(), call.destroy(custom=False)]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_selfserve(self, prompt_mock, auth_mock, os_mock, dockerutil_mock):
        """Starting brings docker-compose up in the environment of the cwd."""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        os_mock.path.isdir.return_value = True
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "develop-py3", "--noupgrade"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="develop-py3"),
            call.up(env=ANY, ganesha=False, custom=False),
        ]
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml'), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None),
            call('.env', 'w'),
            call().__enter__(),
            call().write('DEVLANDIA_PORT=8000\nTAG=develop-py3\nFRUITION=readme\nFILE=unused1\nWORKFLOW=dev\nRECIPE=recipereadme\nRECIPEFILE=unused2\n'),
            call().write('LOCAL_SNAPSHOT_DIR=./nothing\n'),
            call().write('CONTAINER_SNAPSHOT_DIR=/nothing\n'),
            call().__exit__(None, None, None)
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_custom(self, prompt_mock, auth_mock, os_mock, dockerutil_mock):
        """Starting brings docker-compose up in the environment of the cwd."""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        os_mock.path.isdir.return_value = True
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "develop-py3", "--noupgrade", "--custom"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="develop-py3"),
            call.up(env=ANY, ganesha=False, custom=True),
        ]
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml'), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None),
            call('.env', 'w'),
            call().__enter__(),
            call().write(
                'DEVLANDIA_PORT=8000\nTAG=develop-py3\nFRUITION=readme\nFILE=unused1\nWORKFLOW=dev\nRECIPE=recipereadme\nRECIPEFILE=unused2\n'),
            call().write('LOCAL_SNAPSHOT_DIR=./nothing\n'),
            call().write('CONTAINER_SNAPSHOT_DIR=/nothing\n'),
            call().__exit__(None, None, None)
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_with_custom_tag(self, prompt_mock, auth_mock, dockerutil_mock):
        """Starting can occur with any tag."""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "potato", "--noupgrade"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="potato"),
            call.up(env=ANY, ganesha=False, custom=False),
        ]
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml'), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None),
            call('.env', 'w'),
            call().__enter__(),
            call().write('DEVLANDIA_PORT=8000\nTAG=potato\nFRUITION=readme\nFILE=unused1\nWORKFLOW=dev\nRECIPE'
                         '=recipereadme\nRECIPEFILE=unused2\n'),
            call().write('LOCAL_SNAPSHOT_DIR=./nothing\n'),
            call().write('CONTAINER_SNAPSHOT_DIR=/nothing\n'),
            call().__exit__(None, None, None)
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_with_tag_lookup(self, prompt_mock, auth_mock, dockerutil_mock):
        """Starting stable uses the tag master-py3."""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "stable", "--noupgrade"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="master-py3"),
            call.up(env=ANY, ganesha=False, custom=False),
        ]
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml'), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None),
            call('.env', 'w'),
            call().__enter__(),
            call().write('DEVLANDIA_PORT=8000\nTAG=master-py3\nFRUITION=readme\nFILE=unused1\nWORKFLOW=dev\nRECIPE'
                         '=recipereadme\nRECIPEFILE=unused2\n'),
            call().write('LOCAL_SNAPSHOT_DIR=./nothing\n'),
            call().write('CONTAINER_SNAPSHOT_DIR=/nothing\n'),
            call().__exit__(None, None, None)
        ]

    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_core_without_fruitiondir(self, prompt_mock, auth_mock, dockerutil_mock, os_mock):
        """Starting core requires a fruition directory."""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        os_mock.environ.return_value = False
        os_mock.path.join.return_value = ""
        os_mock.getcwd.return_value = ""
        os_mock.path.exists.return_value = False
        os_mock.symlink.return_value = False
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "core", "--noupgrade"])
        assert result.exit_code == 1
        print(result.output)
        assert "Could not find Local Fruition Checkout" in result.output
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml'), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None)
        ]

    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_core_without_fruitioncustomdir(self, prompt_mock, auth_mock, dockerutil_mock, os_mock):
        """Starting core requires a fruition directory."""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        os_mock.environ.return_value = False
        os_mock.path.join.return_value = ""
        os_mock.getcwd.return_value = ""
        os_mock.path.exists.return_value = False
        os_mock.symlink.return_value = False
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "core", "--noupgrade", "--custom"])
        assert result.exit_code == 1
        print(result.output)
        assert "Could not find Local Fruition Custom Checkout, please check that it is symlinked to the top level of Devlandia" in result.output
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml'), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None)
        ]

    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_core_with_fruitiondir(self, prompt_mock, auth_mock, dockerutil_mock, os_mock):
        """Starting core requires a fruition directory."""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        os_mock.environ.return_value = False
        os_mock.path.join.return_value = ""
        os_mock.getcwd.return_value = ""
        os_mock.path.exists.return_value = True
        os_mock.symlink.return_value = False
        prompt_mock.isatty.return_value = 'istty'

        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "core", "--noupgrade"])
        assert result.exit_code == 0
        # We link the fruition/ directory with .env
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser(expanduser('~/.config/juicebox/devlandia.toml')), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None),
            call('.env', 'w'),
            call().__enter__(),
            call().write('DEVLANDIA_PORT=8000\nTAG=develop-py3\nFRUITION=fruition\nFILE=code\nWORKFLOW=core\nRECIPE'
                         '=recipereadme\nRECIPEFILE=unused2\n'),
            call().write('LOCAL_SNAPSHOT_DIR=./nothing\n'),
            call().write('CONTAINER_SNAPSHOT_DIR=/nothing\n'),
            call().__exit__(None, None, None)
            ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="develop-py3"),
            call.up(env=ANY, ganesha=False, custom=False),
        ]

    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_core_with_fruitiondir_custom(self, prompt_mock, auth_mock, dockerutil_mock, os_mock):
        """Starting core requires a fruition directory."""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        os_mock.environ.return_value = False
        os_mock.path.join.return_value = ""
        os_mock.getcwd.return_value = ""
        os_mock.path.exists.return_value = True
        os_mock.symlink.return_value = False
        prompt_mock.isatty.return_value = 'istty'

        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "core", "--noupgrade", "--custom"])
        assert result.exit_code == 0
        # We link the fruition/ directory with .env
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser(expanduser('~/.config/juicebox/devlandia.toml')), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None),
            call('.env', 'w'),
            call().__enter__(),
            call().write('DEVLANDIA_PORT=8000\nTAG=develop-py3\nFRUITION=fruition_custom\nFILE=code\nWORKFLOW=prod-custom\nRECIPE'
                         '=recipereadme\nRECIPEFILE=unused2\n'),
            call().write('LOCAL_SNAPSHOT_DIR=./nothing\n'),
            call().write('CONTAINER_SNAPSHOT_DIR=/nothing\n'),
            call().__exit__(None, None, None)
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="develop-py3"),
            call.up(env=ANY, ganesha=False, custom=True),
        ]

    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_core_with_fruitiondir_and_recipe(self, prompt_mock, auth_mock, dockerutil_mock, os_mock):
        """Starting core requires a fruition directory."""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        os_mock.environ.return_value = False
        os_mock.path.join.return_value = ""
        os_mock.getcwd.return_value = ""
        os_mock.path.exists.return_value = True
        os_mock.symlink.return_value = False
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "core", "--noupgrade", "--dev-recipe"])
        assert result.exit_code == 0
        # We link the fruition/ directory with .env
        # We ALSO link the recipe/ directory
        print(m.mock_calls)
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml'), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None),
            call('.env', 'w'),
            call().__enter__(),
            call().write(
                'DEVLANDIA_PORT=8000\nTAG=develop-py3\nFRUITION=fruition\nFILE=code\nWORKFLOW=core\nRECIPE=recipe\nRECIPEFILE=code/recipe\n'),
            call().write('LOCAL_SNAPSHOT_DIR=./nothing\n'),
            call().write('CONTAINER_SNAPSHOT_DIR=/nothing\n'),
            call().__exit__(None, None, None)
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="develop-py3"),
            call.up(env=ANY, ganesha=False, custom=False),
        ]

    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_core_with_fruitiondir_and_recipe_no_recipe_dir(self, prompt_mock, auth_mock, dockerutil_mock, os_mock):
        """Starting core requires a fruition directory."""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        os_mock.environ.return_value = False
        os_mock.path.join.return_value = ""
        os_mock.getcwd.return_value = ""
        os_mock.path.exists.side_effect = [True, False]
        os_mock.symlink.return_value = False
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "core", "--noupgrade", "--dev-recipe"])
        assert result.exit_code == 1
        # We link the fruition/ directory with .env
        # We ALSO link the recipe/ directory
        print(m.mock_calls)
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml'), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None)
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]

        assert "Could not find local recipe checkout" in result.output

    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_nocore_with_fruitiondir_and_recipe(self, prompt_mock, auth_mock, dockerutil_mock,os_mock):
        """Starting with the dev-recipe flag requires the core flag too"""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        os_mock.environ.return_value = False
        os_mock.path.join.return_value = ""
        os_mock.getcwd.return_value = ""
        os_mock.path.exists.side_effect = [True, True]
        os_mock.symlink.return_value = False
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "dev", "--dev-recipe"])
        assert result.exit_code == 1
        # We link the fruition/ directory with .env
        # We ALSO link the recipe/ directory
        print(m.mock_calls)
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml'), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None)
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running()
        ]

        assert "The dev-recipe flag requires running a core environment" in result.output

    @patch("jbcli.cli.jb.os")
    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_core_with_fruitiondir_and_recipe_custom(self, prompt_mock, auth_mock, dockerutil_mock, os_mock):
        """Starting core requires a fruition directory."""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        os_mock.environ.return_value = False
        os_mock.path.join.return_value = ""
        os_mock.getcwd.return_value = ""
        os_mock.path.exists.return_value = True
        os_mock.symlink.return_value = False
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "core", "--noupgrade", "--dev-recipe", "--custom"])
        assert result.exit_code == 0
        # We link the fruition/ directory with .env
        # We ALSO link the recipe/ directory
        print(m.mock_calls)
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml'), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None),
            call('.env', 'w'),
            call().__enter__(),
            call().write(
                'DEVLANDIA_PORT=8000\nTAG=develop-py3\nFRUITION=fruition_custom\nFILE=code\nWORKFLOW=prod-custom\nRECIPE=recipe\nRECIPEFILE=code/recipe\n'),
            call().write('LOCAL_SNAPSHOT_DIR=./nothing\n'),
            call().write('CONTAINER_SNAPSHOT_DIR=/nothing\n'),
            call().__exit__(None, None, None)
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="develop-py3"),
            call.up(env=ANY, ganesha=False, custom=True),
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_noupgrade_selfserve(self, prompt_mock, auth_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "develop-py3", "--noupgrade"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="develop-py3"),
            call.up(env=ANY, ganesha=False, custom=False),
        ]
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml'), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None),
            call('.env', 'w'),
            call().__enter__(),
            call().write(
                'DEVLANDIA_PORT=8000\nTAG=develop-py3\nFRUITION=readme\nFILE=unused1\nWORKFLOW=dev\nRECIPE=recipereadme\nRECIPEFILE=unused2\n'),
            call().write('LOCAL_SNAPSHOT_DIR=./nothing\n'),
            call().write('CONTAINER_SNAPSHOT_DIR=/nothing\n'),
            call().__exit__(None, None, None)
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch('jbcli.cli.jb.prompt')
    def test_start_noupgrade_custom(self, prompt_mock, auth_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()) as m:
            result = invoke(["start", "develop-py3", "--noupgrade", "--custom"])
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.pull(tag="develop-py3"),
            call.up(env=ANY, ganesha=False, custom=True),
        ]
        assert m.mock_calls == [
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml')),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call(expanduser('~/.config/juicebox/devlandia.toml'), 'w'),
            call().__enter__(),
            call().write('[[users]]\nfirstname = []\nlastname = []\nemail = []\nuser_extra = []\n\n'),
            call().__exit__(None, None, None),
            call('.env', 'w'),
            call().__enter__(),
            call().write(
                'DEVLANDIA_PORT=8000\nTAG=develop-py3\nFRUITION=readme\nFILE=unused1\nWORKFLOW=dev\nRECIPE=recipereadme\nRECIPEFILE=unused2\n'),
            call().write('LOCAL_SNAPSHOT_DIR=./nothing\n'),
            call().write('CONTAINER_SNAPSHOT_DIR=/nothing\n'),
            call().__exit__(None, None, None)
        ]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch("jbcli.cli.jb.check_outdated_image")
    @patch('jbcli.cli.jb.prompt')
    def test_start_noupdate_selfserve(self, image_mock, auth_mock, dockerutil_mock, monkeypatch):
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        image_mock.answer = "no"
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        result = invoke(["start", "develop-py3", "--noupdate", "--noupgrade"])
        assert dockerutil_mock.mock_calls == [
            call.set_creds(),
        ]
        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    @patch("jbcli.cli.jb.check_outdated_image")
    @patch('jbcli.cli.jb.prompt')
    def test_start_noupdate_custom(self, image_mock, auth_mock, dockerutil_mock, monkeypatch):
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.ensure_home.return_value = True
        image_mock.answer = "no"
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        result = invoke(["start", "develop-py3", "--noupdate", "--noupgrade", "--custom"])
        assert dockerutil_mock.mock_calls == [
            call.set_creds(),
        ]
        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    def test_start_already_running_selfserve(self, auth_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = [False, True]
        dockerutil_mock.ensure_home.return_value = True
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        result = invoke(["start", "--noupgrade"])

        assert "An instance of Juicebox Selfserve is already running" in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [call.is_running()]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.auth")
    def test_start_already_running_custom(self, auth_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = [True, False]
        dockerutil_mock.ensure_home.return_value = True
        auth_mock.deduped_mfas = ["arn:aws:iam::423681189101:mfa/TestMFA"]
        result = invoke(["start", "--noupgrade", "--custom"])

        assert "An instance of Juicebox Custom is already running" in result.output
        assert result.exit_code == 0
        assert dockerutil_mock.mock_calls == [call.is_running()]

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.os")
    def test_clone_custom(self, os_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.side_effect = [True, False]
        apps_mock.clone.return_value = "git cookies"
        dockerutil_mock.is_running.return_value = [True, True]
        result = invoke(["clone", "cookies", "chocolate_chip", "--custom"])

        assert apps_mock.mock_calls == [
            call.clone(
                u"chocolate_chip",
                "apps/cookies",
                "apps/chocolate_chip",
                init_vcs=True,
                track_vcs=True,
                custom=True,
            )
        ]
        assert os_mock.mock_calls == [
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/chocolate_chip"),
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp chocolate_chip", env='custom'),
        ]
        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.os")
    def test_clone_selfserve(self, os_mock, apps_mock, dockerutil_mock):
        os_mock.path.isdir.side_effect = [False, True]
        apps_mock.clone.return_value = "git cookies"
        dockerutil_mock.is_running.return_value = [True, True]
        result = invoke(["clone", "cookies", "chocolate_chip"])

        assert apps_mock.mock_calls == []
        assert os_mock.mock_calls == []
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert result.exit_code == 1

    @patch("jbcli.cli.jb.dockerutil")
    def test_clone_running_fail(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = [False, False]

        result = invoke(["clone", "cookies", "chocolate_chip"])

        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert result.exit_code == 1
        assert "Juicebox Custom is not running.  Run jb start with the --custom flag." in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.os")
    def test_clone_from_nonexist_custom(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = [True, False]
        result = invoke(["clone", "cookies", "chocolate_chip", "--custom"])

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
    def test_clone_from_nonexist_selfserve(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.return_value = False
        dockerutil_mock.is_running.return_value = [False, True]
        result = invoke(["clone", "cookies", "chocolate_chip"])

        assert os_mock.mock_calls == []
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
        ]
        assert result.exit_code == 1
        assert "Juicebox Custom is not running.  Run jb start with the --custom flag." in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.os")
    def test_clone_to_exists_custom(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.side_effect = [True, True]
        dockerutil_mock.is_running.return_value = [True, False]

        result = invoke(["clone", "cookies", "chocolate_chip", "--custom"])

        assert os_mock.mock_calls == [
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/chocolate_chip"),
        ]
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert result.exit_code == 1
        assert "App chocolate_chip already exists." in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.os")
    def test_clone_to_exists_selfserve(self, os_mock, dockerutil_mock):
        os_mock.path.isdir.side_effect = [True, True]
        dockerutil_mock.is_running.return_value = [False, True]

        result = invoke(["clone", "cookies", "chocolate_chip"])

        assert os_mock.mock_calls == []
        assert dockerutil_mock.mock_calls == [call.is_running()]
        assert result.exit_code == 1
        assert "Juicebox Custom is not running.  Run jb start with the --custom flag." in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.os")
    def test_clone_failed_selfserve(self, os_mock, apps_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = [True, False]
        os_mock.path.isdir.side_effect = [True, False]
        apps_mock.clone.side_effect = ValueError("Cake Bad")

        result = invoke(["clone", "cookies", "chocolate_chip"])

        assert apps_mock.mock_calls == []
        assert os_mock.mock_calls == []
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
        ]
        assert result.exit_code == 1
        assert "Juicebox Custom is not running.  Run jb start with the --custom flag." in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.apps")
    @patch("jbcli.cli.jb.os")
    def test_clone_run_failed_custom(self, os_mock, apps_mock, dockerutil_mock):
        dockerutil_mock.is_running.return_value = [True, False]
        apps_mock.clone.return_value = True
        os_mock.path.isdir.side_effect = [True, False]

        result = invoke(["clone", "cookies", "chocolate_chip", "--custom"])

        assert apps_mock.mock_calls == [
            call.clone(
                u"chocolate_chip",
                "apps/cookies",
                "apps/chocolate_chip",
                init_vcs=True,
                track_vcs=True,
                custom=True,
            )
        ]
        assert os_mock.mock_calls == [
            call.path.isdir("apps/cookies"),
            call.path.isdir("apps/chocolate_chip"),
        ]
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py loadjuiceboxapp chocolate_chip", env='custom'),
        ]
        assert "Cloning from cookies to chocolate_chip" in result.output

    @patch("jbcli.cli.jb.dockerutil")
    def test_clear_cache_custom(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = [True, False]

        result = invoke(["clear_cache", "--custom"])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py clear_cache", env='custom'),
        ]

        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    def test_clear_cache_selfserve(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = [False, True]

        result = invoke(["clear_cache"])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py clear_cache", env='selfserve'),
        ]

        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    def test_clear_cache_not_running(self, dockerutil_mock):
        dockerutil_mock.is_running.return_value = [False, False]

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
    def test_clear_cache_fail_selfserve(self, dockerutil_mock, click_mock):
        dockerutil_mock.is_running.return_value = [False, True]
        dockerutil_mock.run.side_effect = APIError("Failure")
        result = invoke(["clear_cache"])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py clear_cache", env='selfserve'),
        ]
        assert click_mock.mock_calls == [
            call.get_current_context(),
            call.get_current_context().abort(),
        ]
        assert "Could not clear cache" in result.output

    @patch("jbcli.cli.jb.click")
    @patch("jbcli.cli.jb.dockerutil")
    def test_clear_cache_fail_custom(self, dockerutil_mock, click_mock):
        dockerutil_mock.is_running.return_value = [True, False]
        dockerutil_mock.run.side_effect = APIError("Failure")
        result = invoke(["clear_cache", "--custom"])
        assert dockerutil_mock.mock_calls == [
            call.is_running(),
            call.run("/venv/bin/python manage.py clear_cache", env='custom'),
        ]
        assert click_mock.mock_calls == [
            call.get_current_context(),
            call.get_current_context().abort(),
        ]
        assert "Could not clear cache" in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.subprocess")
    @patch('jbcli.cli.jb.prompt')
    # @patch('jbcli.cli.jb._run')
    def test_jb_run_running_no_env_selfserve(self, prompt_mock, subprocess_mock, dockerutil_mock):
        """When a container is running and no --env is given,
        we run the command in the existing container.
        """
        dockerutil_mock.is_running.return_value = [False, True]
        dockerutil_mock.check_home.return_value = None
        subprocess_mock.check_call.return_value = None
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()):
            result = invoke(["run", "foo", "bar"])
        assert subprocess_mock.mock_calls == [call.check_call(['docker', 'exec', '-it', 'devlandia_juicebox_selfserve_1', 'foo', 'bar'])]
        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.subprocess")
    @patch('jbcli.cli.jb.prompt')
    # @patch('jbcli.cli.jb._run')
    def test_jb_run_running_no_env_custom(self, prompt_mock, subprocess_mock, dockerutil_mock):
        """When a container is running and no --env is given,
        we run the command in the existing container.
        """
        dockerutil_mock.is_running.return_value = [True, False]
        dockerutil_mock.check_home.return_value = None
        subprocess_mock.check_call.return_value = None
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()):
            result = invoke(["run", "foo", "bar", "--custom"])
        assert subprocess_mock.mock_calls == [
            call.check_call(['docker', 'exec', '-it', 'devlandia_juicebox_custom_1', 'foo', 'bar'])]
        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    @patch('jbcli.cli.jb.prompt')
    def test_jb_manage_not_running_no_env_selfserve(self, prompt_mock, dockerutil_mock):
        """When no container is running, and no --env is given, we give up."""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.check_home.return_value = None
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()):
            result = invoke(["manage", "test"])
        assert "Juicebox Selfserve instance is not running.  Run jb start." in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch('jbcli.cli.jb.prompt')
    def test_jb_manage_not_running_no_env_custom(self, prompt_mock, dockerutil_mock):
        """When no container is running, and no --env is given, we give up."""
        dockerutil_mock.is_running.return_value = [False, False]
        dockerutil_mock.check_home.return_value = None
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()):
            result = invoke(["manage", "test", "--custom"])
        assert "\nJuicebox Custom instance is not running.  Run jb start with the --custom flag." in result.output

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.subprocess")
    @patch('jbcli.cli.jb.prompt')
    def test_jb_manage_running_matching_env_selfserve(self, prompt_mock, subprocess_mock, dockerutil_mock):
        """When an --env is given, and it matches a running JB container,
        we use the running container.
        """
        dockerutil_mock.is_running.return_value = [False, True]
        dockerutil_mock.check_home.return_value = None
        subprocess_mock.check_call.return_value = None
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()):
            result = invoke(["manage", "--env", "core", "test"])
        assert subprocess_mock.mock_calls == [
            call.check_call(
                [
                    "docker",
                    "exec",
                    "-it",
                    "devlandia_juicebox_selfserve_1",
                    "/venv/bin/python",
                    "manage.py",
                    "test",
                ]
            )
        ]
        assert result.exit_code == 0

    @patch("jbcli.cli.jb.dockerutil")
    @patch("jbcli.cli.jb.subprocess")
    @patch('jbcli.cli.jb.prompt')
    def test_jb_manage_running_matching_env_custom(self, prompt_mock, subprocess_mock, dockerutil_mock):
        """When an --env is given, and it matches a running JB container,
        we use the running container.
        """
        dockerutil_mock.is_running.return_value = [True, False]
        dockerutil_mock.check_home.return_value = None
        subprocess_mock.check_call.return_value = None
        prompt_mock.isatty.return_value = 'istty'
        with patch("builtins.open", mock_open()):
            result = invoke(["manage", "--env", "core", "test", "--custom"])
        assert subprocess_mock.mock_calls == [
            call.check_call(
                [
                    "docker",
                    "exec",
                    "-it",
                    "devlandia_juicebox_custom_1",
                    "/venv/bin/python",
                    "manage.py",
                    "test",
                ]
            )
        ]
        assert result.exit_code == 0