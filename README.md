# devlandia
It's Juicebox development and implementations environments... it's DEVLANDIA!

# Getting Started
First, if you don't already have it, you'll need to
[download and install Docker](https://download.docker.com/mac/stable/Docker.dmg) on your machine.
Documentation can be found [here](https://docs.docker.com/docker-for-mac/install/).

Create a new virtualenv for devlandia by changing to the desired directory and running ``virtualenv devlandia``.
This can be done in a central place such as ``~/.virtualenvs`` or in your project directory.  Devlandia should 
be using Python 2.7.12.  If you have multiple versions of Python installed and want to specify the version for 
your virtual environment, run ``virtualenv -p /path/to/python/install devlandia``.  If you installed your virtual 
environment to ``~/.virtualenvs/`` you'll need to run ``source ~/.virtualenvs/devlandia/bin/activate`` to activate it.
Once your environment is setup and activated run ``pip install -r requirements.txt`` from the root directory of devlandia.

Next, still in the devlandia root directory, run ``npm install``.  This is necessary for the watcher to work. 
Run ``make ecr_login``.  To automate this login step, copy the ``postactivate`` file in the scripts folder to the bin 
directory for your devlandia virtual environment.  Be sure to edit the file to point to the root of your devlandia 
directory.  This will automatically log you in every time you activate the virtual environment.

Finally you'll need to cd into the desired environment at 
``environment/<env>`` and run ``jb start`` as normal.  Currently the only image that is available is in the 
`environments/test` directory.  Docker will pull down 3 images: Postgres, Redis, and the pre-built Juicebox image.  
After the images are downloaded it will go through its initialization and will
come up at ``http://localhost:8000/``.

Docker will be expecting to find your AWS credentials at ~/.boto.  If you
have your credentials in another location please at least copy them here.