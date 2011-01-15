#!/usr/bin/python

# -*- coding: utf-8 -*-

from PyQt4.QtGui import QApplication
from qGitFilterBranch.main_window import MainWindow
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = MainWindow(debug=True)
    a.show()
    sys.exit(app.exec_())
