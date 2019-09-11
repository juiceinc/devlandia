from setuptools import setup, find_packages

requirements = [
    'boto3',
    'botocore',
    'docker',
    'docker-compose',
    'click',
    'watchdog',
    'tabulate',
    'certifi',
    'elasticsearch',
    'elasticsearch-dsl',
    'tablib',
]

# Have setuptools generate the entry point
# wrapper scripts.
entry_points = '''[console_scripts]
jb=jbcli.cli.jb:cli
jb-admin=jbcli.cli.jb_admin:cli
jb-manage=jbcli.cli.jb_manage:cli
'''

setup(
    name='jbcli',
    version='0.13.1',
    description='Juicebox command line',
    author="Casey Wireman",
    author_email='casey.wireman@juiceanalytics.com',
    packages=find_packages(),
    install_requires=requirements,
    entry_points=entry_points,
)
