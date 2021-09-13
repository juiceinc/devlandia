import configparser
import json
import os

from PyInquirer import prompt

from .subprocess import check_output
from ..utils.format import echo_warning, echo_success


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
                print(e)
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
        if profile and profile[1] is not 'No MFA device':
            token = input("Please enter MFA Code: ")
            output = json.loads(
                check_output(['aws', 'sts', 'get-session-token', '--profile', f'{profile[0]}', '--serial-number',
                              f'{profile[1]}',
                              '--token-code', f'{token}', '--duration-seconds', '86400']))
            _extracted_from_set_creds_44(output)
        elif profile:
            output = json.loads(
                check_output(['aws', 'sts', 'get-session-token', '--profile', f'{profile[0]}', '--duration-seconds',
                              '86400']))
            _extracted_from_set_creds_44(output)
        else:
            echo_warning('Profile not selected, exiting.')
            exit(1)


def _extracted_from_set_creds_44(output):
    os.environ['AWS_ACCESS_KEY_ID'] = output['Credentials']['AccessKeyId']
    os.environ['AWS_SECRET_ACCESS_KEY'] = output['Credentials']['SecretAccessKey']
    os.environ['AWS_SESSION_TOKEN'] = output['Credentials']['SessionToken']
