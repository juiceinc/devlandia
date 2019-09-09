"""Handles watcher-related tasks for app reloading
"""
import os
import time

import click
from requests import get, ConnectionError


def create_browser_instance():
    """Create proxy browser instance for hot reloading
    """
    cmd = 'npx browser-sync start --proxy="localhost:8000"'
    os.system(cmd)


def refresh_browser(timeout=None):
    """Refreshes browser-sync browser instance if
    Django server is ready

    :param timeout: Optional timeout duration before checking
    server status
    """
    click.echo('Checking server status...')
    for i in range(5):
        if timeout:
            time.sleep(timeout)
        response = {'status_code': None}
        try:
            response = get('http://localhost:8000/health_check')
        except ConnectionError:
            click.echo('Still working...')
        else:
            if response and response.status_code == 200:
                click.echo('Refreshing browser...')
                cmd = "npx browser-sync reload"
                os.system(cmd)
                return
    click.echo('Maximum attempts reached! Something might be wrong.')
