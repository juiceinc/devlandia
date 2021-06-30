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
                for line in config:
                    if "mfa_serial" in line:
                        mfa_serial = line.split("=")[1].rstrip()
                        break
        except FileNotFoundError:
            echo_warning('~/.aws/config file not found.')
        if mfa_serial is not None:
            token = input("Please enter MFA Code: ")
            output = json.loads(
                subprocess.check_output(['aws', 'sts', 'get-session-token', '--serial-number', f'{mfa_serial}',
                                         '--token-code', f'{token}']))
            os.environ['AWS_ACCESS_KEY_ID'] = output['Credentials']['AccessKeyId']
            os.environ['AWS_SECRET_ACCESS_KEY'] = output['Credentials']['SecretAccessKey']
            os.environ['AWS_SESSION_TOKEN'] = output['Credentials']['SessionToken']