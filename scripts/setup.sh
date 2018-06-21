#!/usr/bin/env bash

if [ ! -e insecure_key ]; then
    echo "Could not find ./insecure_key."
    echo "Please run this script from the base of devlandia."
    exit 1
fi

set -x

pip install virtualenv virtualenvwrapper

grep "WORKON_HOME" ~/.bash_profile || echo "WORKON_HOME="~/.virtualenvs"" >> ~/.bash_profile
grep "/usr/local/bin/virtualenvwrapper.sh" ~/.bash_profile || echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bash_profile
source $HOME/.bash_profile
chmod 400 insecure_key && cp insecure_key ~/.ssh/
mkvirtualenv devlandia -p python2.7
echo "cd $PWD" >> ~/.virtualenvs/devlandia/bin/postactivate
source $HOME/.virtualenvs/devlandia/bin/activate
pip install -r requirements.txt
sudo mkdir /code
sudo touch /code/manage.py
