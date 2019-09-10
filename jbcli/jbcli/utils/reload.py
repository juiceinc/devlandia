"""Handles watcher-related tasks for app reloading
"""
import time
import click

from .format import echo_warning, echo_highlight
from requests import get, ConnectionError
from subprocess import check_output


def create_browser_instance():
    """Create proxy browser instance for hot reloading
    """
    cmd = ['browser-sync', 'start', '--proxy=localhost:8000']
    check_output(cmd)


def refresh_browser(timeout=None):
    """Refreshes browser-sync browser instance if
    Django server is ready

    :param timeout: Optional timeout duration before checking
    server status
    """
    echo_highlight('Checking server status...')
    for i in range(5):
        if timeout:
            time.sleep(timeout)
        try:
            response = get('http://localhost:8000/health_check')
        except ConnectionError:
            echo_highlight('Still working...')
        else:
            if response and response.status_code == 200:
                click.echo('Refreshing browser...')
                cmd = ['browser-sync', 'reload']
                check_output(cmd)
                return
    echo_warning('Maximum attempts reached! Something might be wrong.')
