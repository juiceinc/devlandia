from __future__ import print_function

import os

from mock import patch, mock, call

from ..cli.jb import auth


class TestAuth(object):
    @patch('jbcli.cli.jb.auth')
    @mock.patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "supersecretkey"}, clear=True)
    def test_creds_in_env(self, auth_mock):
        auth_mock.set_creds()
        assert 'AWS_ACCESS_KEY_ID' in os.environ

    @patch("jbcli.cli.jb.auth.set_creds")
    @patch('jbcli.cli.jb.os.open')
    @mock.patch.dict(os.environ, {"NOPE": "nosupersecretkey"}, clear=True)
    @patch('builtins.input', lambda *args: '111111')
    def test_no_mfa_devices(self, os_mock, auth_mock):
        assert 'AWS_ACCESS_KEY_ID' not in os.environ
        with patch("builtins.open", os_mock(read_data=""), ) as m:
            auth_mock.deduped_mfas.return_value = ['']
            assert call.set_creds()
            auth_mock.set_creds()
            assert m.calls == os_mock().calls
            assert input() == '111111'

    @patch("jbcli.cli.jb.auth.set_creds")
    @patch("jbcli.cli.jb.os")
    @mock.patch.dict(os.environ, {"NOTTHEKEY": "notsupersecretkey"}, clear=True)
    def test_one_mfa(self, os_mock, auth_mock):
        with patch("builtins.open",
                   os_mock(read_data="[default]\nregion=us-east-1\n""output=json\nmfa_serial=arn:aws:iam"
                                     "::423681189101:mfa/test.mfa"), ) as m:
            auth_mock.set_creds()
            assert "AWS_ACCESS_KEY_ID" not in os.environ
            assert auth_mock.deduped_mfas.return_value == ['arn:aws:iam::423681189101:mfa/test.mfa2']
            assert m.calls == os_mock().calls
            assert auth_mock.mock_calls == [call.set_creds()]
