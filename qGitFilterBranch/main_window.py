#!/usr/bin/python

# -*- coding: utf-8 -*-

from PyQt4.QtGui import QMainWindow, QApplication, QCheckBox, QSpacerItem, QSizePolicy, QPushButton
from PyQt4.QtCore import SIGNAL
from qGitFilter.main_window_ui import Ui_MainWindow
from qGitFilter.git_model import GitModel

import sys

AVAILABLE_CHOICES = ['id', 'id_abbrev',
                     'authored_date', 'committed_date',
                     'author', 'committer',
                     'message', 'summary']

class MainWindow(QMainWindow):

    def __init__(self, debug=False):
        QMainWindow.__init__(self)

        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        self._ui.tableView.setModel(GitModel())
        self._ui.tableView.verticalHeader().hide()
        self._ui.tableView.resizeColumnsToContents()

        self.connect_slots()

        self._checkboxes = {}
        self.create_checkboxes()

    def create_checkboxes(self):
        iter = 0
        for checkbox_name in AVAILABLE_CHOICES:
            checkbox = QCheckBox(self._ui.centralwidget)
            self._ui.checkboxLayout.addWidget(checkbox, 0, iter, 1, 1)
            self._checkboxes[checkbox_name] = checkbox
            checkbox.setText(QApplication.translate("MainWindow", checkbox_name,
                                        None, QApplication.UnicodeUTF8))
            iter += 1

        refreshButton = QPushButton(self._ui.centralwidget)
        refreshButton.setObjectName("refreshButton")
        refreshButton.setText(QApplication.translate("MainWindow", "Refresh",
                                        None, QApplication.UnicodeUTF8))
        self._ui.checkboxLayout.addWidget(refreshButton, 0, iter, 1, 1)
        self.connect(refreshButton, SIGNAL("pressed()"),
                     self.refreshCheckboxes)
        iter += 1

        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding,
                                 QSizePolicy.Minimum)
        self._ui.checkboxLayout.addItem(spacerItem, 0, iter, 1, 1)

    def refreshCheckboxes(self):
        choices = []
        for checkbox_name in AVAILABLE_CHOICES:
            if self._checkboxes[checkbox_name].isChecked():
                choices.append(checkbox_name)

        self._ui.tableView.model().setColumns(choices)
        self._ui.tableView.model().populate()
        self._ui.tableView.resizeColumnsToContents()

    def connect_slots(self):
        # connect the tester page and testcace page to methods
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = MainWindow(debug=True)
    a.show()
    sys.exit(app.exec_())
