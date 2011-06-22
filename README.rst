============
gitbuster II
============
Formerly qGitFilterBranch.

" If there's something strange / In your history / Who you gonna call ? / GitBuster! "

Frontend for git cherry-pick/git rebase:

- use drag and drop to rebase a branch onto another (one or a set of commits)

- graphical resolution of merge conflicts by displaying:
    * the original content of the file
    * the patch that was meant to be applied but failed
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
Get the code::

    $ git clone --recursive git://github.com/mike-perdide/gitbuster.git
    $ cd gitbuster

Installing ::

    $ make install

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

----
Bugs
----
There are bugs in gitbuster, especially in:

- dealing with some unicode commit metadata
- cherry-picking big commits (+10 modified files) may result in gitbuster being blocked

If you find any bug, don't hesitate to report it and/or send patches:

- on freenode, channel #gitbuster or directly to me (mike_perdide).
- by email: mike dot perdide at gmail dot com
- on github: https://github.com/mike-perdide/gitbuster/issues/new

Please mention the version you're using, or the tip of the repository if you're using the development version, and the steps to reproduce.
Your help will be greatly appreciated.

-------
Warning
-------

As of v2.1, gitbuster now handles merge commits correctly instead of deleting them as "git rebase -i" would.
You can modifiy metadata of an old commit without worrying that it would mess up your history tree.
However, you should be careful when reordering commits in a non flat history, as gitbuster doesn't display correctly the branched histories.
The rule of thumb is that inserting a commit in a branch will take the commit below in the tableView as reference: the inserted commit inserted will take its place, and the reference commit will become the inserted commit's parent.
All commits that had the reference commit has parent will now have the inserted commit as parent.
