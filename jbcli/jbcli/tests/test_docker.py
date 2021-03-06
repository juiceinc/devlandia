import os
import json
import time
from collections import namedtuple
from datetime import datetime, timedelta

from mock import call, patch, ANY

from ..utils import dockerutil
from ..cli.jb import DEVLANDIA_DIR


class TestDocker:
    @patch('jbcli.utils.dockerutil.check_call')
    def test_up(self, check_mock):
        dockerutil.up()
        assert check_mock.mock_calls == [
            call(['docker-compose',
                  '--project-directory', '.', '--project-name', 'stable',
                  '-f', '../docker-compose.common.yml', '-f', 'docker-compose.yml',
                  'up',
                  '--abort-on-container-exit'], env=None)
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    def test_destroy(self, check_mock):
        dockerutil.destroy()
        assert check_mock.mock_calls == [
            call(['docker-compose',
                  '--project-directory', '.', '--project-name', 'stable',
                  '-f', '../docker-compose.common.yml', '-f', 'docker-compose.yml',
                  'down'], env=None)
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    def test_halt(self, check_mock):
        dockerutil.halt()
        assert check_mock.mock_calls == [
            call(['docker-compose',
                  '--project-directory', '.', '--project-name', 'stable',
                  '-f', '../docker-compose.common.yml', '-f', 'docker-compose.yml',
                  'stop'], env=None)
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.utils.dockerutil.glob')
    def test_multiple_docker_compose_files(self, glob_mock, check_mock):
        """When additional `docker-compose-*.yml` files are available, they
        are passed to `docker-compose`.
        """
        glob_mock.return_value = [
            'docker-compose-coolio.yml', 'docker-compose-2pac.yml']
        dockerutil.up()
        assert check_mock.mock_calls == [
            call([
                'docker-compose',
                '--project-directory', '.',
                '--project-name', 'stable',
                '-f', '../docker-compose.common.yml',
                '-f', 'docker-compose.yml',
                '-f', 'docker-compose-coolio.yml',
                '-f', 'docker-compose-2pac.yml',
                'up',
                '--abort-on-container-exit',
            ], env=None)
        ]

    @patch('jbcli.utils.dockerutil.client')
    def test_get_state_running(self, dockerutil_mock):
        Container = namedtuple('Container', ['status'])
        dockerutil_mock.containers.get('stable_juicebox_1').status = Container(
            status='running')
        result = dockerutil.get_state('stable_juicebox_1')
        assert 'running' in result

    @patch('jbcli.utils.dockerutil.client')
    def test_get_state_exited(self, dockerutil_mock):
        Container = namedtuple('Container', ['status'])
        dockerutil_mock.containers.get('stable_juicebox_1').status = Container(
            status='exited')
        result = dockerutil.get_state('stable_juicebox_1')
        assert 'exited' in result

    @patch('jbcli.utils.dockerutil.click')
    def test_ensure_home(self, click_mock, monkeypatch):
        for env in ['core', 'test', 'hstm-core']:
            monkeypatch.chdir(os.path.join(DEVLANDIA_DIR, 'environments', env))
            dockerutil.ensure_home()

    @patch('jbcli.utils.dockerutil.click')
    @patch('jbcli.utils.dockerutil.os')
    def test_ensure_home_missing_apps(self, os_mock, click_mock):
        os_mock.path.isfile.return_value = True
        os_mock.path.isdir.return_value = False
        dockerutil.ensure_home()
        assert os_mock.mock_calls == [
            call.path.isfile('docker-compose.yml'),
            call.path.isdir('../../apps'),
        ]
        assert click_mock.mock_calls == [
            call.get_current_context(),
            call.get_current_context().abort()
        ]

    @patch('jbcli.utils.dockerutil.click')
    @patch('jbcli.utils.dockerutil.os')
    def test_ensure_home_missing_dc_file(self, os_mock, click_mock):
        os_mock.path.isfile.return_value = False
        dockerutil.ensure_home()
        assert os_mock.mock_calls == [
            call.path.isfile('docker-compose.yml'),
        ]
        assert click_mock.mock_calls == [
            call.get_current_context(),
            call.get_current_context().abort()
        ]

    @patch('jbcli.utils.dockerutil.run')
    def test_run(self, run_mock):
        dockerutil.run('COOKIES!')
        assert run_mock.mock_calls == [
            call('COOKIES!')
        ]

    @patch('jbcli.utils.dockerutil.client')
    def test_is_running_up(self, dockerutil_mock):
        Container = namedtuple('Container', ['name'])
        dockerutil_mock.containers.list.return_value = [
            Container(name='cookie'), Container(name='stable_juicebox_1')]
        result = dockerutil.is_running()
        assert result == Container(name='stable_juicebox_1')

    @patch('jbcli.utils.dockerutil.client')
    def test_is_running_down(self, dockerutil_mock):
        Container = namedtuple('Container', ['name'])
        dockerutil_mock.containers.list.return_value = [Container(name='cookie')]
        result = dockerutil.is_running()
        assert result is None

    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.utils.dockerutil.check_output')
    def test_pull(self, check_output_mock, check_mock, monkeypatch):
        monkeypatch.chdir(os.path.join(DEVLANDIA_DIR, 'environments', 'core'))

        def check_output(args):
            assert args == [
                'aws', 'ecr', 'get-login',
                '--registry-ids', '423681189101', '976661725066',
                '--no-include-email']
            return b"do a thing!"

        check_output_mock.side_effect = check_output

        dockerutil.pull('latest')

        assert check_mock.mock_calls == [
            call([b"do", b"a", b"thing!"]),
            call(['docker', 'pull',
                  '423681189101.dkr.ecr.us-east-1.amazonaws.com/juicebox-devlandia:latest'])
        ]

    @patch('jbcli.utils.dockerutil.check_output')
    def test_image_list(self, check_mock):
        def _make_image_details(tag, td):
                dt = datetime.now() - td
                ts = time.mktime(dt.timetuple())
                return {
                    "imageSizeInBytes": 1,
                    "imageDigest": "sha256:abcd",
                    "imageTags": [
                        tag
                    ],
                    "registryId": "423681189101",
                    "repositoryName": "juicebox-devlandia",
                    "imagePushedAt": ts
                }

        check_mock.return_value = json.dumps({
            'imageDetails': [
                _make_image_details('master', timedelta(seconds=30)),
                _make_image_details('3.22.1', timedelta(days=120)),
            ]
        })

        output = dockerutil.image_list(showall=False, print_flag=False)
        assert check_mock.mock_calls == [
            call(
                "aws ecr describe-images --registry-id 423681189101 --repository-name juicebox-devlandia".split())
        ]

        for o in output:
            o.pop(1)
        assert output == [
            [u'master', '30 seconds ago', 4, False, None]
        ]

        output = dockerutil.image_list(showall=True, print_flag=False)

        for o in output:
            o.pop(1)
        assert output == [
            [u'master', '30 seconds ago', 4, False, u'3.22.1'], 
            [u'3.22.1', '3 months ago', 2, True, None]
        ]

        # Semantic flag gets only semantic tags
        output = dockerutil.image_list(showall=True, print_flag=False, semantic=True)

        for o in output:
            o.pop(1)
        assert output == [
            [u'3.22.1', '3 months ago', 2, True, None]
        ]
