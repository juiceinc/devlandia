from setuptools import setup, find_packages

requirements = [
    'click==6.2',
    'cookiecutter==1.3.0',
    'gabbi==1.24.0',
    'docker==2.2.1',
    'docker-compose==1.12.0',
    'requests==2.20.1',
    'docker==2.2.1',
    'docker-compose==1.12.0',
    'botocore==1.5.76',
    'watchdog==0.8.3',
    'tabulate==0.8.3'
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
    version='0.10.0',
    description='Juicebox command line',
    author="Casey Wireman",
    author_email='casey.wireman@juiceanalytics.com',
    packages=find_packages(),
    install_requires=requirements,
    entry_points=entry_points,
)
