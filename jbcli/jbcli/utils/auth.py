import configparser
import json
import os

import boto3
from botocore.exceptions import ClientError
from PyInquirer import prompt

from .subprocess import check_output
from ..utils.format import echo_warning, echo_success
from ..utils.storageutil import Stash


def has_current_session():
    if "AWS_ACCESS_KEY_ID" in os.environ:
        echo_success("Found existing credentials.")
        return
    stash = Stash("~/.config/juicebox/creds.toml")
    try:
        access_key = stash.get("AWS_ACCESS_KEY_ID")
        if access_key is None:
            echo_warning(
                "AWS Variables not found locally, you'll be prompted to reauthenticate."
            )
            set_creds()
        else:
            echo_success(
                "Checking existing credentials to see if the session is still valid."
            )
            load_creds()
            valid = check_cred_validity(
                aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
                aws_session_token=os.environ["AWS_SESSION_TOKEN"],
            )
            if not valid:
                set_creds()
    except ClientError as e:
        echo_warning(
            f"Client error, session doesn't appear to be valid, reauthenticating: {e}"
        )


def set_creds():
    if "AWS_ACCESS_KEY_ID" in os.environ:
        return
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
            except Exception as e:
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
            token = input("Please enter MFA Code: ")
            output = json.loads(
                check_output(
                    [
                        "aws",
                        "sts",
                        "get-session-token",
                        "--profile",
                        f"{profile[0]}",
                        "--serial-number",
                        f"{profile[1]}",
                        "--token-code",
                        f"{token}",
                        "--duration-seconds",
                        "86400",
                    ]
                )
            )
            set_and_cache_creds(output)
        elif profile:
            output = json.loads(
                check_output(
                    [
                        "aws",
                        "sts",
                        "get-session-token",
                        "--profile",
                        f"{profile[0]}",
                        "--duration-seconds",
                        "86400",
                    ]
                )
            )
            set_and_cache_creds(output)
        else:
            echo_warning("Profile not selected, exiting.")
            exit(1)
    elif len(profile_details) == 1:
        token = input("Please enter MFA Code: ")
        output = json.loads(
            check_output(
                [
                    "aws",
                    "sts",
                    "get-session-token",
                    "--profile",
                    f"{profile_details[0][0]}",
                    "--serial-number",
                    f"{profile_details[0][1]}",
                    "--token-code",
                    f"{token}",
                    "--duration-seconds",
                    "86400",
                ]
            )
        )
        set_and_cache_creds(output)


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


def load_creds():
    echo_success("Loading cached credentials")
    stash = Stash("~/.config/juicebox/creds.toml")
    os.environ["AWS_ACCESS_KEY_ID"] = stash.get("AWS_ACCESS_KEY_ID")
    os.environ["AWS_SECRET_ACCESS_KEY"] = stash.get("AWS_SECRET_ACCESS_KEY")
    os.environ["AWS_SESSION_TOKEN"] = stash.get("AWS_SESSION_TOKEN")


def set_and_cache_creds(output):
    stash = Stash("~/.config/juicebox/creds.toml")
    os.environ["AWS_ACCESS_KEY_ID"] = output["Credentials"]["AccessKeyId"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = output["Credentials"]["SecretAccessKey"]
    os.environ["AWS_SESSION_TOKEN"] = output["Credentials"]["SessionToken"]

    stash.put("AWS_ACCESS_KEY_ID", output["Credentials"]["AccessKeyId"])
    stash.put("AWS_SECRET_ACCESS_KEY", output["Credentials"]["SecretAccessKey"])
    stash.put("AWS_SESSION_TOKEN", output["Credentials"]["SessionToken"])
