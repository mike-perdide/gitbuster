#!/usr/bin/python

# -*- coding: utf-8 -*-

from PyQt4.QtGui import QMainWindow, QApplication, QCheckBox, QSpacerItem, QSizePolicy, QPushButton
from PyQt4.QtCore import SIGNAL, Qt
from qGitFilterBranch.main_window_ui import Ui_MainWindow
from qGitFilterBranch.q_git_model import QGitModel, NAMES
from qGitFilterBranch.q_git_delegate import QGitDelegate

import sys

AVAILABLE_CHOICES = ['hexsha',
                     'authored_date', 'committed_date',
                     'author', 'committer',
                     'message']
PRE_CHOICE = ['hexsha', 'authored_date', 'author', 'message']
AVAILABLE_OPTIONS = {'display_email'    : 'Email',
                     'display_weekday'  : 'Weekday'}

class MainWindow(QMainWindow):

    def __init__(self, debug=False):
        QMainWindow.__init__(self)

        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        model = QGitModel()
        self._ui.tableView.setModel(model)
        model.setMerge(True)
        self._ui.tableView.verticalHeader().hide()
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

        self._checkboxes = {}
        self.create_checkboxes()

        self._ui.filtersWidget.hide()
        self._ui.filterButton.hide()

        self._ui.tableView.resizeColumnsToContents()
        self._ui.tableView.horizontalHeader().setStretchLastSection(True)

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
            self.connect(checkbox, SIGNAL("stateChanged(int)"),
                         self.refresh_checkboxes)
            iter += 1

        for checkbox_name in AVAILABLE_OPTIONS:
            checkbox = QCheckBox(self._ui.centralwidget)
            self._ui.checkboxLayout.addWidget(checkbox, 0, iter, 1, 1)
            self._checkboxes[checkbox_name] = checkbox
            checkbox.setText(QApplication.translate("MainWindow",
                                        AVAILABLE_OPTIONS[checkbox_name], None,
                                        QApplication.UnicodeUTF8))
            if checkbox_name in PRE_CHOICE:
                checkbox.setCheckState(Qt.Checked)
            self.connect(checkbox, SIGNAL("stateChanged(int)"),
                         self.refresh_display_options)
            iter += 1

        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding,
                                 QSizePolicy.Minimum)
        self._ui.checkboxLayout.addItem(spacerItem, 0, iter, 1, 1)
        self.refresh_checkboxes()
        self.refresh_display_options()

    def refresh_checkboxes(self):
        choices = []
        for checkbox_name in AVAILABLE_CHOICES:
            if self._checkboxes[checkbox_name].isChecked():
                choices.append(checkbox_name)

        self._ui.tableView.model().setColumns(choices)
        self._ui.tableView.model().populate()
        self._ui.tableView.resizeColumnsToContents()
        self._ui.tableView.horizontalHeader().setStretchLastSection(True)

    def refresh_display_options(self):
        model = self._ui.tableView.model()
        for option_name in AVAILABLE_OPTIONS:
            if self._checkboxes[option_name].isChecked():
                model.enable_option(option_name)
            else:
                model.disable_option(option_name)

        self._ui.tableView.resizeColumnsToContents()
        self._ui.tableView.horizontalHeader().setStretchLastSection(True)

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

        self.connect(self._ui.toggleModificationsButton, SIGNAL("clicked()"),
                     self.toggle_modifications)

        self.connect(self._ui.tableView, SIGNAL("activated(const QModelIndex&)"),
                     self._ui.tableView.edit)

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
            model.enable_option("filters")
        else:
            self._ui.filtersWidget.hide()
            extra_height = self._ui.filtersWidget.height() + 6
            self.resize(current_width,
                        current_height - extra_height)
            self._ui.filterButton.hide()
            model.disable_option("filters")

        model.reset()

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

        model.populate()
        model.reset()

    def toggle_modifications(self):
        model = self._ui.tableView.model()

        model.toggle_modifications()

        if model.show_modifications():
            label = "Hide modifications"
        else:
            label = "Show modifications"

        self._ui.toggleModificationsButton.setText(
            QApplication.translate("MainWindow", label,
                                   None, QApplication.UnicodeUTF8))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = MainWindow(debug=True)
    a.show()
    sys.exit(app.exec_())
