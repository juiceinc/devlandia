import configparser
import json
import os

import boto3
from PyInquirer import prompt

from .subprocess import check_output
from ..utils.format import echo_warning, echo_success
from ..utils.storageutil import Stash


def has_valid_session() -> bool:
    return True


def has_current_session():
    stash = Stash("~/.config/juicebox/creds.toml")
    try:
        test = stash.get('AWS_ACCESS_KEY_ID')
        if test is None:
            set_creds()
        else:
            load_creds()
    except Exception as e:
        print(f'Error: {e}')


def set_creds():
    if "AWS_ACCESS_KEY_ID" in os.environ:
        return
    profile_details = []
    try:
        echo_success("Found ~/.aws/config file.")
        config = configparser.ConfigParser()
        config.read(f"{os.path.expanduser('~')}/.aws/config")
        for section in config.sections():
            try:
                parsed = section.replace('profile ', '') if 'profile' in section else section
                if config.get(section, 'mfa_serial'):
                    details = (parsed, config.get(section, 'mfa_serial'))
                    profile_details.append(details)
            except Exception as e:
                profile_details.append((parsed, 'No MFA device'))
    except Exception as e:
        print(e)
    if len(profile_details) > 1:
        choices = [
            {'name': k[0] + ' - ' + k[1], 'value': (k[0], k[1])}
            for k in profile_details
        ]

        questions = [
            {
                'type': 'list',
                'name': 'profile',
                'message': 'What profile and MFA device would you like to use?',
                'choices': choices
            }
        ]

        profile = prompt(questions).get('profile')
        if profile and profile[1] != 'No MFA device':
            token = input("Please enter MFA Code: ")
            output = json.loads(
                check_output(['aws', 'sts', 'get-session-token', '--profile', f'{profile[0]}', '--serial-number',
                              f'{profile[1]}', '--token-code', f'{token}', '--duration-seconds', '86400']))
            _extracted_from_set_creds(output)
        elif profile:
            output = json.loads(
                check_output(['aws', 'sts', 'get-session-token', '--profile', f'{profile[0]}', '--duration-seconds',
                              '86400']))
            _extracted_from_set_creds(output)
        else:
            echo_warning('Profile not selected, exiting.')
            exit(1)


def load_creds():
    print("Loading cached credentials")
    stash = Stash("~/.config/juicebox/creds.toml")
    os.environ['AWS_ACCESS_KEY_ID'] = stash.get('AWS_ACCESS_KEY_ID')
    os.environ['AWS_SECRET_ACCESS_KEY'] = stash.get('AWS_SECRET_ACCESS_KEY')
    os.environ['AWS_SESSION_TOKEN'] = stash.get('AWS_SESSION_TOKEN')

def test_creds():


def _extracted_from_set_creds(output):
    stash = Stash("~/.config/juicebox/creds.toml")
    os.environ['AWS_ACCESS_KEY_ID'] = output['Credentials']['AccessKeyId']
    os.environ['AWS_SECRET_ACCESS_KEY'] = output['Credentials']['SecretAccessKey']
    os.environ['AWS_SESSION_TOKEN'] = output['Credentials']['SessionToken']
    stash.put("AWS_ACCESS_KEY_ID", output['Credentials']['AccessKeyId'])
    stash.put("AWS_SECRET_ACCESS_KEY", output['Credentials']['SecretAccessKey'])
    stash.put("AWS_SESSION_TOKEN", output['Credentials']['SessionToken'])
