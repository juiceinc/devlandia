""" Defines common settings and variables to be shared throughout JBCLI.
"""
import os


# Prefix to use for the app template
APP_TEMPLATE_URL = os.environ.get(
    'JB_APP_TEMPLATE_URL',
    'git@github.com:juiceinc')

GITHUB_ORGANIZATION = os.environ.get('JB_GITHUB_ORGANIZATION', 'juiceinc')

# The prefix used for implementations / app repos.
# Default to how Juice namespaces these.
GITHUB_REPO_PREFIX = os.environ.get('JB_GITHUB_REPO_PREFIX', 'implementation-')

PROJECT_WATCHER = os.environ.get('JB_PROJECT_WATCHER', 'grunt watch')

DEFAULT_MODE = os.environ.get('JB_DEFAULT_MODE', 'local')

# vagrant or docker eventually
BACKEND_DRIVER = os.environ.get('JB_BACKEND_DRIVER', 'vagrant')
