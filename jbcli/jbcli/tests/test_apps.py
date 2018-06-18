import io
import shutil
from subprocess import CalledProcessError

from mock import call, patch, ANY

from ..utils import apps


class TestApps:

    @patch('jbcli.utils.apps.conf')
    def test_make_github_rep_url(self, conf_mock):
        conf_mock.GITHUB_ORGANIZATION = 'cookies'
        conf_mock.GITHUB_REPO_PREFIX = 'peanut_butter-'
        result = apps.make_github_repo_url('sugar')
        assert result == 'git@github.com:cookies/peanut_butter-sugar.git'

    @patch('jbcli.utils.apps.conf')
    def test_make_github_rep_link(self, conf_mock):
        conf_mock.GITHUB_ORGANIZATION = 'cookies'
        conf_mock.GITHUB_REPO_PREFIX = 'peanut_butter-'
        result = apps.make_github_repo_link('sugar')
        assert result == 'https://github.com/cookies/peanut_butter-sugar'

    @patch('jbcli.utils.apps.make_github_repo_url')
    @patch('jbcli.utils.apps.make_github_repo_link')
    @patch('jbcli.utils.apps.os.chdir')
    @patch('jbcli.utils.apps.check_call')
    def test_perform_init_vcs(self, check_mock, cd_mock, link_mock, url_mock):
        url_mock.return_value = 'git@github.com:cookies/sugar'
        link_mock.return_value = 'https://github.com/cookies/sugar'
        apps.perform_init_vcs('sugar', 'apps/sugar', True)

        assert cd_mock.mock_calls == [call('apps/sugar')]
        assert check_mock.mock_calls == [
            call(['git', 'init']),
            call(['git', 'add', '.']),
            call(['git', 'commit', '-m', 'Initial commit']),
            call(['git', 'remote', 'add', 'origin',
                  'git@github.com:cookies/sugar']),
            call(['git', 'push', '-u', 'origin', 'master']),
            call(['github', 'apps/sugar'])
        ]
        assert link_mock.mock_calls == [call('sugar')]
        assert url_mock.mock_calls == [call('sugar')]

    @patch('jbcli.utils.apps.make_github_repo_url')
    @patch('jbcli.utils.apps.make_github_repo_link')
    @patch('jbcli.utils.apps.os.chdir')
    @patch('jbcli.utils.apps.check_call')
    def test_perform_init_vcs_no_track(self, check_mock, cd_mock, link_mock,
                                       url_mock):
        url_mock.return_value = 'git@github.com:cookies/sugar'
        link_mock.return_value = 'https://github.com/cookies/sugar'
        apps.perform_init_vcs('sugar', 'apps/sugar', False)

        assert cd_mock.mock_calls == [call('apps/sugar')]
        assert check_mock.mock_calls == [
            call(['git', 'init']),
            call(['git', 'add', '.']),
            call(['git', 'commit', '-m', 'Initial commit']),
        ]
        assert link_mock.mock_calls == [call('sugar')]
        assert url_mock.mock_calls == [call('sugar')]

    @patch('jbcli.utils.apps.make_github_repo_url')
    @patch('jbcli.utils.apps.make_github_repo_link')
    @patch('jbcli.utils.apps.os.chdir')
    @patch('jbcli.utils.apps.check_call')
    @patch('jbcli.utils.apps.echo_warning')
    def test_perform_init_vcs_git_fail(self, echo_mock, check_mock, cd_mock,
                                       link_mock, url_mock):
        url_mock.return_value = 'git@github.com:cookies/sugar'
        link_mock.return_value = 'https://github.com/cookies/sugar'
        check_mock.side_effect = CalledProcessError(2, 'cmd', 'Ugh Cake')

        apps.perform_init_vcs('sugar', 'apps/sugar', True)

        assert cd_mock.mock_calls == [call('apps/sugar')]
        assert check_mock.mock_calls == [
            call(['git', 'init']),
        ]
        assert link_mock.mock_calls == [call('sugar')]
        assert url_mock.mock_calls == [call('sugar')]
        assert echo_mock.mock_calls == [
            call('Failed to initialize Git repository.')
        ]

    @patch('jbcli.utils.apps.make_github_repo_url')
    @patch('jbcli.utils.apps.make_github_repo_link')
    @patch('jbcli.utils.apps.os.chdir')
    @patch('jbcli.utils.apps.check_call')
    @patch('jbcli.utils.apps.echo_warning')
    def test_perform_init_vcs_push_fail(self, echo_mock, check_mock,
                                        cd_mock, link_mock, url_mock):
        url_mock.return_value = 'git@github.com:cookies/sugar'
        link_mock.return_value = 'https://github.com/cookies/sugar'
        check_mock.side_effect = [True, True, True, True,
                                  CalledProcessError(2, 'cmd', 'Ugh Cake'),
                                  True]

        apps.perform_init_vcs('sugar', 'apps/sugar', True)

        assert cd_mock.mock_calls == [call('apps/sugar')]
        assert check_mock.mock_calls == [
            call(['git', 'init']),
            call(['git', 'add', '.']),
            call(['git', 'commit', '-m', 'Initial commit']),
            call(['git', 'remote', 'add', 'origin',
                  'git@github.com:cookies/sugar']),
            call(['git', 'push', '-u', 'origin', 'master']),
            call(['github', 'apps/sugar'])
        ]
        assert link_mock.mock_calls == [call('sugar')]
        assert url_mock.mock_calls == [call('sugar')]
        assert echo_mock.call_count == 1

    @patch('jbcli.utils.apps.make_github_repo_url')
    @patch('jbcli.utils.apps.make_github_repo_link')
    @patch('jbcli.utils.apps.os.chdir')
    @patch('jbcli.utils.apps.check_call')
    @patch('jbcli.utils.apps.echo_warning')
    def test_perform_init_vcs_desktop_fail(self, echo_mock, check_mock,
                                           cd_mock, link_mock, url_mock):
        url_mock.return_value = 'git@github.com:cookies/sugar'
        link_mock.return_value = 'https://github.com/cookies/sugar'
        check_mock.side_effect = [True, True, True, True, True,
                                  CalledProcessError(2, 'cmd', 'Ugh Cake')]

        apps.perform_init_vcs('sugar', 'apps/sugar', True)

        assert cd_mock.mock_calls == [call('apps/sugar')]
        assert check_mock.mock_calls == [
            call(['git', 'init']),
            call(['git', 'add', '.']),
            call(['git', 'commit', '-m', 'Initial commit']),
            call(['git', 'remote', 'add', 'origin',
                  'git@github.com:cookies/sugar']),
            call(['git', 'push', '-u', 'origin', 'master']),
            call(['github', 'apps/sugar'])
        ]
        assert link_mock.mock_calls == [call('sugar')]
        assert url_mock.mock_calls == [call('sugar')]
        assert echo_mock.call_count == 1

    @patch('jbcli.utils.apps.shutil')
    @patch('jbcli.utils.apps.os')
    @patch('jbcli.utils.apps.replace_in_yaml')
    @patch('jbcli.utils.apps.perform_init_vcs')
    def test_clone(self, vcs_mock, ry_mock, os_mock, sh_mock):
        replacements = {'slug:': 'cookies', 'label:': 'cookies', 'id:': ANY}
        os_mock.listdir.return_value = ['.file', 'flour', 'water']
        os_mock.path.join.return_value = 'apps/cookies/app.yaml'
        apps.clone('cookies', 'apps/sugar', 'apps/cookies')
        assert vcs_mock.mock_calls == [
            call('cookies', 'apps/cookies', True)
        ]
        assert ry_mock.mock_calls == [
            call('apps/cookies/app.yaml', replacements),
        ]
        assert os_mock.mock_calls == [
            call.path.join('apps/cookies', 'app.yaml')
        ]
        assert sh_mock.mock_calls == [
            call.copytree('apps/sugar', 'apps/cookies', ignore=ANY)
        ]

    @patch('jbcli.utils.apps.shutil')
    @patch('jbcli.utils.apps.os')
    @patch('jbcli.utils.apps.replace_in_yaml')
    @patch('jbcli.utils.apps.perform_init_vcs')
    def test_clone_no_init(self, vcs_mock, ry_mock, os_mock, sh_mock):
        replacements = {'slug:': 'cookies', 'label:': 'cookies', 'id:': ANY}
        os_mock.listdir.return_value = ['.file', 'flour', 'water']
        os_mock.path.join.return_value = 'apps/cookies/app.yaml'
        apps.clone('cookies', 'apps/sugar', 'apps/cookies', False)
        assert vcs_mock.mock_calls == []
        assert ry_mock.mock_calls == [
            call('apps/cookies/app.yaml', replacements),
        ]
        assert os_mock.mock_calls == [
            call.path.join('apps/cookies', 'app.yaml'),
        ]
        assert sh_mock.mock_calls == [
            call.copytree('apps/sugar', 'apps/cookies', ignore=ANY)
        ]

    @patch('jbcli.utils.apps.shutil')
    @patch('jbcli.utils.apps.os')
    @patch('jbcli.utils.apps.replace_in_yaml')
    @patch('jbcli.utils.apps.perform_init_vcs')
    def test_clone_no_track(self, vcs_mock, ry_mock, os_mock, sh_mock):
        replacements = {'slug:': 'cookies', 'label:': 'cookies', 'id:': ANY}
        os_mock.listdir.return_value = ['.file', 'flour', 'water']
        os_mock.path.join.return_value = 'apps/cookies/app.yaml'
        apps.clone('cookies', 'apps/sugar', 'apps/cookies', True, False)
        assert vcs_mock.mock_calls == [
            call('cookies', 'apps/cookies', False)
        ]
        assert ry_mock.mock_calls == [
            call('apps/cookies/app.yaml', replacements),
        ]
        assert os_mock.mock_calls == [
            call.path.join('apps/cookies', 'app.yaml'),
        ]
        assert sh_mock.mock_calls == [
            call.copytree('apps/sugar', 'apps/cookies', ignore=ANY)
        ]

    @patch('jbcli.utils.apps.echo_warning')
    @patch('jbcli.utils.apps.shutil.copytree')
    def test_clone_copy_fail(self, sh_mock, echo_mock):
        sh_mock.side_effect = shutil.ExecError()
        apps.clone('cookies', 'apps/sugar', 'apps/cookies')
        assert echo_mock.mock_calls == [
            call('Cloning failed on the copy step'),
        ]
        assert sh_mock.mock_calls == [
            call.copytree('apps/sugar', 'apps/cookies', ignore=ANY)]

    @patch('jbcli.utils.apps.tempfile')
    @patch('jbcli.utils.apps.shutil.move')
    @patch('jbcli.utils.apps.os')
    @patch('__builtin__.open')
    def test_replace_in_yaml(self, open_mock, os_mock, sh_mock, temp_mock):
        replacements = {'slug:': 'cookies', 'label:': 'cookies',
                        'id:': 'aedc2134'}
        new_file = io.StringIO()
        temp_mock.mkstemp.return_value = (1, 2)
        open_mock.side_effect = [
            new_file,
            io.StringIO(u'slug: 1234\nugh: ugh\nlabel: cake\nid: batman')
        ]
        apps.replace_in_yaml('/tmp/cookies.yaml', replacements)
        assert open_mock.mock_calls == [call(2, 'w'),
                                        call('/tmp/cookies.yaml')]
        assert os_mock.mock_calls == [call.close(1),
                                      call.remove('/tmp/cookies.yaml')]
        assert sh_mock.mock_calls == [call.move(2, '/tmp/cookies.yaml')]
        assert temp_mock.mkstemp.call_count == 1
