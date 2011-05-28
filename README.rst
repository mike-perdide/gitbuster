============
gitbuster II
============
Formerly qGitFilterBranch.

" If there's something strange / In your history / Who you gonna call ? / GitBuster! "

Frontend for git cherry-pick/git rebase:

- use drag and drop to rebase a branch onto another (one or a set of commits)

- graphical resolution of merge conflicts by displaying:
    * the original content of the file
    * the patch that was meant to be applied bu failed
    * the unmerged content of the file for you to edit if necessary
    * a set of resolution choices (delete the file, add the file, add the file with custom content)

- works with remote branches (directory on your filesystem or web)

- rename a branch or create a new branch from any commit of your history

- special conflicts mode that can be called right after a conflict when using 'git rebase -i'

Frontend for git filter-branch:

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

- automatically re-order a given set of commits onto a given set of time ranges

--------
Safe try
--------
With the demo.sh you can try gitbuster in a safe environment. The script
will check that all dependencies are met and install GitPython in a virtualenv.
That way it won't interfere with your system packaging tools (like apt).

--------------------
Installing From PyPI
--------------------

Installing with pip::

    $ pip install gitbuster

-------------------
Manual Installation
-------------------
Download the tarball, then::

    $ tar xvf gitbuster-2.0.0b.tar.gz
    $ cd gitbuster

Installing with distutils::

    $ python setup.py install

Installing with distutils2::
    
    $ pysetup run install_dist

---------------------
Building From Sources
---------------------
Dependencies:

- pyuic4: on debian/ubuntu systems, look for a package named 'pyqt4-dev-tools'.
- gcc: on most systems, look for a package named 'gcc'.
- make: on most systems, look for a package named 'make'.
- gfbi_core: see https://github.com/mike-perdide/gfbi_core.
- GitPython


To build gitbuster UI files::

    $ cd gitbuster/
    $ make

To launch gitbuster::

    $ export PYTHONPATH=$PYTHONPATH:<path_to_>/gitbuster
    $ cd gitbuster
    $ ./gitbuster
