#!/usr/bin/env bash

pip install virtualenvwrapper
echo "WORKON_HOME="~/.virtualenvs"" >> ~/.bash_profile
echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bash_profile
source $HOME/.bash_profile
mkvirtualenv devlandia -p /usr/bin/python