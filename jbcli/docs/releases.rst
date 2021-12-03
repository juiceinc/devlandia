========
Releases
========

0.20.0
======

- Improved: Added prompt for how often to check if an image is out of date.  This is done at startup initially
- Added: Command ``jb interval <days>`` to update the value that's set.

0.15.0
======

- Improved: Added option on many jbcli functions for passing an override to the runtime environment.  The default is venv and works as normal, passing ``--runtime venv3`` will run the commands with the py3 interpreter, but it is only valid in the new py3 environment.

0.8.0
=====

- Added: New ``jb ls`` command to list images.  Optional --showall or --semantic flags.  By default only shows tagged images from last 30 days.
- Added: New ``jb select`` command to select a desired tagged image in the test or core environments.
- Improved: ``jb watch`` is now multithreaded and will run both the normal watcher and ``make jswatch`` simultaneously.  In core, if you update ``webpack.config.js`` you will need to stop and restart the watcher for changes to be picked up.

0.6.0
=====

- Added: New ``jb test_app`` command utilizing Gabbi
- Improved: Documentation is now automatically built and deployed on merges to
  the master branch

0.5.0
=====

- Fixed: When switching between develop and release branches, ``jb fix``
  didn't always fix the database, since it can't migrate backwards. Added a
  ``--reset`` flag to completely reset the database.
- Fixed: ``jb create`` was failing to properly initialize the app's Git repo

0.4.0
=====

- Added: More tests! Increased coverage to 99%
- Added: ``jb clone`` to duplicate an existing app
- Added: ``jb cli_upgrade`` to self-upgrade from pip

0.3.1
=====

- Fixed: ``jb create`` was creating apps a directory too deep
- Fixed: Commands were not bailing out properly when errors happened
- Fixed: The installation process was confusing
- Fixed: Failures in one app were not collected and reported on properly
- Added: Initial test suite with PyTest and tox
- Added: ``jb --version`` command

0.3.0
=====

- Add ``add`` and ``remove`` command to manage apps.

0.2.0
=====

- Fully manage local Juicebox environment with Vagrant
- Initialize Git repositories when creating new apps
- Add a project watcher that will reload apps when they are changed, as well
as rebuild JS and CSS when they are changed.
- Add a ``package`` command to package Juicebox apps for deployment

0.1.0
=====

- Create a new Juicebox app from a template
