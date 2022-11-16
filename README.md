# devlandia
It's Juicebox development and implementations environments... it's DEVLANDIA!

# Getting Started
First, if you don't already have it, you'll need to download and install Docker.  Follow [this link](https://docs.docker.com/docker-for-mac/install/) and follow the instructions appropriate to your machine (Intel vs Apple Silicon).  Windows users on anything
other than Windows 10 Pro, Enterprise, or Education with a minimum build number of 10586 will need to install
[Docker Toolbox](https://download.docker.com/win/stable/DockerToolbox.exe).  Run the full installation.

# Setting up your SSH key with Github
First, follow the Github guide on checking any existing keys you might have, and generating one if necessary.  After a
key is setup you'll also want to setup an SSH config entry to use this key.

In your ~/.ssh/config file, add a block like the one below:

    Host github.com
        Hostname ssh.github.com
        Port 443
        user <githubusername>
        IdentityFile ~/.ssh/<ssh_key>

The 443 port is needed because of an issue we discovered where users were unable to interact with Github while on
the Juice VPN.

# Installing Python
Almost all the work on developing data services is done via Python. While
Macs ship with Python installed, it's easier to manage Python versions from pyenv or homebrew to
avoid many pitfalls.  Below are the instructions for setting up with pyenv (installed via homebrew)  The default Python 
version that homebrew installs at the time of writing is 3.10 which may be incompatible with Devlandia:

First, install homebrew if you don't already have it installed:

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    brew install pyenv
    
    pyenv install --list

Choose your desired version and install it.  We don't currently have an exhaustive list of compatible versions, but 3.7.8 and 3.8.6 
are confirmed to work as of 11/22:

    pyenv install 3.8.6

Create a new virtual environment for devlandia by changing to the desired directory and running ``virtualenv devlandia``.
This can be done in a central place such as ``~/.virtualenvs`` or in your project directory.  Devlandia should 
be using at least Python 3.7.8.  If you have multiple versions of Python installed and want to specify the version for 
your virtual environment, run ``virtualenv -p /path/to/python/install devlandia``.  If you installed your virtual 
environment to ``~/.virtualenvs/`` you'll need to run ``source ~/.virtualenvs/devlandia/bin/activate`` to activate it.
Once your environment is set up and activated run ``pip install -r requirements.txt`` from the root directory of devlandia.

Finally, you'll need to run ``jb start`` from the devlandia directory. You will see a menu that will give you options
as to what environment you would like to run. You can instead specify an image name or other options and bypass the menu
selection like so ``jb start master-py3``
Docker will pull down 4 images: Postgres, Redis, the pre-built Juicebox image, and the snapshot image.  After the images are downloaded it 
will go through its initialization and will come up at ``http://localhost:8000/``.  If you're starting in a HSTM specific
environment, go to ``http://localhost:8000/admin`` to bypass the single signon.  To add new apps, go to the root of
Devlandia and run ``jb add <app_name>``.

An important note, the default behavior of running ``jb start`` now is to look for changes with
the local image you're working on compared to the server version and to pull these updates, so you'll always be up to 
date.  If for whatever reason you don't want to update the Juicebox image immediately, you can call the command 
as follows: ``jb start --noupdate``.  This has to be done every time you start if you don't want the image to update.

We also now prompt you to set up a username (Format should be "FirstName LastName") and email address.  Once set we 
automatically create users for you in each Devlandia client as a ClientRole.owner.

# Authentication

We need to make sure your AWS credential and config files are set up correctly.

You will need to have your credentials in the ~/.aws/credentials file.  It is in the following format:
 
    [default]
    aws_access_key_id = AWS_ACCESS_KEY
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY
    
If you have multiple users (not roles) your credential file may look like this:
    
    [default]
    aws_access_key_id = AWS_ACCESS_KEY
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY

    [sec]
    aws_access_key_id = AWS_ACCESS_KEY
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY

For the ~/.aws/config file it should be in the following format:
 
    [default]
    region = us-east-1
    output = json
    mfa_serial = arn:aws:iam::423681189101:mfa/<username>

If you have multiple profiles the ~/.aws/config file might look like this:

    [default]
    region = us-east-1
    output =  json
    mfa_serial = arn:aws:iam::423681189101:mfa/<username>

    [profile profilename]
    role_arn = arn:aws:iam::423681189101:role/RoleName
    source_profile = default

Once this is set up, you can run ``jb start <optional_env>``.  If you only have one MFA device it will automatically detect
that and use that one.  If you have multiple MFA devices you'll be prompted to select the MFA device's index in the list (0 based).

You will then be prompted for your MFA token, as well as the profile name and Juicebox should start.

# Debugging
The juicebox image is built with SSH enabled so that we can set up a remote interpreter through the connection.  For 
local development purposes, a default insecure_key is installed to make it easier to set up and distribute.  The private
key is located in the root of this repository.  To avoid getting an error about your key permissions being too 
permissive, in the devlandia root run ``chmod 400 insecure_key``.  Move this file to your SSH directory at ``~/.ssh/``.
You will need to have Juicebox running initially to set up the remote interpreter.

Once Juicebox is running, go to the PyCharm menu and click preferences.  Select ``Project: devlandia`` and 
``Project interpreter``.  Click the gear icon and ``Add Remote``.  Set your settings as listed in the image below.

![SSH Options](https://github.com/juiceinc/devlandia/blob/master/readme/sshoptions.png)

PyCharm will complain if we don't enable ``Django Support``.  To do this go to ``PyCharm -> Preferences -> Languages & Frameworks -> Django``
Click ``Enable Django Support``.  For ``Django Project root`` just add the root of the Devlandia project, and you're done. 

If you work only in one environment in Devlandia, you should be good to go.  Devlandia includes a `Juicebox` 
run configuration that should work with the settings we've set up to this point.  You should be able to set break points
in your app.  Click ``Run -> Debug - 'Juicebox'``.  It will create a new debug server running on port 8888.  Go to
``http://localhost:8888`` to interact with this debugging instance.  It should now break on your break points.

HealthStream environments have a separate Run configuration ``HSTM-Juicebox``.  To debug, click 
``Run -> Debug - 'HSTM-Juicebox'``.

# Troubleshooting

## Port Already Allocated
In some cases you may encounter some variation of the following error: ``Error starting userland proxy: Bind for 
0.0.0.0:8000 failed: port is already allocated``.  This is most likely due to a program running on the port we need 
(Juicebox in Vagrant for example).  Be sure to kill the task that's using the port, and try again.  If you still 
encounter this issue, and you're sure you've killed the necessary task, try restarting Docker.  On Mac there will be a Whale 
icon in your top task bar, click that, and restart should be the first option.  If all else fails try a full restart of 
your computer.

## Signature Expired
The following error seems to come up if you've started Juicebox and left it running for quite a while.  The credential 
session expires after 12 hours in most cases.  Normally a restart of Docker fixes this issue, but if not try a full reboot.
We have seen a couple of variations of the message, listed below, but the fix is the same.

``botocore.exceptions.ClientError: An error occurred (InvalidSignatureException) when calling the Query operation: Signature expired: 20170519T122830Z is now earlier than 20170519T124310Z (20170519T125810Z - 15 min.)``

``credstash.KmsError: KMS ERROR: Decryption error An error occurred (InvalidSignatureException) when calling the Decrypt operation: Signature expired: 20171010T195804Z is now earlier than 20171010T200613Z (20171010T201113Z - 5 min.)``

## Debugging Not Working
There could be a couple issues at play here.  In the PyCharm menu -> Project: devlandia -> Project Interpreter, check to be sure you have a path mapping set.  It should be <Project root>/apps -> /code/apps.  If it's already set, but you can't hit any breakpoints, try removing and readding this path mapping.  Map the root of your devlandia direoctory/apps -> /code/apps.  The project root is a virtual mapping that gets expanded, but due to quirks in PyCharm it doesn't always get translated correctly, and you're left with an invalid path that doesn't map to anything.

# Core Development
If you'll be working on the core and wanted to test things in Devlandia, you'll use a bit of a different workflow.  Clone
the develop branch of fruition into the root devlandia directory with `git clone --recursive git@github.com:juiceinc/fruition.git`.
The core docker-compose file is currently based on the image from the current develop branch.  The docker-compose file selectively mounts your local Juicebox 
code subdirectories into corresponding directories inside the container at `/code/`. Edits to local core code should be 
reflected inside the running container. After cloning the repo, run `npm install` in the `fruition` folder, to install requirements. You will be responsible for keeping this branch up to date.  It's not something Devlandia will handle itself. 
