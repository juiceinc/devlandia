from mock import call, patch

from ..utils.format import (
    echo_success, echo_warning, echo_highlight, human_readable_timediff
)
from datetime import datetime, timedelta


class TestFormat:

    @patch('jbcli.utils.format.secho')
    def test_echo_highlight(self, secho_mock):
        echo_highlight('COOKIES!')
        assert secho_mock.mock_calls == [
            call('COOKIES!', fg='yellow', bold=True)
        ]

    @patch('jbcli.utils.format.secho')
    def test_echo_success(self, secho_mock):
        echo_success('COOKIES!')
        assert secho_mock.mock_calls == [
            call('COOKIES!', fg='green', bold=True)
        ]

    @patch('jbcli.utils.format.secho')
    def test_echo_warning(self, secho_mock):
        echo_warning('COOKIES!')
        assert secho_mock.mock_calls == [
            call('COOKIES!', fg='red', bold=True)
        ]


class TestTimeDiff:

    def test_human_readable_timediff(self):
        v = human_readable_timediff(datetime.now() - timedelta(minutes=30))
        assert v == '30 minutes ago'

        v = human_readable_timediff(datetime.now() - timedelta(days=2) - timedelta(minutes=30))
        assert v == '2 days, 30 minutes ago'

