import os
import time

import click
from requests import get


def create_browser_instance():
    # Create proxy browser instance for hot reloading
    cmd = 'npx browser-sync start --proxy="localhost:8000"'
    os.system(cmd)


def refresh_browser(timeout=None):
    click.echo('Checking server status...')

    if timeout:
        time.sleep(timeout)

    def attempt_refresh():
        try:
            response = get('http://localhost:8000')
            if response and response.status_code == 200:
                click.echo('Refreshing browser...')
                cmd = "npx browser-sync reload"
                os.system(cmd)
        except:
            click.echo('Almost done...')
            if timeout:
                time.sleep(timeout)
            attempt_refresh()
    attempt_refresh()
