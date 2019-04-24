=====
Usage
=====

Juicebox CLI is used to make creating, packaging, and deploying juicebox
applications easier.

Applications Commands
=====================

These are the commands for working with your local Juicebox apps. You'll want
to get real friendly with these.

These include day-to-day actions like creating a new apps, adding existing
apps, packaging apps for deployment, and removing apps from your local
Juicebox environment.

create
------

The create command is used to create a new Juicebox application from a
template. The only required parameter is the name of the application. This
will create a repo using our default template.

This will create the initial application from our default template, initialize
it as a Git repo, connect it to a remote Github repo, and push the initial
commit.

Often you'll want to follow this command with the ``add`` command.

Options
~~~~~~~

.. csv-table::
   :header: "Option", "Description"
   :widths: 15, 30

   "--dest","The directory in which to create the application."
   "--template","The template to use. An alternative template is jbclwd."
   "--template-branch", "A specific branch to use."
   "--no-init", "Skip creating a local git repo and remote setup."
   "--no-track", "Skip pointing and pushing to a remote Github repo."
   "--no-checkrepo","Skip asking if the remote repo has already been created using oplord."


Example::

    $ jb create cookies
    Have you created the repo by running the following in Slack?

    /opslord create_imp_repo cookies

    Type Yes or No: yes
    ...
    app_id [d6e492a2]:
    app_slug [cookies]:
    juicebox [cookies]:
    project_name [cookies]:
    version [0.1.0]:

    ----------------------------------------

    Juicebox app cookies has been created at apps/cookies.

