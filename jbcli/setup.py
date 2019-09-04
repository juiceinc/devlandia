from setuptools import setup, find_packages

requirements = [
    'boto3~=1.9.210',
    'botocore~=1.12.212',
    'docker',
    'docker-compose',
    'click~=6.2',
    'watchdog~=0.8.3',
    'tabulate~=0.8.2',
    'certifi~=2019.3.9',
    'elasticsearch~=6.3.1',
    'elasticsearch-dsl~=6.3.1',
    'tablib~=0.13.0',
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
    version='0.11.2',
    description='Juicebox command line',
    author="Casey Wireman",
    author_email='casey.wireman@juiceanalytics.com',
    packages=find_packages(),
    install_requires=requirements,
    entry_points=entry_points,
)
