from requests import post, ConnectionError, ConnectTimeout
import os
from .storageutil import stash
from .format import *

SERVER = "http://localhost:8000"
JB_ADMIN_USER = os.environ.get("JB_ADMIN_USER", "chris@juice.com")
JB_ADMIN_PASSWORD = os.environ.get("JB_ADMIN_PASSWORD", "cremacuban0!")


def get_admin_token(refresh_token=False):
    """Get an admin user token. """
    if not refresh_token:
        token = stash.get('token')
        if token:
            echo_success('Got admin token from storage')
            return token

    url = "{SERVER}/api/v1/jb/api-token-auth/".format(SERVER=SERVER)
    payload = {"email": JB_ADMIN_USER, "password": JB_ADMIN_PASSWORD}
    response = post(url, data=payload)
    if response.status_code == 200:
        token = response.json()["token"]
        echo_success("New admin token acquired.")
        stash.put('token', token)
        return token

    else:
        echo_warning(
            "Could not fetch admin token, status {}".format(response.status_code)
        )
        return None


def echo_result(result):
    """Format results like

    DEBUG     Slice was unchanged

            instance=free-form for Basketball (Slice)


    DEBUG     Found existing Theme

            instance=Theme for jbodemo_birdo (Theme)
            lookup_params={'id': 'de726b3b'}

    """
    logs = result.get('details', {}).get('logs', [])
    for log in logs:
        level = log.pop('level', 'unknown')
        event = log.pop('event', 'unknown')
        content = '{:10s}{}\n\n'.format('[' + level + ']', event)
        for k in sorted(log.keys()):
            content += '{:>20}: {}\n'.format(k, log[k])
        if level in ('error', 'warning'):
            echo_warning(content)
        else:
            echo_success(content)


def load_app(app, refresh_token=False):
    """Attempt to load an app using jb API. If successful return True. """
    admin_token = get_admin_token(refresh_token)
    if admin_token:
        url = "{SERVER}/api/v1/app/load/{APP}/".format(SERVER=SERVER, APP=app)
        headers = {
            "Authorization": "JWT {}".format(admin_token),
            "Content-Type": "application-json",
        }
        retry_cnt = 0
        while retry_cnt < 4
            try:
                response = post(url, headers=headers)
            except ConnectionError:
                retry_cnt += 1
                echo_warning('Can not connect, retrying')
                time.sleep(2**retry_cnt)
                continue
            break
        if response.status_code == 200:
            result = response.json()
            echo_success("{} was added successfully via API.".format(app))
            echo_result(result)
            return True
        elif response.status_code == 401:
            echo_warning('Token is expired')
            return load_app(app, refresh_token=True)
        else:
            result = response.json()
            echo_warning("Loading app status code was {}".format(response.status_code))
            echo_result(result)
            return False
    else:
        echo_warning("Could not get admin token.")
        return False
