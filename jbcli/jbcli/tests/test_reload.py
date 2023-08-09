from mock import call, patch, Mock
import requests
import requests_mock
from ..utils.reload import ( create_browser_instance, refresh_browser, )


class TestReload():

    @patch('jbcli.utils.reload.check_output')
    def test_create_browser_instance_custom(self, output_mock):
        create_browser_instance(custom=True)
        assert output_mock.mock_calls == [
            call(['../../node_modules/.bin/browser-sync', 'start', '--proxy=localhost:8001'])
        ]

    @patch('jbcli.utils.reload.check_output')
    def test_create_browser_instance_selfserve(self, output_mock):
        create_browser_instance(custom=False)
        assert output_mock.mock_calls == [
            call(['../../node_modules/.bin/browser-sync', 'start', '--proxy=localhost:8000'])
        ]

    @patch('jbcli.utils.reload.check_output')
    def test_refresh_browser_timeout_none(self, output_mock):
        refresh_browser(timeout=None)
        assert output_mock.mock_calls == [
            call(['../../node_modules/.bin/browser-sync','reload'])
        ]

    @patch('time.sleep', return_value=None)
    @patch('jbcli.utils.reload.check_output')
    def test_refresh_browser_with_timeout_selfserve(self, output_mock, sleep_mock):
        mock_response = Mock()
        mock_response.status_code = 200
        refresh_browser(custom=False, timeout=1)
        assert output_mock.mock_calls == [
            call(['../../node_modules/.bin/browser-sync','reload'])
        ]

    @patch('time.sleep', return_value=None)
    @patch('jbcli.utils.reload.check_output')
    def test_refresh_browser_with_timeout_custom(self, output_mock, sleep_mock):
        mock_response = Mock()
        mock_response.status_code = 200
        refresh_browser(custom=True, timeout=1)
        assert output_mock.mock_calls == [
            call(['../../node_modules/.bin/browser-sync', 'reload'])
        ]

    @patch('jbcli.utils.reload.get')
    @patch('jbcli.utils.reload.echo_highlight')
    @patch('jbcli.utils.reload.echo_warning')
    @patch('time.sleep', return_value=None)
    def test_refresh_browser_with_timeout_custom_connection_error(self, sleep_mock, echo_warning_mock, echo_highlight_mock, get_mock):
        get_mock.side_effect = requests.exceptions.ConnectionError()
        refresh_browser(custom=True, timeout=1)
        assert echo_highlight_mock.mock_calls == [
            call('Checking server status...'),
            call('Still checking...'),
            call('Still checking...'),
            call('Still checking...'),
            call('Still checking...'),
            call('Still checking...')
        ]
        assert echo_warning_mock.mock_calls == [call('Maximum attempts reached! Something might be wrong.')]