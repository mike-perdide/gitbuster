# filter_main_class.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QMainWindow, QApplication, QCheckBox, QSpacerItem, \
                        QSizePolicy
from PyQt4.QtCore import SIGNAL, QObject, Qt, QThread, QDir, QSettings, \
                         QDateTime, QModelIndex

from gitbuster.q_git_model import QGitModel, NAMES
from gitbuster.q_git_delegate import QGitDelegate
from gitbuster.confirm_dialog import ConfirmDialog

import time
from datetime import datetime


AVAILABLE_CHOICES = ['hexsha',
                     'authored_date', 'committed_date',
                     'author', 'committer',
                     'message']
PRE_CHOICE = ['hexsha', 'authored_date', 'author', 'message']
AVAILABLE_OPTIONS = {'display_email'    : 'Email',
                     'display_weekday'  : 'Weekday'}


def _connect_button(button, function):
    QObject.connect(button, SIGNAL("clicked()"), function)


class ProgressThread(QThread):
    """
        Thread checking on the git command process, rewriting the
        git repository.
    """

    def __init__(self, progress_bar, model):
        """
            Initializes the thread with the progress bar widget and the
            qGitModel used.

            :param progress_bar:
                Progress bar widdget used to display the progression of the
                git command process.
            :param model:
                The qGitModel used in the MainWindow's view.
        """
        QThread.__init__(self)

        self._progress_bar = progress_bar
        self._model = model

    def run(self):
        """
            Run method of the thread. Will check on the git command process
            progress regularly and updates the progress bar widget.
        """
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


