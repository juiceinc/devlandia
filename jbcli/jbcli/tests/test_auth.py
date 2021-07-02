from __future__ import print_function

import os
from mock import call, mock_open, patch, ANY, mock
import pytest

from ..cli.jb import auth

class TestAuth(object):

    @patch('jbcli.cli.jb.auth')
    @mock.patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "supersecretkey"}, clear = True)
    def test_creds_in_env(self, auth_mock):
        print(os.environ)
        auth.set_creds()
        assert 'AWS_ACCESS_KEY_ID' in os.environ
