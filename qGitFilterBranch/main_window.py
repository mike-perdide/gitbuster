#!/usr/bin/python

# -*- coding: utf-8 -*-

from PyQt4.QtGui import QMainWindow, QApplication, QCheckBox, QSpacerItem, QSizePolicy, QPushButton
from PyQt4.QtCore import SIGNAL, Qt
from qGitFilter.main_window_ui import Ui_MainWindow
from qGitFilter.q_git_model import QGitModel, NAMES
from qGitFilter.q_git_delegate import QGitDelegate

import sys

AVAILABLE_CHOICES = ['hexsha',
                     'authored_date', 'committed_date',
                     'author', 'committer',
                     'message']
PRE_CHOICE = ['hexsha', 'committed_date', 'committer', 'message']

class MainWindow(QMainWindow):

    def __init__(self, debug=False):
        QMainWindow.__init__(self)

        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        self._ui.tableView.setModel(QGitModel())
        self._ui.tableView.verticalHeader().hide()
        self._ui.tableView.resizeColumnsToContents()
        self._ui.tableView.setItemDelegate(QGitDelegate())

        self.connect_slots()

        self._checkboxes = {}
        self.create_checkboxes()

    def create_checkboxes(self):
        iter = 0
        for checkbox_name in AVAILABLE_CHOICES:
            checkbox = QCheckBox(self._ui.centralwidget)
            self._ui.checkboxLayout.addWidget(checkbox, 0, iter, 1, 1)
            self._checkboxes[checkbox_name] = checkbox
            checkbox.setText(QApplication.translate("MainWindow",
                                                    NAMES[checkbox_name], None,
                                                    QApplication.UnicodeUTF8))
            if checkbox_name in PRE_CHOICE:
                checkbox.setCheckState(Qt.Checked)
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
        self.refreshCheckboxes()

    def refreshCheckboxes(self):
        choices = []
        for checkbox_name in AVAILABLE_CHOICES:
            if self._checkboxes[checkbox_name].isChecked():
                choices.append(checkbox_name)

        self._ui.tableView.model().setColumns(choices)
        self._ui.tableView.model().populate()
        self._ui.tableView.resizeColumnsToContents()

    def connect_slots(self):
        self.connect(self._ui.cancelButton, SIGNAL("clicked()"),
                     self.close)

        self.connect(self._ui.applyButton, SIGNAL("clicked()"),
                     self.apply)

        self.connect(self._ui.mergeCheckBox, SIGNAL("stateChanged(int)"),
                     self.merge_clicked)
    def apply(self):
        self._ui.tableView.model().write()

    def merge_clicked(self):
        model = self._ui.tableView.model()
        check_state = self._ui.mergeCheckBox.checkState()
        if check_state == Qt.Checked:
            model.setMerge(True)
        else:
            model.setMerge(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = MainWindow(debug=True)
    a.show()
    sys.exit(app.exec_())
