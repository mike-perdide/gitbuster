# __init__.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt


from PyQt4.QtGui import QApplication, QMessageBox
from gitbuster.main_window import MainWindow
from gitbuster.util import is_top_git_directory, select_git_directory
import signal
import sys
import warnings


def get_gitpython():
    try:
        from git import Repo
    except ImportError:
        warnings.warn("""Couldn't import git. You might want to install GitPython from:
        http://pypi.python.org/pypi/GitPython/""", ImportWarning)
        sys.exit(1)

    from git import __version__
    str_maj, str_min, str_rev = __version__.split(".")
    _maj, _min, _rev = int(str_maj), int(str_min), int(str_rev)
    if  _maj < 0 or (_maj == 0 and _min < 3) or \
        (_maj == 0 and _min == 3 and _rev < 1):
        warnings.warn("This project needs GitPython (>=0.3.1).", ImportWarning)
        raise Exception()
        sys.exit(1)
    return Repo

def main():
    " This method launches gitbuster."
    repo_klass = get_gitpython()
    app = QApplication(sys.argv)

    if len(sys.argv) == 2 and is_top_git_directory(sys.argv[1]):
        filepath = sys.argv[1]
    else:
        filepath = select_git_directory()

    if not filepath:
        sys.exit(1)

    test_repo = repo_klass(filepath)
    if test_repo.is_dirty():
        warning_title = "Unclean repository"
        warning_text = "The chosen repository has unstaged changes. " \
                       "You should commit or stash them. "\
                       "Do you want to continue anyway ?"
        warning_choice = QMessageBox.warning(None, warning_title,
                                             warning_text,
                                             "Yes",
                                             button1Text="No",
                                             button2Text ="Stash")

        if warning_choice == 1:
            sys.exit(2)
        elif warning_choice == 2:
            test_repo.git.stash()

    window = MainWindow(directory=filepath, debug=True)
    window.show()

    #reroute SIGINT to Qt.
    def quit(signum, frame):
        # Clean the repo : stages, tmp_rebase, remotes
        window._ui.actionQuit.trigger()
    signal.signal(signal.SIGINT, quit)

    #run app and exit with same code
    sys.exit(app.exec_())
