#!/usr/bin/python

# -*- coding: utf-8 -*-

from PyQt4.QtGui import QMainWindow, QApplication
from PyQt4.QtCore import SIGNAL
from qGitFilter.main_window_ui import Ui_MainWindow
from qGitFilter.git_model import GitModel

import sys


class MainWindow(QMainWindow):

    def __init__(self, debug=False):
        QMainWindow.__init__(self)

        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        self._ui.tableView.setModel(GitModel())
        self._ui.tableView.verticalHeader().hide()
        self._ui.tableView.resizeColumnsToContents()

        self.connect_slots()

    def connect_slots(self):
        # connect the tester page and testcace page to methods
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = MainWindow(debug=True)
    a.show()
    sys.exit(app.exec_())
