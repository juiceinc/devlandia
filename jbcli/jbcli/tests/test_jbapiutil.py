import requests_mock
from mock import patch

from ..utils import jbapiutil


class TestAPIUtil:
    def test_get_admin_token_custom(self):
        """Test a successful login. """
        with requests_mock.Mocker() as m:
            url = "http://localhost:8001/api/v1/jb/api-token-auth/"
            m.post(url, json={"token": "foo"})

            val = jbapiutil.get_admin_token(refresh_token=True, custom=True)
            assert val == "foo"

    def test_get_admin_token_selfserve(self):
        """Test a successful login. """
        with requests_mock.Mocker() as m:
            url = "http://localhost:8000/api/v1/jb/api-token-auth/"
            m.post(url, json={"token": "foo"})

            val = jbapiutil.get_admin_token(refresh_token=True, custom=False)
            assert val == "foo"

    def test_get_admin_token_failed_custom(self):
        """Test a bad login. """
        with requests_mock.Mocker() as m:
            url = "http://localhost:8001/api/v1/jb/api-token-auth/"
            m.post(url, status_code=400)

            val = jbapiutil.get_admin_token(refresh_token=True, custom=True)
            assert val is None

    def test_get_admin_token_failed_selfserve(self):
        """Test a bad login. """
        with requests_mock.Mocker() as m:
            url = "http://localhost:8000/api/v1/jb/api-token-auth/"
            m.post(url, status_code=400)

            val = jbapiutil.get_admin_token(refresh_token=True, custom=False)
            assert val is None

    @patch("jbcli.utils.jbapiutil.get_admin_token")
    def test_load_app_notoken_custom(self, mock_admin_token):
        """Test app load when no token returned. """
        mock_admin_token.return_value = None

        with requests_mock.Mocker() as m:
            url = "http://localhost:8001/api/v1/app/load/{APP}/".format(APP="meow")
            m.post(url, status_code=200, json={"hi": "there"})

            val = jbapiutil.load_app("meow", custom=True)
            assert val is False

    @patch("jbcli.utils.jbapiutil.get_admin_token")
    def test_load_app_notoken_selfserve(self, mock_admin_token):
        """Test app load when no token returned. """
        mock_admin_token.return_value = None

        with requests_mock.Mocker() as m:
            url = "http://localhost:8000/api/v1/app/load/{APP}/".format(APP="meow")
            m.post(url, status_code=200, json={"hi": "there"})

            val = jbapiutil.load_app("meow", custom=False)
            assert val is False

    @patch("jbcli.utils.jbapiutil.get_admin_token")
    def test_load_app_success_custom(self, mock_admin_token):
        """Test a successful app load. """
        mock_admin_token.return_value = "foo"

        with requests_mock.Mocker() as m:
            url = "http://localhost:8001/api/v1/app/load/{APP}/".format(APP="meow")
            m.post(url, status_code=200, json={"hi": "there"})

            val = jbapiutil.load_app("meow", custom=True)
            assert val is True

    @patch("jbcli.utils.jbapiutil.get_admin_token")
    def test_load_app_success_selfserve(self, mock_admin_token):
        """Test a successful app load. """
        mock_admin_token.return_value = "foo"

        with requests_mock.Mocker() as m:
            url = "http://localhost:8000/api/v1/app/load/{APP}/".format(APP="meow")
            m.post(url, status_code=200, json={"hi": "there"})

            val = jbapiutil.load_app("meow", custom=False)
            assert val is True

    @patch("jbcli.utils.jbapiutil.get_admin_token")
    def test_load_app_failure_custom(self, mock_admin_token):
        """Test a failed app load. """
        mock_admin_token.return_value = "foo"

        with requests_mock.Mocker() as m:
            url = "http://localhost:8001/api/v1/app/load/{APP}/".format(APP="meow")
            m.post(url, status_code=400, json={"no": "good"})

            val = jbapiutil.load_app("meow", custom=True)
            assert val is False
