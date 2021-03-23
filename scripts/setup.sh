#!/usr/bin/env bash

if [ ! -e insecure_key ]; then
    echo "Could not find ./insecure_key."
    echo "Please run this script from the base of devlandia."
    exit 1
fi

echo "installing virtualenv and virtualenvwrapper..."
pip install virtualenv virtualenvwrapper

echo "modifying ~/.bash_profile if needed..."
grep "WORKON_HOME" ~/.bash_profile || echo "WORKON_HOME="~/.virtualenvs"" >> ~/.bash_profile
grep "/usr/local/bin/virtualenvwrapper.sh" ~/.bash_profile || echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bash_profile

echo "sourcing ~/.bash_profile..."
source $HOME/.bash_profile

echo "copying insecure ssh key into place if needed..."
if [ ! -e ~/.ssh/insecure_key ]; then
    chmod 400 insecure_key
    cp insecure_key ~/.ssh/
fi

echo "creating virtualenv \"devlandia\"..."
mkvirtualenv devlandia -p python3.7
echo "cd $PWD" >> ~/.virtualenvs/devlandia/bin/postactivate

echo "activating virtualenv \"devlandia\""
source $HOME/.virtualenvs/devlandia/bin/activate

echo "installing requirements into \"devlandia\"..."
pip install -r requirements.txt

echo "creating /code/manage.py if needed..."
if [ ! -e /code/manage.py ]; then
   sudo mkdir /code
   sudo touch /code/manage.py
fi

echo "Setup complete. If you saw no catastrophic errors above,"
echo "then you should be able to **open a new terminal** and run"
echo
echo "    workon devlandia"
echo
