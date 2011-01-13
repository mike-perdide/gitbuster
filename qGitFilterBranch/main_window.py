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

        self._filters_checkboxes = {
            "afterWeekday"  : self._ui.afterWeekdayFilterComboBox.currentIndex,
            "beforeWeekday" : self._ui.beforeWeekdayFilterComboBox.currentIndex,
            "beforeDate"    : self._ui.beforeDateFilterDateEdit.date,
            "afterDate"     : self._ui.afterDateFilterDateEdit.date,
            "beforeHour"    : self._ui.beforeHourFilterTimeEdit.time,
            "afterHour"     : self._ui.afterHourFilterTimeEdit.time,
            "commit"        : self._ui.commitFilterLineEdit.text,
            "nameEmail"     : self._ui.nameEmailFilterLineEdit.text
        }

        self.connect_slots()

        self._field_checkboxes = {}
        self.create_checkboxes()

        self._ui.filtersWidget.hide()
        self._ui.filterButton.hide()

    def create_checkboxes(self):
        iter = 0
        for checkbox_name in AVAILABLE_CHOICES:
            checkbox = QCheckBox(self._ui.centralwidget)
            self._ui.checkboxLayout.addWidget(checkbox, 0, iter, 1, 1)
            self._field_checkboxes[checkbox_name] = checkbox
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
            if self._field_checkboxes[checkbox_name].isChecked():
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

        self.connect(self._ui.filtersCheckBox, SIGNAL("stateChanged(int)"),
                     self.filters_clicked)

        self.connect(self._ui.filterButton, SIGNAL("clicked()"),
                     self.get_filters)

    def apply(self):
        self._ui.tableView.model().write()

    def merge_clicked(self, check_state):
        model = self._ui.tableView.model()

        if check_state == Qt.Checked:
            model.setMerge(True)
        else:
            model.setMerge(False)

    def filters_clicked(self, check_state):
        model = self._ui.tableView.model()

        current_width = self.size().width()
        current_height = self.size().height()

        if check_state == Qt.Checked:
            self._ui.filtersWidget.show()
            extra_height = self._ui.filtersWidget.height() + 6
            self.resize(current_width,
                        current_height + extra_height)
            self._ui.filterButton.show()
        else:
            self._ui.filtersWidget.hide()
            extra_height = self._ui.filtersWidget.height() + 6
            self.resize(current_width,
                        current_height - extra_height)
            self._ui.filterButton.hide()

    def get_filters(self):
        model = self._ui.tableView.model()

        for checkbox_name in self._filters_checkboxes:
            checkbox = eval("self._ui." + checkbox_name + "FilterCheckBox")
            check_state = checkbox.checkState()

            if check_state == Qt.Checked:
                get_value = self._filters_checkboxes[checkbox_name]
                value = get_value()
                model.filter_set(checkbox_name, value)
            else:
                model.filter_unset(checkbox_name)

        model.reset()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = MainWindow(debug=True)
    a.show()
    sys.exit(app.exec_())
