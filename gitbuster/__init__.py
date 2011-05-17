# __init__.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QApplication
from gitbuster.main_window import MainWindow
from gitbuster.util import select_git_directory, is_top_git_directory
import sys


def main():
    " This method launches gitbuster."
    app = QApplication(sys.argv)

    if len(sys.argv) == 2 and is_top_git_directory(sys.argv[1]):
        filepath = sys.argv[1]
    else:
        filepath = select_git_directory()

    if filepath:
        window = MainWindow(directory=filepath, debug=True)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(1)
