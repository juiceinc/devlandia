import os
from .subprocess import check_call, check_output
from .format import echo_warning, echo_success
import json

def set_creds():
    if "AWS_ACCESS_KEY_ID" not in os.environ:
        mfa_serial = None
        try:
            with open(f"{os.path.expanduser('~')}/.aws/config") as config:
                echo_success("Found ~/.aws/config file.")
                mfas = [line.split("=")[1].rstrip() for line in config if "mfa_serial" in line]
                deduped_mfas = list(dict.fromkeys(mfas))
                echo_success(f"{deduped_mfas}")
                if len(deduped_mfas) < 1:
                    echo_warning("Error: No MFA Devices Found in Config")
                    exit(1)
                if len(deduped_mfas) == 1:
                    choice = 0
                elif len(deduped_mfas) > 1:
                    choice = int(input(f"Select index of MFA Serial to use (0-{len(deduped_mfas)-1}): "))

        except FileNotFoundError:
            echo_warning('~/.aws/config file not found.')
        if deduped_mfas[choice] is not None:
            token = input("Please enter MFA Code: ")
            output = json.loads(
                check_output(['aws', 'sts', 'get-session-token', '--serial-number', f'{deduped_mfas[choice]}',
                                         '--token-code', f'{token}']))
            os.environ['AWS_ACCESS_KEY_ID'] = output['Credentials']['AccessKeyId']
            os.environ['AWS_SECRET_ACCESS_KEY'] = output['Credentials']['SecretAccessKey']
            os.environ['AWS_SESSION_TOKEN'] = output['Credentials']['SessionToken']