# devlandia
It's Juicebox development and implementations environments... it's DEVLANDIA!

# Getting Started
First, if you don't already have it, you'll need to
[download and install Docker (this link is for Mac users)](https://download.docker.com/mac/stable/Docker.dmg) on your 
machine.  Documentation can be found [here](https://docs.docker.com/docker-for-mac/install/).  Windows users on anything
other than Windows 10 Pro, Enterprise, or Education with a minimum build number of 10586 will need to install
[Docker Toolbox](https://download.docker.com/win/stable/DockerToolbox.exe).  Run the full installation.

Create a new virtual environment for devlandia by changing to the desired directory and running ``virtualenv devlandia``.
This can be done in a central place such as ``~/.virtualenvs`` or in your project directory.  Devlandia should 
be using Python 2.7.12.  If you have multiple versions of Python installed and want to specify the version for 
your virtual environment, run ``virtualenv -p /path/to/python/install devlandia``.  If you installed your virtual 
environment to ``~/.virtualenvs/`` you'll need to run ``source ~/.virtualenvs/devlandia/bin/activate`` to activate it.
Once your environment is setup and activated run ``pip install -r requirements.txt`` from the root directory of devlandia.

Next, still in the devlandia root directory, run ``npm install --only=dev``.  This is necessary for the watcher to work. 
Run ``make ecr_login``.  To automate this login step, copy the ``postactivate`` file in the scripts folder to the bin 
directory for your devlandia virtual environment.  Be sure to edit the file to point to the root of your devlandia 
directory.  This will automatically log you in to our private Docker registry every time you activate the virtual
environment.

Finally you'll need to cd into the desired environment at 
``environments/<env>`` and run ``jb start`` as normal.  Currently the only images available are `environments/test`, 
and ``environments/hstm-test``.  Docker will pull down 3 images: Postgres, Redis, and the pre-built Juicebox image.  
After the images are downloaded it will go through its initialization and will come up at ``http://localhost:8000/``.

Docker will be expecting to find your AWS credentials at ~/.boto.  If you have your credentials in another location 
please at least copy them here with the form:
 
    [Credentials]
    aws_access_key_id = NEW_ACCESS_KEY
    aws_secret_access_key = NEW_SECRET_KEY

# Debugging
The juicebox image is built with SSH enabled so that we can setup a remote interpreter through the connection.  For 
local development purposes, a default insecure_key is installed to make it easier to setup and distribute.  The private
key is located in the root of this repository.  To avoid getting an error about your key permissions being too 
permissive, in the devlandia root run ``chmod 400 insecure_key``.  Move this file to your SSH directory at ``~/.ssh/``.
You will need to have Juicebox running initially to setup the remote interpreter.

Once Juicebox is running, go to the PyCharm menu and click preferences.  Select ``Project: devlandia`` and 
``Project interpreter``.  Click the gear icon and ``Add Remote``.  Set your settings as listed in the image below.

![SSH Options](https://github.com/juiceinc/devlandia/blob/master/readme/sshoptions.png)

PyCharm will complain if we don't enable ``Django Support``.  To do this go to ``PyCharm -> Preferences -> Languages & Frameworks -> Django``
Click ``Enable Django Support``.  For ``Django Project root`` just add the root of the Devlandia project and you're done. 

If you work only in one environment in Devlandia, you should be good to go.  Devlandia includes a `Juicebox` 
run configuration that should work with the settings we've setup to this point.  You should be able to set break points
in your app.  Click ``Run -> Debug - 'Juicebox'``.  It will create a new debug server running on port 8888.  Go to
``http://localhost:8888`` to interact with this debugging instance.  It should now break on your break points.

HealthStream environments have a separate Run configuration ``HSTM-Juicebox``.  To debug, click 
``Run -> Debug - 'HSTM-Juicebox'``.

# Troubleshooting
In some cases you may encounter some variation of the following error: ``Error starting userland proxy: Bind for 
0.0.0.0:8000 failed: port is already allocated``.  This is most likely due to a program running on the port we need 
(Juicebox in Vagrant for example).  Be sure to kill the task that's using the port, and try again.  If you still 
encounter this issue and you're sure you've killed the necessary, try restarting Docker.  On Mac there will be a Whale 
icon in your top task bar, click that, and restart should be the first option.  If all else fails try a full restart of 
your computer.