class FilterMainClass():

    def __init__(self, parent, directory, models):
        self.parent = parent
        self._models = models

        self._filters_values = {
            "afterWeekday"  : self.parent._ui.afterWeekdayFilterComboBox.currentIndex,
            "beforeWeekday" : self.parent._ui.beforeWeekdayFilterComboBox.currentIndex,
            "beforeDate"    : self.parent._ui.beforeDateFilterDateEdit.date,
            "afterDate"     : self.parent._ui.afterDateFilterDateEdit.date,
            "beforeHour"    : self.parent._ui.beforeHourFilterTimeEdit.time,
            "afterHour"     : self.parent._ui.afterHourFilterTimeEdit.time,
            "commit"        : self.parent._ui.commitFilterLineEdit.text,
            "nameEmail"     : self.parent._ui.nameEmailFilterLineEdit.text,
            "localOnly"     : None
        }

        self._shown_columns = []

        self.set_current_directory(directory)

        self.connect_slots()

        self.parent._ui.progressBar.hide()

        # Initialize the dateEdit widgets
        dateedits = [self.parent._ui.beforeDateFilterDateEdit,
                     self.parent._ui.afterDateFilterDateEdit,
                     self.parent._ui.reOrderMinDateEdit,
                     self.parent._ui.reOrderMaxDateEdit]

        for dateedit in dateedits:
            dateedit.setDateTime(QDateTime.currentDateTime())

    def set_current_directory(self, directory):
        """
            Sets the current directory and sets up the important widgets.

            :param directory:
                The git directory.
        """
        a_model = QGitModel(directory)
        current_branch = a_model.get_current_branch()

        self._model = self._models[current_branch]
        self.parent._ui.tableView.setModel(self._model)
        self.parent._ui.tableView.verticalHeader().hide()
        self.parent._ui.tableView.setItemDelegate(QGitDelegate(self.parent._ui.tableView))

        self.parent._ui.tableView.resizeColumnsToContents()
        self.parent._ui.tableView.horizontalHeader().setStretchLastSection(True)

        self._checkboxes = {}
        self.create_checkboxes()

        index = 0
        self.parent._ui.currentBranchComboBox.clear()

        for branch in self._models:
            self.parent._ui.currentBranchComboBox.addItem("%s" % str(branch))
            if branch == current_branch:
                current_index = index
            index += 1
        self.parent._ui.currentBranchComboBox.setCurrentIndex(current_index)

    def connect_slots(self):
        """
            Connect the slots to the objects.
        """
        _connect_button(self.parent._ui.cancelButton, self.parent.close)
        _connect_button(self.parent._ui.applyButton, self.apply)

        self.parent.connect(self.parent._ui.mergeCheckBox, SIGNAL("stateChanged(int)"),
                     self.merge_clicked)

        _connect_button(self.parent._ui.toggleModificationsButton, self.toggle_modifications)

        self.parent.connect(self.parent._ui.tableView,
                     SIGNAL("activated(const QModelIndex&)"),
                     self.parent._ui.tableView.edit)

        # Catching progress bar signals.
        self.parent.connect(self.parent._ui.progressBar, SIGNAL("starting"),
                     self.show_progress_bar)

        self.parent.connect(self.parent._ui.progressBar, SIGNAL("update(int)"),
                     self.update_progress_bar)

        self.parent.connect(self.parent._ui.progressBar, SIGNAL("stopping"),
                     self.hide_progress_bar)

        # Change current branch when the currentBranchComboBox current index is
        # changed.
        self.parent.connect(self.parent._ui.currentBranchComboBox,
                     SIGNAL("currentIndexChanged(const QString&)"),
                     self.current_branch_changed)

        # Apply filters when filter edit widgets are edited or when the filter
        # checkboxes are ticked.
        box_widgets = (self.parent._ui.afterWeekdayFilterComboBox,
                       self.parent._ui.beforeWeekdayFilterComboBox)
        for widget in box_widgets:
            self.parent.connect(widget, SIGNAL("currentIndexChanged (int)"),
                         self.apply_filters)

        time_edit_widgets = (self.parent._ui.afterHourFilterTimeEdit,
                             self.parent._ui.beforeHourFilterTimeEdit)
        for widget in time_edit_widgets:
            self.parent.connect(widget, SIGNAL("timeChanged (const QTime&)"),
                         self.apply_filters)

        date_edit_widgets = (self.parent._ui.afterDateFilterDateEdit,
                             self.parent._ui.beforeDateFilterDateEdit)
        for widget in date_edit_widgets:
            self.parent.connect(widget, SIGNAL("dateChanged (const QDate&)"),
                         self.apply_filters)

        line_edit_widgets = (self.parent._ui.nameEmailFilterLineEdit,
                             self.parent._ui.commitFilterLineEdit)
        for widget in line_edit_widgets:
            self.parent.connect(widget, SIGNAL("returnPressed()"),
                         self.apply_filters)

        filter_checkbox_widgets = (self.parent._ui.afterWeekdayFilterCheckBox,
                                   self.parent._ui.beforeWeekdayFilterCheckBox,
                                   self.parent._ui.afterHourFilterCheckBox,
                                   self.parent._ui.beforeHourFilterCheckBox,
                                   self.parent._ui.afterDateFilterCheckBox,
                                   self.parent._ui.beforeDateFilterCheckBox,
                                   self.parent._ui.nameEmailFilterCheckBox,
                                   self.parent._ui.commitFilterCheckBox,
                                   self.parent._ui.localOnlyFilterCheckBox)
        for widget in filter_checkbox_widgets:
            self.parent.connect(widget, SIGNAL("stateChanged(int)"),
                         self.apply_filters)

        # Connecting the re-order push button to the re-order method.
        _connect_button(self.parent._ui.reOrderPushButton, self.reorder_pushed)

    def create_checkboxes(self):
        """
            Creates the checkboxes used to determine what columns are to be
            displayed or what options should be set to the model (i.e. should we
            display the weekday, etc.)
        """
        iter = 0
        for checkbox_name in AVAILABLE_CHOICES:
            checkbox = QCheckBox(self.parent._ui.centralwidget)
            self.parent._ui.checkboxLayout.addWidget(checkbox, 0, iter, 1, 1)
            self._checkboxes[checkbox_name] = checkbox
            checkbox.setText(QApplication.translate("MainWindow",
                                                    NAMES[checkbox_name], None,
                                                    QApplication.UnicodeUTF8))
            if checkbox_name in PRE_CHOICE:
                checkbox.setCheckState(Qt.Checked)
            self.parent.connect(checkbox, SIGNAL("stateChanged(int)"),
                         self.refresh_checkboxes)
            iter += 1

        for checkbox_name in AVAILABLE_OPTIONS:
            checkbox = QCheckBox(self.parent._ui.centralwidget)
            self.parent._ui.checkboxLayout.addWidget(checkbox, 0, iter, 1, 1)
            self._checkboxes[checkbox_name] = checkbox
            checkbox.setText(QApplication.translate("MainWindow",
                                        AVAILABLE_OPTIONS[checkbox_name], None,
                                        QApplication.UnicodeUTF8))
            if checkbox_name in PRE_CHOICE:
                checkbox.setCheckState(Qt.Checked)
            self.parent.connect(checkbox, SIGNAL("stateChanged(int)"),
                         self.refresh_display_options)
            iter += 1

        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding,
                                 QSizePolicy.Minimum)
        self.parent._ui.checkboxLayout.addItem(spacerItem, 0, iter, 1, 1)
        self.refresh_checkboxes()
        self.refresh_display_options()

    def refresh_checkboxes(self):
        """
            When a "column checkbox" is checked or unchecked, we repopulate the
            model so that only the selected columns are displayed.
        """
        self._shown_columns = []
        for checkbox_name in AVAILABLE_CHOICES:
            column_index = AVAILABLE_CHOICES.index(checkbox_name)
            if self._checkboxes[checkbox_name].isChecked():
                self.parent._ui.tableView.showColumn(column_index)
                self._shown_columns.append(column_index)
            else:
                self.parent._ui.tableView.hideColumn(column_index)

        self.parent._ui.tableView.resizeColumnsToContents()
        self.parent._ui.tableView.horizontalHeader().setStretchLastSection(True)

    def refresh_display_options(self):
        """
            When a "display option" is checked or unchecked, we set the display
            options on the model.
        """
        model = self.parent._ui.tableView.model()
        for option_name in AVAILABLE_OPTIONS:
            if self._checkboxes[option_name].isChecked():
                model.enable_option(option_name)
            else:
                model.disable_option(option_name)

        self.parent._ui.tableView.resizeColumnsToContents()
        self.parent._ui.tableView.horizontalHeader().setStretchLastSection(True)

    def reorder_pushed(self):
        """
            The user asks for the automatic re-order of the commits.
        """
        q_max_date = self.parent._ui.reOrderMaxDateEdit.date()
        q_min_date = self.parent._ui.reOrderMinDateEdit.date()

        q_max_time = self.parent._ui.reOrderMaxTimeEdit.time()
        q_min_time = self.parent._ui.reOrderMinTimeEdit.time()

        error = ""
        if not q_max_date >= q_min_date:
            error = "Min date is greater than max date."
        elif not q_max_time >= q_min_time:
            error = "Min time is greater than max time."
        if error:
            self.parent._ui.reOrderErrorsLabel.setText(
                QApplication.translate("MainWindow", error,
                                       None, QApplication.UnicodeUTF8))
            return

        checkboxes = {self.parent._ui.reOrderWeekdayMondayCheckBox : 0,
                      self.parent._ui.reOrderWeekdayTuesdayCheckBox : 1,
                      self.parent._ui.reOrderWeekdayWednesdayCheckBox : 2,
                      self.parent._ui.reOrderWeekdayThursdayCheckBox : 3,
                      self.parent._ui.reOrderWeekdayFridayCheckBox : 4,
                      self.parent._ui.reOrderWeekdaySaturdayCheckBox : 5,
                      self.parent._ui.reOrderWeekdaySundayCheckBox : 6,
        }
        weekdays = []
        for checkbox in checkboxes:
            if checkbox.checkState() == Qt.Checked:
                weekdays.append(checkboxes[checkbox])

        if not weekdays:
            weekdays = (0, 1, 2, 3, 4, 5, 6)


        q_max_date = q_max_date.addDays(1)
        max_date = datetime(q_max_date.year(), q_max_date.month(),
                            q_max_date.day())
        min_date = datetime(q_min_date.year(), q_min_date.month(),
                            q_min_date.day())

        max_time = datetime(2000, 1, 1, q_max_time.hour(),
                            q_max_time.minute(), q_max_time.second())
        min_time = datetime(2000, 1, 1, q_min_time.hour(),
                            q_min_time.minute(), q_min_time.second())

        model = self.parent._ui.tableView.model()
        model.reorder_commits((min_date, max_date),
                              ((min_time, max_time),),
                              weekdays)

    def current_branch_changed(self, new_branch_name):
        """
            When the currentBranchComboBox current index is changed, set the
            current branch of the model to the new branch.
        """
        for branch in self._models:
            if new_branch_name == str(branch):
                self._model = self._models[branch]
                self.parent._ui.tableView.setModel(self._model)
                self.refresh_checkboxes()
                break

    def merge_clicked(self, check_state):
        """
            When the "merge checkbox" is checked or unchecked, pass on the
            option to the model.
        """
        model = self.parent._ui.tableView.model()
        model.setMerge(check_state == Qt.Checked)

    def apply_filters(self):
        """
            When a "filter checkbox" is checked or unchecked, set the filters on
            the model and reset it.
        """
        tableView = self.parent._ui.tableView
        model = tableView.model()

        filters = []
        for checkbox_name in self._filters_values:
            checkbox = self._filterbox_byname(checkbox_name)

            if checkbox.checkState() == Qt.Checked:
                filter = self._filter_byname(checkbox_name)
                model.filter_set(checkbox_name, filter)
                filters.append(checkbox_name)
            else:
                model.filter_unset(checkbox_name)


        total_filter_score = 0
        for word in ("Hour", "Date", "Weekday"):
            group = "after%s" % word, "before%s" % word
            if any(item in filters for item in group):
                total_filter_score += 1

        for item in ("nameEmail", "commit", "localOnly"):
            if item in filters:
                total_filter_score += 1


        for row in xrange(model.rowCount()):
            tableView.showRow(row)

        if total_filter_score:
            for row in xrange(model.rowCount()):
                score = 0
                for column in self._shown_columns:
                    index = model.index(row, column)
                    score += model.filter_score(index)

                if score < total_filter_score:
                    tableView.hideRow(row)

        tableView.reset()

    def _filterbox_byname(self, name):
        """
        Given a filter name, returns corresponding checkbox object
        """
        return getattr(self.parent._ui, '%sFilterCheckBox' % name)

    def _filter_byname(self, name):
        """
        Given a filter name, returns the filter, or None
        """
        getter = self._filters_values[name]

        if getter:
            return getter()

        return None

    def toggle_modifications(self):
        """
            When the toggleModifications button is pressed, change the displayed
            model.
        """
        current_model = self.parent._ui.tableView.model()
        if current_model == self._model:
            # if the displayed model is the editable model
            orig_model = current_model.get_orig_q_git_model()
            self.parent._ui.tableView.setModel(orig_model)
            label = "&Show modifications"
        else:
            self.parent._ui.tableView.setModel(self._model)
            label = "&Hide modifications"

        self.parent._ui.toggleModificationsButton.setText(
            QApplication.translate("MainWindow", label,
                                   None, QApplication.UnicodeUTF8))

    def apply(self):
        """
            Write the modifications to the git repository.
        """
        model = self.parent._ui.tableView.model()
        modified_commits_count = model.get_modified_count()
        if modified_commits_count > 0:
            to_rewrite_count = model.get_to_rewrite_count()

            msgBox = ConfirmDialog(modified_count=modified_commits_count,
                                   to_rewrite_count=to_rewrite_count)
            ret = msgBox.exec_()

            if ret:
                ui = msgBox._ui
                log_checked = ui.logCheckBox.checkState() == Qt.Checked
                script_checked = ui.scriptCheckBox.checkState() == Qt.Checked

                model.write(log_checked, script_checked)

                # If we have more than 80 commits modified, show progress bar
                if to_rewrite_count > 80:
                    progress_bar = self.parent._ui.progressBar
                    self.progress_thread = ProgressThread(progress_bar, model)
                    self.progress_thread.start()
                else:
                    # Wait a few milliseconds and before repopulating the model
                    while not model.is_finished_writing():
                        time.sleep(0.2)
                    model.populate()

    def show_progress_bar(self):
        """
            Shows the progress bar representing the progress of the writing
            process.
        """
        self.parent._ui.progressBar.show()
        self.parent._ui.applyButton.setDisabled(True)
        self.parent._ui.cancelButton.setDisabled(True)

    def update_progress_bar(self, value):
        """
            Updates the progress bar with a value.

            :param value:
                Progression of the write process, between 0 and 100
        """
        self.parent._ui.progressBar.setValue(value)

    def hide_progress_bar(self):
        """
            Hide the progress bar representing the progress of the writing
            process.
        """
        self.parent._ui.progressBar.hide()
        self.parent._ui.applyButton.setEnabled(True)
        self.parent._ui.cancelButton.setEnabled(True)
