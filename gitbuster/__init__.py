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

try:
    from git import Repo
except:
    print """Couldn't import git. You might want to install GitPython from:
    http://pypi.python.org/pypi/GitPython/"""
    sys.exit(1)
try:
    from git import __version__
    str_maj, str_min, str_rev = __version__.split(".")
    _maj, _min, _rev = int(str_maj), int(str_min), int(str_rev)
    if  _maj < 0 or (_maj == 0 and _min < 3) or \
        (_maj == 0 and _min == 3 and _rev < 1):
        raise Exception()
except:
    print "This project needs GitPython (>=0.3.1)."
    sys.exit(1)

def main():
    " This method launches gitbuster."
    app = QApplication(sys.argv)

    if len(sys.argv) == 2 and is_top_git_directory(sys.argv[1]):
        filepath = sys.argv[1]
    else:
        filepath = select_git_directory()

    test_repo = Repo(filepath)
    if test_repo.is_dirty():
        warning_title = "Unclean repository"
        warning_text = "The chosen repository has unstaged changes. " \
                       "You should commit or stash them. "\
                       "Do you want to continue anyway ?"
        warning_choice = QMessageBox.warning(None, warning_title, warning_text,
                                             QMessageBox.Yes, QMessageBox.No)

        if warning_choice == QMessageBox.No:
            sys.exit(2)

    if filepath:
        window = MainWindow(directory=filepath, debug=True)
        window.show()

        def quit(signum, frame):
            window._ui.actionQuit.trigger()
        signal.signal(signal.SIGINT, quit)
        sys.exit(app.exec_())

    sys.exit(1)
