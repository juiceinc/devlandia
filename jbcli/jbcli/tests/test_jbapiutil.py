from builtins import object
from unittest.mock import call, patch
import requests_mock

from ..utils import jbapiutil


class TestAPIUtil(object):
    def test_get_admin_token(self):
        """Test a successful login. """
        with requests_mock.Mocker() as m:
            url = "{SERVER}/api/v1/jb/api-token-auth/".format(SERVER=jbapiutil.SERVER)
            m.post(url, json={"token": "foo"})

            val = jbapiutil.get_admin_token(refresh_token=True)
            assert val == "foo"

    def test_get_admin_token_failed(self):
        """Test a bad login. """
        with requests_mock.Mocker() as m:
            url = "{SERVER}/api/v1/jb/api-token-auth/".format(SERVER=jbapiutil.SERVER)
            m.post(url, status_code=400)

            val = jbapiutil.get_admin_token(refresh_token=True)
            assert val is None

    @patch("jbcli.utils.jbapiutil.get_admin_token")
    def test_load_app_notoken(self, mock_admin_token):
        """Test app load when no token returned. """
        mock_admin_token.return_value = None

        with requests_mock.Mocker() as m:
            url = "{SERVER}/api/v1/app/load/{APP}/".format(
                SERVER=jbapiutil.SERVER, APP="meow"
            )
            m.post(url, status_code=200, json={"hi": "there"})

            val = jbapiutil.load_app("meow")
            assert val is False

    @patch("jbcli.utils.jbapiutil.get_admin_token")
    def test_load_app_success(self, mock_admin_token):
        """Test a successful app load. """
        mock_admin_token.return_value = "foo"

        with requests_mock.Mocker() as m:
            url = "{SERVER}/api/v1/app/load/{APP}/".format(
                SERVER=jbapiutil.SERVER, APP="meow"
            )
            m.post(url, status_code=200, json={"hi": "there"})

            val = jbapiutil.load_app("meow")
            assert val is True

    @patch("jbcli.utils.jbapiutil.get_admin_token")
    def test_load_app_failure(self, mock_admin_token):
        """Test a failed app load. """
        mock_admin_token.return_value = "foo"

        with requests_mock.Mocker() as m:
            url = "{SERVER}/api/v1/app/load/{APP}/".format(
                SERVER=jbapiutil.SERVER, APP="meow"
            )
            m.post(url, status_code=400, json={"no": "good"})

            val = jbapiutil.load_app("meow")
            assert val is False
