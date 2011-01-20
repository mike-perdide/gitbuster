#!/usr/bin/python

# -*- coding: utf-8 -*-

from PyQt4.QtGui import QMainWindow, QApplication, QCheckBox, QSpacerItem, QSizePolicy, QMessageBox, QProgressBar
from PyQt4.QtCore import SIGNAL, Qt, QThread
from qGitFilterBranch.main_window_ui import Ui_MainWindow
from qGitFilterBranch.q_git_model import QGitModel, NAMES
from qGitFilterBranch.q_git_delegate import QGitDelegate
import time

AVAILABLE_CHOICES = ['hexsha',
                     'authored_date', 'committed_date',
                     'author', 'committer',
                     'message']
PRE_CHOICE = ['hexsha', 'authored_date', 'author', 'message']
AVAILABLE_OPTIONS = {'display_email'    : 'Email',
                     'display_weekday'  : 'Weekday'}

class ProgressThread(QThread):

    def __init__(self, progress_bar, model):
        QThread.__init__(self)

        self._progress_bar = progress_bar
        self._model = model

    def run(self):
        model = self._model
        progress_bar = self._progress_bar

        progress_bar.emit(SIGNAL("starting"))
        progress_bar.emit(SIGNAL("update(int)"), 0)

        while not model.is_finished_writing():
            # While the git filter-branch command isn't finished, update the
            # progress bar with the process progress.
            progress = model.progress()

            if progress:
                progress_bar.emit(SIGNAL("update(int)"), int(progress * 100))
            time.sleep(0.5)

        progress_bar.emit(SIGNAL("update(int)"), 100)
        time.sleep(0.2)
        progress_bar.emit(SIGNAL("stopping"))

        # Repopulate the model after the filter-branch is done.
        model.populate()


class MainWindow(QMainWindow):

    def __init__(self, directory=".", debug=False):
        QMainWindow.__init__(self)

        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        model = QGitModel(directory=directory)
        self._ui.tableView.setModel(model)
        model.setMerge(True)
        model.enable_option("filters")
        self._ui.tableView.verticalHeader().hide()
        self._ui.tableView.setItemDelegate(QGitDelegate(self._ui.tableView))

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

        self._ui.tableView.resizeColumnsToContents()
        self._ui.tableView.horizontalHeader().setStretchLastSection(True)

        self._ui.progressBar.hide()

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

        self.connect(self._ui.filterButton, SIGNAL("clicked()"),
                     self.apply_filters)

        self.connect(self._ui.toggleModificationsButton, SIGNAL("clicked()"),
                     self.toggle_modifications)

        self.connect(self._ui.tableView,
                     SIGNAL("activated(const QModelIndex&)"),
                     self._ui.tableView.edit)

        # Catching progress bar signals.
        self.connect(self._ui.progressBar, SIGNAL("starting"),
                     self.show_progress_bar)

        self.connect(self._ui.progressBar, SIGNAL("update(int)"),
                     self.update_progress_bar)

        self.connect(self._ui.progressBar, SIGNAL("stopping"),
                     self.hide_progress_bar)

        # Apply filters when filter edit widgets are edited or when the filter
        # checkboxes are ticked.
        box_widgets = (self._ui.afterWeekdayFilterComboBox,
                       self._ui.beforeWeekdayFilterComboBox)
        for widget in box_widgets:
            self.connect(widget, SIGNAL("currentIndexChanged (int)"),
                         self.apply_filters)

        time_edit_widgets = (self._ui.afterHourFilterTimeEdit,
                             self._ui.beforeHourFilterTimeEdit)
        for widget in time_edit_widgets:
            self.connect(widget, SIGNAL("timeChanged (const QTime&)"),
                         self.apply_filters)

        date_edit_widgets = (self._ui.afterDateFilterDateEdit,
                             self._ui.beforeDateFilterDateEdit)
        for widget in time_edit_widgets:
            self.connect(widget, SIGNAL("dateChanged (const QDate&)"),
                         self.apply_filters)

        line_edit_widgets = (self._ui.nameEmailFilterLineEdit,
                             self._ui.commitFilterLineEdit)
        for widget in line_edit_widgets:
            self.connect(widget, SIGNAL("returnPressed()"),
                         self.apply_filters)

        filter_checkbox_widgets = (self._ui.afterWeekdayFilterCheckBox,
                                   self._ui.beforeWeekdayFilterCheckBox,
                                   self._ui.afterHourFilterCheckBox,
                                   self._ui.beforeHourFilterCheckBox,
                                   self._ui.afterDateFilterCheckBox,
                                   self._ui.beforeDateFilterCheckBox,
                                   self._ui.nameEmailFilterCheckBox,
                                   self._ui.commitFilterCheckBox)
        for widget in filter_checkbox_widgets:
            self.connect(widget, SIGNAL("stateChanged(int)"),
                         self.apply_filters)

    def apply(self):
        model = self._ui.tableView.model()
        modified_commits_count = model.get_modified_count()
        if modified_commits_count > 0:
            to_rewrite_count = model.get_to_rewrite_count()

            if modified_commits_count > 1:
                msg = "%d commits have been modified.\n"
            else:
                msg = "%d commit has been modified.\n"

            if to_rewrite_count > 1:
                msg += "%d commits of the git tree are about to be rewritten."
            else:
                msg += "%d commit of the git tree is about to be rewritten."

            msgBox = QMessageBox()
            msgBox.setText(msg % (modified_commits_count, to_rewrite_count))
            msgBox.setInformativeText("Do you want to continue ?")
            msgBox.setStandardButtons(QMessageBox.Ok |
                                      QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Cancel)
            ret = msgBox.exec_()

            if ret == QMessageBox.Ok:
                check_state = self._ui.logCheckBox.checkState()
                if check_state == Qt.Checked:
                    log_checked = True
                else:
                    log_checked = False

                model = self._ui.tableView.model()
                model.write(log_checked)

                # If we have more than 80 commits modified, show progress bar
                if to_rewrite_count > 80:
                    progress_bar = self._ui.progressBar
                    self.progress_thread = ProgressThread(progress_bar, model)
                    self.progress_thread.start()
                else:
                    # Wait a few milliseconds and before repopulating the model
                    while not model.is_finished_writing():
                        time.sleep(0.2)
                    model.populate()

    def show_progress_bar(self):
        self._ui.progressBar.show()
        self._ui.applyButton.setDisabled(True)
        self._ui.cancelButton.setDisabled(True)

    def update_progress_bar(self, value):
        self._ui.progressBar.setValue(value)

    def hide_progress_bar(self):
        self._ui.progressBar.hide()
        self._ui.applyButton.setEnabled(True)
        self._ui.cancelButton.setEnabled(True)

    def merge_clicked(self, check_state):
        model = self._ui.tableView.model()

        if check_state == Qt.Checked:
            model.setMerge(True)
        else:
            model.setMerge(False)

    def apply_filters(self):
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

