# filter_main_class.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QApplication, QCheckBox, QSpacerItem, QSizePolicy
from PyQt4.QtCore import SIGNAL, QObject, Qt, QThread, QDateTime

from gitbuster.q_git_model import NAMES
from gitbuster.q_git_delegate import QGitDelegate
from gitbuster.util import _connect_button

import time
from datetime import datetime


AVAILABLE_CHOICES = ['hexsha',
                     'authored_date', 'committed_date',
                     'author_name', 'author_email',
                     'committer_name', 'committer_email',
                     'message']
PRE_CHOICE = ['hexsha', 'authored_date', 'author_name', 'message']
AVAILABLE_OPTIONS = {'display_weekday'  : 'Weekday'}


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

        self.gui = self.parent._ui
        self._filters_values = {
            "afterWeekday"  : self.gui.afterWeekdayFilterComboBox.currentIndex,
            "beforeWeekday" : self.gui.beforeWeekdayFilterComboBox.currentIndex,
            "beforeDate"    : self.gui.beforeDateFilterDateEdit.date,
            "afterDate"     : self.gui.afterDateFilterDateEdit.date,
            "beforeHour"    : self.gui.beforeHourFilterTimeEdit.time,
            "afterHour"     : self.gui.afterHourFilterTimeEdit.time,
            "commit"        : self.gui.commitFilterLineEdit.text,
            "nameEmail"     : self.gui.nameEmailFilterLineEdit.text,
            "localOnly"     : None
        }

        self._shown_columns = []
        self._checkboxes = {}
        self._model = None

        self.set_current_directory(directory)

        self.connect_slots()

        self.gui.progressBar.hide()

        # Initialize the dateEdit widgets
        dateedits = [self.gui.beforeDateFilterDateEdit,
                     self.gui.afterDateFilterDateEdit,
                     self.gui.reOrderMinDateEdit,
                     self.gui.reOrderMaxDateEdit]

        for dateedit in dateedits:
            dateedit.setDateTime(QDateTime.currentDateTime())

    def set_current_directory(self, directory):
        """
            Sets the current directory and sets up the important widgets.

            :param directory:
                The git directory.
        """
        current_branch = self.parent.current_branch

        self._model = self._models[current_branch]
        self.gui.tableView.setModel(self._model)
        self.gui.tableView.verticalHeader().hide()
        self.gui.tableView.setItemDelegate(QGitDelegate(self.gui.tableView))

        self.gui.tableView.resizeColumnsToContents()
        self.gui.tableView.horizontalHeader().setStretchLastSection(True)

        self.create_checkboxes()

        index = 0
        self.gui.currentBranchComboBox.clear()

        for branch in self._models:
            self.gui.currentBranchComboBox.addItem("%s" % str(branch))
            if branch == current_branch:
                current_index = index
            index += 1
        self.gui.currentBranchComboBox.setCurrentIndex(current_index)

    def connect_slots(self):
        """
            Connect the slots to the objects.
        """
        connect = QObject.connect

        connect(self.gui.mergeCheckBox, SIGNAL("stateChanged(int)"),
                self.merge_clicked)

        # This can't be done using edit triggers : edit when enter is pressed
        connect(self.gui.tableView,
                SIGNAL("activated(const QModelIndex&)"),
                self.gui.tableView.edit)

        # Catching progress bar signals.
        connect(self.gui.progressBar, SIGNAL("starting"),
                                                    self.show_progress_bar)
        connect(self.gui.progressBar, SIGNAL("update(int)"),
                                                    self.update_progress_bar)
        connect(self.gui.progressBar, SIGNAL("stopping"),
                                                    self.hide_progress_bar)

        # Change current branch when the currentBranchComboBox current index is
        # changed.
        connect(self.gui.currentBranchComboBox,
                SIGNAL("currentIndexChanged(const QString&)"),
                self.current_branch_changed)

        # Apply filters when filter edit widgets are edited or when the filter
        # checkboxes are ticked.
        filters_widgets = {
            "currentIndexChanged (int)" : (self.gui.afterWeekdayFilterComboBox,
                                          self.gui.beforeWeekdayFilterComboBox),
            "timeChanged (const QTime&)": (self.gui.afterHourFilterTimeEdit,
                                           self.gui.beforeHourFilterTimeEdit),
            "dateChanged (const QDate&)": (self.gui.afterDateFilterDateEdit,
                                           self.gui.beforeDateFilterDateEdit),
            "returnPressed()"           : (self.gui.nameEmailFilterLineEdit,
                                           self.gui.commitFilterLineEdit),
            "stateChanged(int)"         : (self.gui.afterWeekdayFilterCheckBox,
                                           self.gui.beforeWeekdayFilterCheckBox,
                                           self.gui.afterHourFilterCheckBox,
                                           self.gui.beforeHourFilterCheckBox,
                                           self.gui.afterDateFilterCheckBox,
                                           self.gui.beforeDateFilterCheckBox,
                                           self.gui.nameEmailFilterCheckBox,
                                           self.gui.commitFilterCheckBox,
                                           self.gui.localOnlyFilterCheckBox),
        }
        for signal, widgets in filters_widgets.items():
            for widget in widgets:
                connect(widget, SIGNAL(signal), self.apply_filters)

        # Connecting the re-order push button to the re-order method.
        _connect_button(self.gui.reOrderPushButton, self.reorder_pushed)

    def create_checkboxes(self):
        """
            Creates the checkboxes used to determine what columns are to be
            displayed or what options should be set to the model (i.e. should we
            display the weekday, etc.)
        """
        count = 0
        for checkbox_name in AVAILABLE_CHOICES:
            checkbox = QCheckBox(self.gui.centralwidget)
            self.gui.checkboxLayout.addWidget(checkbox, 0, count, 1, 1)
            self._checkboxes[checkbox_name] = checkbox
            checkbox.setText(QApplication.translate("MainWindow",
                                                    NAMES[checkbox_name], None,
                                                    QApplication.UnicodeUTF8))
            if checkbox_name in PRE_CHOICE:
                checkbox.setCheckState(Qt.Checked)
            self.parent.connect(checkbox, SIGNAL("stateChanged(int)"),
                                self.refresh_checkboxes)
            count += 1

        for checkbox_name in AVAILABLE_OPTIONS:
            checkbox = QCheckBox(self.gui.centralwidget)
            self.gui.checkboxLayout.addWidget(checkbox, 0, count, 1, 1)
            self._checkboxes[checkbox_name] = checkbox
            checkbox.setText(QApplication.translate("MainWindow",
                                        AVAILABLE_OPTIONS[checkbox_name], None,
                                        QApplication.UnicodeUTF8))
            if checkbox_name in PRE_CHOICE:
                checkbox.setCheckState(Qt.Checked)
            self.parent.connect(checkbox, SIGNAL("stateChanged(int)"),
                         self.refresh_display_options)
            count += 1

        spacer_item = QSpacerItem(40, 20, QSizePolicy.Expanding,
                                 QSizePolicy.Minimum)
        self.gui.checkboxLayout.addItem(spacer_item, 0, count, 1, 1)
        self.refresh_checkboxes()
        self.refresh_display_options()

    def refresh_checkboxes(self):
        """
            When a "column checkbox" is checked or unchecked, we change the
            view's displayed columns model so that only the selected columns are
            displayed.
        """
        self._shown_columns = []
        for checkbox_name in AVAILABLE_CHOICES:
            column_index = AVAILABLE_CHOICES.index(checkbox_name)
            if self._checkboxes[checkbox_name].isChecked():
                self.gui.tableView.showColumn(column_index)
                self._shown_columns.append(column_index)
            else:
                self.gui.tableView.hideColumn(column_index)

        self.gui.tableView.resizeColumnsToContents()
        self.gui.tableView.horizontalHeader().setStretchLastSection(True)

    def refresh_display_options(self):
        """
            When a "display option" is checked or unchecked, we set the display
            options on the model.
        """
        model = self.gui.tableView.model()
        for option_name in AVAILABLE_OPTIONS:
            if self._checkboxes[option_name].isChecked():
                model.enable_option(option_name)
            else:
                model.disable_option(option_name)

        self.gui.tableView.resizeColumnsToContents()
        self.gui.tableView.horizontalHeader().setStretchLastSection(True)

    def reorder_pushed(self):
        """
            The user asks for the automatic re-order of the commits.
        """
        q_max_date = self.gui.reOrderMaxDateEdit.date()
        q_min_date = self.gui.reOrderMinDateEdit.date()

        q_max_time = self.gui.reOrderMaxTimeEdit.time()
        q_min_time = self.gui.reOrderMinTimeEdit.time()

        error = ""
        if not q_max_date >= q_min_date:
            error = "Min date is greater than max date."
        elif not q_max_time >= q_min_time:
            error = "Min time is greater than max time."
        if error:
            self.gui.reOrderErrorsLabel.setText(
                QApplication.translate("MainWindow", error,
                                       None, QApplication.UnicodeUTF8))
            return

        checkboxes = {self.gui.reOrderWeekdayMondayCheckBox : 0,
                      self.gui.reOrderWeekdayTuesdayCheckBox : 1,
                      self.gui.reOrderWeekdayWednesdayCheckBox : 2,
                      self.gui.reOrderWeekdayThursdayCheckBox : 3,
                      self.gui.reOrderWeekdayFridayCheckBox : 4,
                      self.gui.reOrderWeekdaySaturdayCheckBox : 5,
                      self.gui.reOrderWeekdaySundayCheckBox : 6,
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

        model = self.gui.tableView.model()
        model.reorder_commits((min_date, max_date),
                              ((min_time, max_time),),
                              weekdays)

    def current_branch_changed(self, new_branch_name):
        """
            When the currentBranchComboBox current index is changed, set the
            current branch of the model to the new branch.
        """
        for branch, model in self._models.items():
            if new_branch_name == branch.name:
                self._model = model
                if self.parent._modifications_shown:
                    self.gui.tableView.setModel(model)
                else:
                    orig_model = model.get_orig_q_git_model()
                    self.gui.tableView.setModel(orig_model)
                self.refresh_checkboxes()
                break

    def merge_clicked(self, check_state):
        """
            When the "merge checkbox" is checked or unchecked, pass on the
            option to the model.
        """
        model = self.gui.tableView.model()
        model.setMerge(check_state == Qt.Checked)

    def apply_filters(self):
        """
            When a "filter checkbox" is checked or unchecked, set the filters on
            the model and reset it.
        """
        table_view = self.gui.tableView
        model = table_view.model()

        filters = []
        for checkbox_name in self._filters_values:
            checkbox = self._filterbox_byname(checkbox_name)

            if checkbox.checkState() == Qt.Checked:
                _filter = self._filter_byname(checkbox_name)
                model.filter_set(checkbox_name, _filter)
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
            table_view.showRow(row)

        if total_filter_score:
            for row in xrange(model.rowCount()):
                score = 0
                for column in self._shown_columns:
                    index = model.index(row, column)
                    score += model.filter_score(index)

                if score < total_filter_score:
                    table_view.hideRow(row)

        table_view.reset()

    def _filterbox_byname(self, name):
        """
        Given a filter name, returns corresponding checkbox object
        """
        return getattr(self.gui, '%sFilterCheckBox' % name)

    def _filter_byname(self, name):
        """
        Given a filter name, returns the filter, or None
        """
        getter = self._filters_values[name]

        if getter:
            return getter()

        return None

    def toggle_modifications(self, show_modifications):
        """
            When the toggleModifications button is pressed, change the displayed
            model.
        """
        if show_modifications:
            self.gui.tableView.setModel(self._model)
        else:
            # if the displayed model is the editable model
            orig_model = self._model.get_orig_q_git_model()
            self.gui.tableView.setModel(orig_model)

    def show_progress_bar(self):
        """
            Shows the progress bar representing the progress of the writing
            process.
        """
        self.gui.progressBar.show()
        self.gui.applyButton.setDisabled(True)
        self.gui.cancelButton.setDisabled(True)

    def update_progress_bar(self, value):
        """
            Updates the progress bar with a value.

            :param value:
                Progression of the write process, between 0 and 100
        """
        self.gui.progressBar.setValue(value)

    def hide_progress_bar(self):
        """
            Hide the progress bar representing the progress of the writing
            process.
        """
        self.gui.progressBar.hide()
        self.gui.applyButton.setEnabled(True)
        self.gui.cancelButton.setEnabled(True)
