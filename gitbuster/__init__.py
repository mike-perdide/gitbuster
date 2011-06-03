# __init__.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt

__version__ = "2.0b1"
from PyQt4.QtGui import QApplication, QMessageBox
from gitbuster.main_window import MainWindow
from gitbuster.util import is_top_git_directory, select_git_directory
from gitbuster.conflicts_dialog import ConflictsDialog
from gfbi_core.git_rebase_process import get_unmerged_files, apply_solutions
import signal
import sys
import os
import warnings
import git
from git import Repo


def main():
    " This method launches gitbuster."
    app = QApplication(sys.argv)

    if len(sys.argv) == 2 and is_top_git_directory(sys.argv[1]):
        filepath = os.path.abspath(sys.argv[1])
    else:
        filepath = select_git_directory()

    if not filepath:
        sys.exit(1)

    test_repo = Repo(filepath)
    if os.path.exists(os.path.join(filepath, ".git/rebase-merge")):
        # Special conflict mode
        os.chdir(filepath)
        unmerged_files = get_unmerged_files()
        conflicts_dialog = ConflictsDialog(unmerged_files)
        ret = conflicts_dialog.exec_()
        if ret:
            solutions = conflicts_dialog.get_solutions()
            apply_solutions(solutions)
            print "Applied your solutions, you can now continue:"
            print "git rebase --continue"
        sys.exit()

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
