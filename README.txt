================
qGitFilterBranch
================

Python Qt4 frontend for git filter-branch. qGitFilterBranch allows you to :
- use filters to display only the commits matching
* committed before/after a date (e.g. commits before 01/01/11)
* committed before/after a weekday (e.g. commits after friday)
* committed before/after an hour (e.g. commits after 20:00)
* the log message contains some string (e.g. matching "CHANGEME")
* the user/email contains some string (e.g. matching "wrong.email@")
- edit the displayed commits to change
* the authored/committed date
* the author/committer name and email
* the log message
- change multiple values at once

Safe try
========
With the demo.sh you can try qGitFilterBranch in a safe environment. The script
will check that all dependencies are met and install GitPython in a virtualenv.
That way it won't interfere with your system packaging tools (like apt).

Installation
============
Dependencies:
* pyuic4: on debian/ubuntu systems, look for a package named 'pyqt4-dev-tools'.

   # apt-get install pyqt4-dev-tools

* gcc: on most systems, look for a package named 'gcc'.

   # apt-get install gcc

* make: on most systems, look for a package named 'make'.

   # apt-get install make

* GitPython: you can use the following command.

   # pip install GitPython

To build qGitFilterBranch UI files:

    $ cd qGitFilterBranch/
    $ make

To launch qGitFilterBranch:

    $ export PYTHONPATH=$PYTHONPATH:<path_to_>/qGitFilterBranch
    $ cd qGitFilterBranch
    $ ./qGitFilterBranch
