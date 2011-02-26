# __init__.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QApplication
from gitbuster.main_window import MainWindow, select_git_directory
import sys

def main():
    app = QApplication(sys.argv)

    filepath = select_git_directory()

    if filepath:
        a = MainWindow(directory=filepath, debug=True)
        a.show()
        sys.exit(app.exec_())
    else:
        sys.exit(1)
