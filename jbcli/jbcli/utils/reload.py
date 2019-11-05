"""Handles watcher-related tasks for app reloading
"""
from __future__ import absolute_import
from builtins import range
import time
import click

from .format import echo_warning, echo_highlight
from requests import get, ConnectionError
from .subprocess import check_output


browser_sync_path = '../../node_modules/.bin/browser-sync'


def create_browser_instance():
    """Create proxy browser instance for hot reloading
    """
    cmd = [browser_sync_path, 'start', '--proxy=localhost:8000']
    check_output(cmd)


def restart_browser():
    click.echo('Refreshing browser...')
    cmd = [browser_sync_path, 'reload']
    check_output(cmd)


def refresh_browser(timeout=None):
    """Refreshes browser-sync browser instance if
    Django server is ready

    :param timeout: Optional timeout duration before checking
    server status
    """    
    if timeout is None:
        restart_browser()
        return

    else:
        echo_highlight('Checking server status...')
        for i in range(5):
            time.sleep(timeout)
            try:
                response = get('http://localhost:8000/health_check')
            except ConnectionError:
                echo_highlight('Still checking...')
            else:
                if response and response.status_code == 200:
                    restart_browser()
                    return

        echo_warning('Maximum attempts reached! Something might be wrong.')
