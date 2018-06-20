#!/usr/bin/env bash

pip install virtualenv virtualenvwrapper
echo "WORKON_HOME="~/.virtualenvs"" >> ~/.bash_profile
echo "source /usr/local/bin/setup.sh" >> ~/.bash_profile
source $HOME/.bash_profile
chmod 400 insecure_key && cp insecure_key ~/.ssh/
mkvirtualenv devlandia -p /usr/local/Cellar/python/2.7.14/bin/python
echo "cd $PWD" >> ~/.virtualenvs/devlandia/bin/postactivate
source $HOME/.virtualenvs/devlandia/bin/activate
pip install -r requirements.txt
sudo mkdir /code
sudo touch /code/manage.py
