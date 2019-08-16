import requests
import os
from .format import *

SERVER = 'http://localhost:8000'
JB_ADMIN_USER = os.environ.get('JB_ADMIN_USER', 'chris@juice.com')
JB_ADMIN_PASSWORD = os.environ.get('JB_ADMIN_PASSWORD', 'cremacuban0!')


def get_admin_token():
    """Get an admin user token. """
    url = '{SERVER}/api/v1/jb/api-token-auth/'.format(SERVER=SERVER)
    payload = {
        'email': JB_ADMIN_USER,
        'password': JB_ADMIN_PASSWORD,
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        echo_success('Admin token acquired')
        return response.json()['token']
    else:
        echo_warning('Could not fetch admin token, status {}'.format(response.status_code))
        return None


def load_app(app):
    """Attempt to load an app using jb API. If successful return True. """
    admin_token = get_admin_token()
    if admin_token:
        url = '{SERVER}/api/v1/app/load/{APP}/'.format(SERVER=SERVER, APP=app)
        headers = {
            'Authorization': 'JWT {}'.format(admin_token),
            'Content-Type': 'application-json'
        }
        response = requests.post(url, headers=headers)
        if response.status_code == 204:
            echo_success('{} was added successfully via API.'.format(app))
            return True
        else:
            echo_warning('Loading app status code was {}'.format(response.status_code))
            return False
    else:
        return False
