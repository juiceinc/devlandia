from builtins import object
from unittest.mock import call, patch, ANY, mock_open

from ..utils.storageutil import Stash


class TestStash(object):

    @patch('jbcli.utils.storageutil.os')
    def test_init(self, os_mock):
        os_mock.path.exists.return_value = True
        os_mock.path.dirname.return_value = 'foo'
        os_mock.path.abspath.return_value = 'moo'

        # Default values
        s = Stash()
        assert os_mock.mock_calls == [
            call.path.expanduser('~/.config/juicebox/devlandia.toml'),
            call.path.abspath(ANY),
            call.path.dirname('moo'),
            call.path.exists('foo')]
        assert s.local_filename == 'moo'
        
        # Custom file
        os_mock.reset_mock()
        s = Stash('foo.toml')
        assert os_mock.mock_calls == [
            call.path.expanduser('foo.toml'),
            call.path.abspath(ANY),
            call.path.dirname('moo'),
            call.path.exists('foo')]

    @patch('jbcli.utils.storageutil.os')
    def test_data(self, os_mock):
        """ Test read and write """
        os_mock.path.exists.return_value = True
        os_mock.path.dirname.return_value = 'foo'
        os_mock.path.abspath.return_value = 'moo'

        with patch('six.moves.builtins.open', mock_open(read_data='hi = "there"')) as m:
            s = Stash()
            assert s.data == {'hi': 'there'}

            s.put('eat', 'cookie')
            assert call().write(u'hi = "there"\neat = "cookie"\n') in m.mock_calls
