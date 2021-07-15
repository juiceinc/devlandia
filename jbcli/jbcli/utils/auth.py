import os
from .subprocess import check_call, check_output
from .format import echo_warning, echo_success
import json


def set_creds():
    if "AWS_ACCESS_KEY_ID" not in os.environ:
        mfa_serial = None
        mfas = []
        profiles = []
        choice = 0
        try:
            with open(f"{os.path.expanduser('~')}/.aws/config") as config:
                echo_success("Found ~/.aws/config file.")
                for line in config:
                    if '[' in line and 'profile' not in line:
                        profiles.append(line.replace('[', '').replace(']', '').rstrip())
                    elif '[' in line and 'profile' in line:
                        profiles.append(line.replace('[', '').replace(']', '').replace('profile ', '').rstrip())
                    elif 'mfa_serial' in line:
                        mfas.append(line.split('=')[1].rstrip())
                echo_success(f'Profiles: {profiles}')
                deduped_mfas = list(dict.fromkeys(mfas))
                echo_success(f"MFAs: {deduped_mfas}")
                if len(deduped_mfas) < 1:
                    echo_warning("Error: No MFA Devices Found in Config")
                    exit(1)
                if len(deduped_mfas) == 1:
                    choice = 0
                elif len(deduped_mfas) > 1:
                    choice = int(input(f"Select index of MFA Serial to use (0-{len(deduped_mfas) - 1}): "))

        except FileNotFoundError:
            echo_warning('~/.aws/config file not found.')
        if deduped_mfas[choice] is not None:
            token = input("Please enter MFA Code: ")
            profile_name = input("Please enter profile name: ")
            output = json.loads(
                check_output(['aws', 'sts', 'get-session-token', '--profile', f'{profile_name}', '--serial-number', f'{deduped_mfas[choice]}',
                              '--token-code', f'{token}', '--duration-seconds', '86400']))
            os.environ['AWS_ACCESS_KEY_ID'] = output['Credentials']['AccessKeyId']
            os.environ['AWS_SECRET_ACCESS_KEY'] = output['Credentials']['SecretAccessKey']
            os.environ['AWS_SESSION_TOKEN'] = output['Credentials']['SessionToken']
            print(os.getcwd())