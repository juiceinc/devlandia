from requests import post
import os
from .format import *
from pprint import pformat

SERVER = "http://localhost:8000"
JB_ADMIN_USER = os.environ.get("JB_ADMIN_USER", "chris@juice.com")
JB_ADMIN_PASSWORD = os.environ.get("JB_ADMIN_PASSWORD", "cremacuban0!")


def get_admin_token():
    """Get an admin user token. """
    url = "{SERVER}/api/v1/jb/api-token-auth/".format(SERVER=SERVER)
    payload = {"email": JB_ADMIN_USER, "password": JB_ADMIN_PASSWORD}
    response = post(url, data=payload)
    if response.status_code == 200:
        echo_success("Admin token acquired")
        return response.json()["token"]
    else:
        echo_warning(
            "Could not fetch admin token, status {}".format(response.status_code)
        )
        return None


def load_app(app):
    """Attempt to load an app using jb API. If successful return True. """
    admin_token = get_admin_token()
    if admin_token:
        url = "{SERVER}/api/v1/app/load/{APP}/".format(SERVER=SERVER, APP=app)
        headers = {
            "Authorization": "JWT {}".format(admin_token),
            "Content-Type": "application-json",
        }
        response = post(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            echo_success("{} was added successfully via API.".format(app))
            # TODO: We could format the logs nicely
            echo_success(pformat(result))
            return True
        else:
            result = response.json()
            echo_warning("Loading app status code was {}".format(response.status_code))
            # TODO: We could format the logs nicely
            echo_warning(pformat(result))
            return False
    else:
        echo_warning("Could not get admin token.")
        return False
