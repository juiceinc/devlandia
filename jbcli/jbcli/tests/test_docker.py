import os
import json
import time
from collections import namedtuple
from datetime import datetime, timedelta

from mock import call, patch, ANY

from ..cli.jb import DEVLANDIA_DIR
from ..utils import dockerutil


class TestDocker:
    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.cli.jb.determine_arch')
    def test_up_x86(self, arch_mock, check_mock):
        arch_mock.return_value = 'x86_64'
        dockerutil.up(arch=arch_mock.return_value)
        assert check_mock.mock_calls == [
            call(['docker-compose',
                  '--project-directory', '.', '--project-name', 'devlandia',
                  '-f', 'common-services.yml', '-f', 'docker-compose.selfserve.yml','up'], env=None)
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.cli.jb.determine_arch')
    def test_up_arm(self, arch_mock, check_mock):
        arch_mock.return_value = 'arm'
        dockerutil.up(arch=arch_mock.return_value)
        assert check_mock.mock_calls == [
            call(['docker-compose',
                  '--project-directory', '.', '--project-name', 'devlandia',
                  '-f', 'docker-compose.arm.yml', 'up'], env=None)
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.cli.jb.determine_arch')
    def test_destroy_x86(self, arch_mock, check_mock):
        arch_mock.return_value = 'x86_64'
        dockerutil.destroy(arch=arch_mock.return_value)
        assert check_mock.mock_calls == [
            call(['docker-compose',
                  '--project-directory', '.', '--project-name', 'devlandia',
                  '-f', 'common-services.yml', '-f', 'docker-compose.selfserve.yml', 'down'], env=None)
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.cli.jb.determine_arch')
    def test_destroy_arm(self, arch_mock, check_mock):
        arch_mock.return_value = 'arm'
        dockerutil.destroy(arch=arch_mock.return_value)
        assert check_mock.mock_calls == [
            call(['docker-compose',
                  '--project-directory', '.', '--project-name', 'devlandia',
                  '-f', 'docker-compose.arm.yml', 'down'], env=None)
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.cli.jb.determine_arch')
    def test_halt_x86(self, arch_mock, check_mock):
        arch_mock.return_value = 'x86_64'
        dockerutil.halt(arch=arch_mock.return_value)
        assert check_mock.mock_calls == [
            call(['docker-compose',
                  '--project-directory', '.', '--project-name', 'devlandia',
                  '-f', 'common-services.yml', '-f', 'docker-compose.selfserve.yml', 'stop'], env=None)
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.cli.jb.determine_arch')
    def test_halt_arm(self, arch_mock, check_mock):
        arch_mock.return_value = 'arm'
        dockerutil.halt(arch=arch_mock.return_value)
        assert check_mock.mock_calls == [
            call(['docker-compose',
                  '--project-directory', '.', '--project-name', 'devlandia',
                  '-f', 'docker-compose.arm.yml', 'stop'], env=None)
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.utils.dockerutil.glob')
    def test_multiple_docker_compose_files_x86(self, glob_mock, check_mock):
        """When additional `docker-compose-*.yml` files are available, they
        are passed to `docker-compose`.
        """
        glob_mock.return_value = [
            'docker-compose-coolio.yml', 'docker-compose-2pac.yml']

        dockerutil.up(arch='x86_64')
        assert check_mock.mock_calls == [
            call([
                'docker-compose',
                '--project-directory', '.',
                '--project-name', 'devlandia',
                '-f', 'common-services.yml',
                '-f', 'docker-compose-coolio.yml',
                '-f', 'docker-compose-2pac.yml',
                '-f', 'docker-compose.selfserve.yml',
                'up',
            ], env=None)
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.utils.dockerutil.glob')
    def test_docker_compose_with_ganesha_selfserve(self, glob_mock, check_mock):
        """When additional `docker-compose-*.yml` files are available, they
        are passed to `docker-compose`.
        """
        glob_mock.return_value = [
            'docker-compose-coolio.yml', 'docker-compose-2pac.yml']
        dockerutil.up(ganesha=True, custom=False)
        assert check_mock.mock_calls == [
            call([
                'docker-compose',
                '--project-directory', '.',
                '--project-name', 'devlandia',
                '-f', 'common-services.yml',
                '-f', 'docker-compose-coolio.yml',
                '-f', 'docker-compose-2pac.yml',
                '-f', 'docker-compose.ganesha.yml',
                '-f', 'docker-compose.selfserve.yml',
                'up',
            ], env=None)
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.utils.dockerutil.glob')
    def test_docker_compose_with_ganesha_custom(self, glob_mock, check_mock):
        """When additional `docker-compose-*.yml` files are available, they
        are passed to `docker-compose`.
        """
        glob_mock.return_value = [
            'docker-compose-coolio.yml', 'docker-compose-2pac.yml']
        dockerutil.up(ganesha=True, custom=True)
        assert check_mock.mock_calls == [
            call([
                'docker-compose',
                '--project-directory', '.',
                '--project-name', 'devlandia',
                '-f', 'common-services.yml',
                '-f', 'docker-compose-coolio.yml',
                '-f', 'docker-compose-2pac.yml',
                '-f', 'docker-compose.ganesha.yml',
                '-f', 'docker-compose.custom.yml',
                'up',
            ], env=None),
        ]

    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.utils.dockerutil.glob')
    def test_multiple_docker_compose_files_arm(self, glob_mock, check_mock):
        """When additional `docker-compose-*.yml` files are available, they
        are passed to `docker-compose`.
        """
        glob_mock.return_value = [
            'docker-compose-coolio.yml', 'docker-compose-2pac.yml']
        dockerutil.up(arch='arm')
        assert check_mock.mock_calls == [
            call([
                'docker-compose',
                '--project-directory', '.',
                '--project-name', 'devlandia',
                '-f', 'docker-compose.arm.yml',
                '-f', 'docker-compose-coolio.yml',
                '-f', 'docker-compose-2pac.yml',
                'up',
            ], env=None),
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

    def test_ensure_home(self, monkeypatch):
        for _ in ['core', 'test', 'hstm-newcore']:
            monkeypatch.chdir(DEVLANDIA_DIR)
            dockerutil.ensure_home()

    @patch('jbcli.utils.dockerutil.click')
    @patch('jbcli.utils.dockerutil.os')
    def test_ensure_home_missing_apps(self, os_mock, click_mock):
        os_mock.path.isfile.return_value = True
        os_mock.path.isdir.return_value = False
        dockerutil.ensure_home()
        assert os_mock.mock_calls == [
            call.path.isfile('docker-compose.selfserve.yml'),
            call.path.isdir('apps'),
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
            call.path.isfile('docker-compose.selfserve.yml'),
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
    def test_is_running_up_selfserve(self, dockerutil_mock):
        Container = namedtuple('Container', ['name'])
        dockerutil_mock.containers.list.return_value = [
            Container(name='cookie'), Container(name='juicebox_selfserve')]
        result = dockerutil.is_running()
        # result = dockerutil_mock.is_running().list.return_value = [True, False]
        assert result == [False, True]

    @patch('jbcli.utils.dockerutil.client')
    def test_is_running_up_custom(self, dockerutil_mock):
        Container = namedtuple('Container', ['name'])
        dockerutil_mock.containers.list.return_value = [
            Container(name='cookie'), Container(name='juicebox_custom')]
        result = dockerutil.is_running()
        # result = dockerutil_mock.is_running().list.return_value = [True, False]
        assert result == [True, False]

    @patch('jbcli.utils.dockerutil.client')
    def test_is_running_down(self, dockerutil_mock):
        Container = namedtuple('Container', ['name'])
        dockerutil_mock.containers.list.return_value = [Container(name='cookie')]
        result = dockerutil_mock.is_running().return_value = [False, False]
        assert result == [False, False]

    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.utils.dockerutil.check_output')
    @patch('platform.processor')
    def test_pull_x86(self, platform_mock, check_output_mock, check_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        platform_mock.return_value = 'x86_64'

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

    @patch('jbcli.utils.dockerutil.check_call')
    @patch('jbcli.utils.dockerutil.check_output')
    @patch('platform.processor')
    def test_pull_arm(self, platform_mock, check_output_mock, check_mock, monkeypatch):
        monkeypatch.chdir(DEVLANDIA_DIR)
        platform_mock.return_value = 'arm'

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
                  '423681189101.dkr.ecr.us-east-1.amazonaws.com/juicebox-devlandia-arm:latest'])
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
