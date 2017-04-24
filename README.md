# devlandia
It's Juicebox development and implementations environments... it's DEVLANDIA!

# Getting Started
First, if you don't already, you'll need to
[download and install Docker](https://download.docker.com/mac/stable/Docker.dmg) on your machine.
Documentation can be found [here](https://docs.docker.com/docker-for-mac/install/).

Create a new virtualenv for devlandia and run
``pip install -r requirements.txt``.  This will install the updated copy
of jbcli in your environment.

Next, make sure you're in the devlandia directory and run ``npm install``.  This is necessary
for the watcher to work.  Next run ``make ecr-login``, then ``jb start`` as normal.  

Docker will pull down 3 images: Postgres, Redis, and the pre-built Juicebox image.  After the
images are downloaded it will go through its initialization and will
come up at ``http://localhost:8000/``.

Docker will be expecting to find your AWS credentials at ~/.boto.  If you
have your credentials in another location please at least copy them here.