An example of creating a jbclwd app::

    $ jb create jbclwd_cookies --template=jbclwd --template-branch=cookiecutter
    Have you created the repo by running the following in Slack?

    /opslord create_imp_repo jbclwd_cookies

    Type Yes or No: yes
    Creating Juicebox app jbclwd_cookies in apps/
    You've cloned /Users/chrisgemignani/.cookiecutters/jbclwd before. Is it okay to delete and re-clone it? [yes]: yes
    ...
    Switched to a new branch 'cookiecutter'
    name [Foo]:
    description [JBCLWD starter kit]:
    app_id [ddaa891b]:
    app_slug [jbclwd_cookies]:
    stack_label [Report]:
    app_header_title [What is getting built in Nashville?]:
    app_sub_title [Approved building permits for a city can uncover many things about how and where communities are changing.]:
    primary_color [###### Hex color]: ff6600
    accent_color [###### Hex color]: 009944

    ----------------------------------------

    Juicebox app jbclwd_cookies has been created at apps/jbclwd_cookies.

add
---

The add command is used to load an existing application. It can take one or more
application names separated by spaces.

If the application is not already found in the application directory, it is
downloaded from Github. It will then load the application into the Juicebox VM,
and optionally add the repo to the Github desktop application.

Options
~~~~~~~

.. csv-table::
   :header: "Option", "Description"
   :widths: 15, 30

   "--add-desktop","Adds the application to the Github desktop app."


Example::

    $ jb add cookies


clone
-----

The clone command is used to create a new Juicebox application by copying an
existing one. It requires the name of an existing application and a name
for the new application.

The command will create an application from an existing application, create a
local git repo inside the newly created application directory, setup a pointer
to a remote Github repo, push the data to that Github repo.

Often you'll want to follow this command with the ``add`` command.

Options
~~~~~~~

.. csv-table::
   :header: "Option", "Description"
   :widths: 15, 30

   "--no-init","Skip creating a local git repo and remote setup."
   "--no-track","Skip pointing and pushing to a remote Github repo."


Example::

    $ jb clone cookies sugar_cookies


remove
------

The remove command deletes an application from the Juicebox VM and the apps
folder on your machine. The command can take one or more application names
separated by spaces. It will require you to confirm the deletion.

Options
~~~~~~~

.. csv-table::
   :header: "Option", "Description"
   :widths: 15, 30

   "--yes","Automatically confirm the prompt prior to deleting."


Example::

    $ jb remove sugar_cookies --yes


package
------

The package command packages an application from Juicebox for deployment and
allows you to optionally specify a destination S3 bucket. The command can take
one or more application names separated by spaces.

Options
~~~~~~~

.. csv-table::
   :header: "Option", "Description"
   :widths: 15, 30

   "--bucket","Specify destination S3 bucket."


Example::

    $ jb package sugar_cookies --bucket=jb_uploads_dev


clear_cache
-----------

The clear_cache command allows you to clear the Juicebox cache inside the Docker
container. The command can take one or more application names separated by spaces.

Example::

    $ jb clear_cache


pull
----

The pull command allows you to explicitly download a specific version of the Juicebox container
by specifying the tag.  Implementors will probably not use this very much directly
(it is used behind the scenes to automatically keep your environment up to date), but
the option is there if you need a specific version.

Example::

    $ jb pull stable


test_app
--------

The test_app command allows you to run Gabbi tests of your app in the container.

Example::

    $ jb test_app blueprint


manage
------

The manage command allows you to run arbitrary management commands inside the container.

Options
~~~~~~~

.. csv-table::
   :header: "Option", "Description"
   :widths: 15, 30

   "--options/-o","Options you want to pass to the test command."


Example::

    $ jb manage test --keepdb --failfast

This will run ``python manage.py test --keepdb --failfast`` inside the container.

Environment Commands
====================

These commands are for working with your local Juicebox environment. This
includes running the project watcher, working with Docker, and running
the Django dev server.

ls
--

By default this command only lists tagged images available within the last 30 days.

Options
~~~~~~~

.. csv-table::
   :header: "Option", "Description"
   :widths: 15, 30

   "--showall","Shows all tagged images available regardless of time."
   "--semantic", "Only shows the semantically versioned (release) images."

Example::

    $ jb ls --semantic

      Image Name    Digest                                                            Time Tagged
      ------------  ----------------------------------------------------------------  -------------
      3.14.3        1ef0510f66c37b54f9498784db799b553b500c9382453dde2ac5eece0da943c8  24 days ago
      3.14.4        05a205f4d716a268a93181b0da4de49a4a595306a98d9e302fe3ea6a81abbc02  20 days ago
      3.14.6        4246fbf8d9974a2e69adac29fa2f2e3ab01a2922c9da1e2d422a47a01bb6a9a6  16 days ago
      3.15.0        e8118ab1b66c50127292f1abe178f6dbdd0ecfb11c84fa001bbdcce27a4fb19b  9 days ago
      3.15.1        6522b5d52ffa16750640e4b04166605aa58aa84c935243c312bb876a722f99aa  6 days ago
      3.16.0        7d348d6b018b5c2318131ed76f613ab8392998b1263a7563d7b8a182979d0840  a day ago

Will show all semantically tagged versions.

select
------

Used in conjunction with ``jb ls``, will rewrite the docker-compose.yml file in the environment allowing you to switch between tagged images easily.

Example::

    $ jb select 3.16.0

      Making sure we're in the Juicebox test environment...
      WARNING! Using --password via the CLI is insecure. Use --password-stdin.
      Login Succeeded
      3.16.0: Pulling from juicebox-devlandia
      Digest: sha256:16d7028e28eb24274be54f8620b55544773d75760d63bab07ab119001f7780e2
      Status: Image is up to date for 423681189101.dkr.ecr.us-east-1.amazonaws.com/juicebox-devlandia:3.16.0


watch
-----

This will start the Juicebox project watcher so that changes will be reloaded
as you make them as well as run ``make jswatch`` in a separate thread to detect JS changes.

Example::

    $ jb watch

Please see the install guide for instructions on installing requirements for
the watcher.


start
-----

This command will start your Juicebox VM if it is not already running.  The default behavior automatically
checks for a newer image for the environment you're currently in so you are always on the latest version.
This can be suppressed with the --noupdate flag.

Options
~~~~~~~

.. csv-table::
   :header: "Option", "Description"
   :widths: 15, 30

   "--noupdate","Whether or not to automatically download image updates."


Example::

    $ jb start
    or
    $ jb start --noupdate


stop
----

This command will stop your Juicebox VM if it is already running.

Options
~~~~~~~

None

Example::

    $ jb stop

Built-in Help
=============

The ``jbcli`` also has built-in help documentation::

    $ jb --help

You can also get help for specific commands::

    $ jb create --help
