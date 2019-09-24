import json
import time
from collections import namedtuple
from datetime import datetime, timedelta

from mock import call, patch, ANY

from ..utils import dockerutil


class TestDocker:
    @patch('jbcli.utils.dockerutil.check_call')
    def test_up(self, check_mock):
        dockerutil.up()
        assert check_mock.mock_calls == [
            call(['docker-compose', '-f', 'docker-compose.yml',
                  'up'], env=None)
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    def test_destroy(self, check_mock):
        dockerutil.destroy()
        assert check_mock.mock_calls == [
            call(['docker-compose', '-f', 'docker-compose.yml',
                  'down'], env=None)
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    def test_halt(self, check_mock):
        dockerutil.halt()
        assert check_mock.mock_calls == [
            call(['docker-compose', '-f', 'docker-compose.yml',
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
                '-f', 'docker-compose.yml',
                '-f', 'docker-compose-coolio.yml',
                '-f', 'docker-compose-2pac.yml',
                'up',
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
    @patch('jbcli.utils.dockerutil.os')
    def test_ensure_home_no_hstm(self, os_mock, click_mock):
        os_mock.path.isfile.return_value = True
        os_mock.path.isdir.return_value = True
        os_mock.getcwd.return_value = "NotHealthStream"
        dockerutil.ensure_home()
        assert os_mock.mock_calls == [
            call.path.isfile('docker-compose.yml'),
            call.path.isdir('../../apps'),
            call.getcwd()
        ]

    @patch('jbcli.utils.dockerutil.click')
    @patch('jbcli.utils.dockerutil.os')
    def test_ensure_home_hstm(self, os_mock, click_mock):
        os_mock.path.isfile.return_value = True
        os_mock.path.isdir.return_value = True
        os_mock.getcwd.return_value = "hstm-"
        dockerutil.ensure_home()
        assert os_mock.mock_calls == [
            call.path.isfile('docker-compose.yml'),
            call.path.isdir('../../apps'),
            call.getcwd(),
            call.environ.__setitem__('AWS_PROFILE', 'hstm')
        ]

    @patch('jbcli.utils.dockerutil.click')
    @patch('jbcli.utils.dockerutil.os')
    def test_ensure_home_missing_apps(self, os_mock, click_mock):
        os_mock.path.isfile.return_value = True
        os_mock.path.isdir.return_value = False
        os_mock.getcwd.return_value = "NoHealthStream"
        dockerutil.ensure_home()
        assert os_mock.mock_calls == [
            call.path.isfile('docker-compose.yml'),
            call.path.isdir('../../apps'),
            call.getcwd()
        ]
        assert click_mock.mock_calls == [
            call.get_current_context(),
            call.get_current_context().abort()
        ]

    @patch('jbcli.utils.dockerutil.click')
    @patch('jbcli.utils.dockerutil.os')
    def test_ensure_home_missing_dc_file(self, os_mock, click_mock):
        os_mock.path.isfile.return_value = False
        os_mock.getcwd.return_value = "NoHealthStream"
        dockerutil.ensure_home()
        assert os_mock.mock_calls == [
            call.path.isfile('docker-compose.yml'),
            call.getcwd()
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

    @patch('jbcli.utils.dockerutil.get_state')
    @patch('jbcli.utils.dockerutil.client')
    def test_is_running_up(self, dockerutil_mock, state_mock):
        state_mock.return_value = 'running'
        Container = namedtuple('Container', ['name'])
        dockerutil_mock.containers.list.return_value = [
            Container(name='cookie'), Container(name='stable_juicebox_1')]
        result = dockerutil.is_running()
        assert result is True

    @patch('jbcli.utils.dockerutil.get_state')
    @patch('jbcli.utils.dockerutil.client')
    def test_is_running_down(self, dockerutil_mock, state_mock):
        state_mock.return_value = 'exited'
        Container = namedtuple('Container', ['name'])
        dockerutil_mock.containers.list.return_value = [
            Container(name='cookie'), Container(name='stable_juicebox_1')]
        result = dockerutil.is_running()
        assert result is False

    @patch('jbcli.utils.dockerutil.os')
    @patch('jbcli.utils.dockerutil.parse_dc_file')
    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.utils.dockerutil.check_output')
    def test_pull(self, check_output_mock, check_mock, parse_mock, os_mock):
        parse_mock.return_value = '423681189101.dkr.ecr.us-east-1.amazonaws.com/juicebox-dev:stable'
        os_mock.path.abspath.return_value = '/path/'
        os_mock.path.isfile.return_value = True
        os_mock.path.isdir.return_value = True
        os_mock.getcwd.return_value = '/path'

        def check_output(args):
            assert args == [
                'aws', 'ecr', 'get-login', '--registry-ids', '423681189101',
                '--no-include-email']
            return "do a thing!"

        check_output_mock.side_effect = check_output
        dockerutil.pull('latest')
        assert check_mock.mock_calls == [
            call(["do", "a", "thing!"]),
            call(['docker', 'pull',
                  '423681189101.dkr.ecr.us-east-1.amazonaws.com/juicebox-dev:stable'])
        ]
        assert os_mock.mock_calls == [
            call.path.isfile('docker-compose.yml'),
            call.path.isdir('../../apps'),
            call.getcwd(),
            call.getcwd(),
            call.path.abspath(os_mock.getcwd.return_value),
            call.chdir('../..'),
            call.chdir(os_mock.path.abspath.return_value)
        ]
        assert parse_mock.mock_calls == [
            call(tag='latest')
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
