import configparser
import json
import os

import boto3
from PyInquirer import prompt

from .subprocess import check_output
from ..utils.format import echo_warning, echo_success


def set_creds():
    try:
        profile_details = []
        config = configparser.ConfigParser()
        config.read(f"{os.path.expanduser('~')}/.aws/config")
        echo_success("Found ~/.aws/config file.")
        for section in config.sections():
            try:
                parsed = (
                    section.replace("profile ", "") if "profile" in section else section
                )
                if config.get(section, "mfa_serial"):
                    details = (parsed, config.get(section, "mfa_serial"))
                    profile_details.append(details)
            except Exception:
                profile_details.append((parsed, "No MFA device"))
    except Exception as e:
        print(e)
    if len(profile_details) > 1:
        choices = [
            {"name": k[0] + " - " + k[1], "value": (k[0], k[1])}
            for k in profile_details
        ]

        questions = [
            {
                "type": "list",
                "name": "profile",
                "message": "What profile and MFA device would you like to use?",
                "choices": choices,
            }
        ]

        profile = prompt(questions).get("profile")
        if profile and profile[1] != "No MFA device":
            token = query_token()
            set_and_cache_creds(profile[0], profile[1], token)
        elif profile:
            set_and_cache_creds(profile[0])
        else:
            echo_warning("Profile not selected, exiting.")
            exit(1)
    elif len(profile_details) == 1:
        token = query_token()
        set_and_cache_creds(profile_details[0][0], profile_details[0][1], token)


def query_token():
    if "JB_BW_TOTP_NAME" in os.environ:
        # Use bitwarden to get the TOTP token.
        # radix is probably the only person who uses this.
        bw_item_name = os.environ["JB_BW_TOTP_NAME"]
        token = check_output(["bw", "get", "totp", bw_item_name])
    else:
        token = input("Please enter MFA Code: ")
    return token


def check_cred_validity(aws_access_key_id, aws_secret_access_key, aws_session_token):
    ecr_test = boto3.client(
        "ecr",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
    )
    try:
        ecr_test.describe_images(
            registryId="423681189101",
            repositoryName="juicebox-devlandia",
            imageIds=[
                {"imageTag": "develop-py3"},
            ],
        )

        echo_success("Credentials are valid.")
        return True

    except Exception:
        del os.environ["AWS_ACCESS_KEY_ID"]
        del os.environ["AWS_SECRET_ACCESS_KEY"]
        del os.environ["AWS_SESSION_TOKEN"]
        echo_warning("Credentials not valid, prompting for reauthentication.")
        return False


def set_and_cache_creds(profile, serial_number=None, token=None):
    cmd = [
        "aws",
        "sts",
        "get-session-token",
        "--duration-seconds",
        "86400",
        "--profile",
        profile,
    ]
    if serial_number and token:
        cmd.extend(["--serial-number", serial_number, "--token-code", token])
    output = json.loads(check_output(cmd))

    os.environ["AWS_ACCESS_KEY_ID"] = output["Credentials"]["AccessKeyId"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = output["Credentials"]["SecretAccessKey"]
    os.environ["AWS_SESSION_TOKEN"] = output["Credentials"]["SessionToken"]
