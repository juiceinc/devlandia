import os
from .subprocess import check_call, check_output
from .format import echo_warning, echo_success
import json
import configparser


def set_creds():
    if "AWS_ACCESS_KEY_ID" not in os.environ:
        mfa_serial = None
        mfas = []
        profiles = []
        mfa_map = {}
        choice = 0
        try:
            echo_success("Found ~/.aws/config file.")
            config = configparser.ConfigParser()
            config.read(f"{os.path.expanduser('~')}/.aws/config")
            for section in config.sections():
                try:
                    mfa = config.get(section, 'mfa_serial')
                    continue
                except configparser.NoOptionError:
                    echo_warning(f"No MFA Detected in section {section}, skipping.")
                if 'profile ' in section:
                    profiles.append(section.replace('profile ', ''))
                else:
                    profiles.append(section)
                if mfa not in mfas:
                    mfas.append(mfa)
            echo_success(f'Profiles: {profiles}')
            echo_success(f"MFAs: {mfas}")
            if len(mfas) < 1:
                echo_warning("Error: No MFA Devices Found in Config")
                exit(1)
            elif len(mfas) == 1:
                choice = 0
            elif len(mfas) > 1:
                choice = int(input(f"Select index of MFA Serial to use (0-{len(mfas) - 1}): "))

        except FileNotFoundError:
            echo_warning('~/.aws/config file not found.')
        if mfas[choice] is not None:
            token = input("Please enter MFA Code: ")
            profile_name = input("Please enter profile name: ")
            output = json.loads(
                check_output(['aws', 'sts', 'get-session-token', '--profile', f'{profile_name}', '--serial-number', f'{mfas[choice]}',
                              '--token-code', f'{token}', '--duration-seconds', '86400']))
            os.environ['AWS_ACCESS_KEY_ID'] = output['Credentials']['AccessKeyId']
            os.environ['AWS_SECRET_ACCESS_KEY'] = output['Credentials']['SecretAccessKey']
            os.environ['AWS_SESSION_TOKEN'] = output['Credentials']['SessionToken']
            print(os.getcwd())