# filter_main_class.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from PyQt4.QtCore import QDateTime, QObject, Qt, SIGNAL, QRegExp
from PyQt4.QtGui import QApplication, QCheckBox, QSizePolicy, QSpacerItem

from gitbuster.q_git_delegate import QGitDelegate
from gitbuster.q_git_model import NAMES
from gitbuster.util import _connect_button

from datetime import datetime


AVAILABLE_CHOICES = ['hexsha',
                     'authored_date', 'committed_date',
                     'author_name', 'author_email',
                     'committer_name', 'committer_email',
                     'message']
PRE_CHOICE = ['hexsha', 'authored_date', 'author_name', 'message']
AVAILABLE_OPTIONS = {'display_weekday': 'Weekday'}

_FILTER_WIDGETS = {
"currentIndexChanged (int)": """
    afterWeekdayFilterComboBox
    beforeWeekdayFilterComboBox""",
"timeChanged (const QTime&)": """
    afterHourFilterTimeEdit
    beforeHourFilterTimeEdit""",
"dateChanged (const QDate&)": """
    afterDateFilterDateEdit
    beforeDateFilterDateEdit""",
"returnPressed()": """
    nameEmailFilterLineEdit
    messageFilterLineEdit""",
"stateChanged(int)": """
    afterWeekdayFilterCheckBox
    beforeWeekdayFilterCheckBox
    afterHourFilterCheckBox
    beforeHourFilterCheckBox
    afterDateFilterCheckBox
    beforeDateFilterCheckBox
    nameEmailFilterCheckBox
    messageFilterCheckBox
    localOnlyFilterCheckBox""",
        }

#afterHour, beforeHour etc
_DATE_FILTERS = frozenset([frozenset(["after%s" % word, "before%s" % word])
    for word in "Hour Date Weekday".split()
    ])

_SIMPLE_FILTERS = frozenset(["nameEmail", "message", "localOnly"])


class FilterMainClass():

    def __init__(self, parent, directory, models):
        self.parent = parent
        self._models = None

        self.gui = self.parent._ui
        self._filters_values = {
            "afterWeekday": self.gui.afterWeekdayFilterComboBox.currentIndex,
            "beforeWeekday": self.gui.beforeWeekdayFilterComboBox.currentIndex,
            "beforeDate": self.gui.beforeDateFilterDateEdit.date,
            "afterDate": self.gui.afterDateFilterDateEdit.date,
            "beforeHour": self.gui.beforeHourFilterTimeEdit.time,
            "afterHour": self.gui.afterHourFilterTimeEdit.time,
            "message": self.gui.messageFilterLineEdit.text,
            "nameEmail": self.gui.nameEmailFilterLineEdit.text,
            "localOnly": None
        }

        self._shown_columns = []
        self._checkboxes = {}
        self._model = None

        self.reset_interface(models)

        self.connect_slots()

        # Initialize the dateEdit widgets
        dateedits = [self.gui.beforeDateFilterDateEdit,
                     self.gui.afterDateFilterDateEdit,
                     self.gui.reOrderMinDateEdit,
                     self.gui.reOrderMaxDateEdit]

        for dateedit in dateedits:
            dateedit.setDateTime(QDateTime.currentDateTime())

    def reset_interface(self, models):
        """
            Resets the filter tab (usually after a directory change).
        """
        current_branch = self.parent.current_branch

        self._models = models
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

    def add_new_model(self, model):
        """
            Add a new model to this tab.
        """
        branch = model.get_current_branch() or model.get_remote_ref()
        self.gui.currentBranchComboBox.addItem("%s" % branch.name)

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

        # Change current branch when the currentBranchComboBox current index is
        # changed.
        connect(self.gui.currentBranchComboBox,
                SIGNAL("currentIndexChanged(const QString&)"),
                self.current_branch_changed)

        # Apply filters when filter edit widgets are edited or when the filter
        # checkboxes are ticked.
        for signal, widgets in _FILTER_WIDGETS.iteritems():
            for widgetname in widgets.split():
                widget = getattr(self.gui, widgetname)
                connect(widget, SIGNAL(signal), self.apply_filters)

        # Connecting the re-order push button to the re-order method.
        _connect_button(self.gui.reOrderPushButton, self.reorder_pushed)

    def create_checkboxes(self):
        """
            Creates the checkboxes used to determine what columns are to be
            displayed or what options should be set to the model (i.e. should
            we display the weekday, etc.)
        """
        # Hiding every columns (even those not listed in AVAILABLE_CHOICES)
        for column, field in enumerate(self._model.get_columns()):
            self.gui.tableView.hideColumn(column)

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
            view's displayed columns model so that only the selected columns
            are displayed.
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

        checkboxes = {self.gui.reOrderWeekdayMondayCheckBox: 0,
                      self.gui.reOrderWeekdayTuesdayCheckBox: 1,
                      self.gui.reOrderWeekdayWednesdayCheckBox: 2,
                      self.gui.reOrderWeekdayThursdayCheckBox: 3,
                      self.gui.reOrderWeekdayFridayCheckBox: 4,
                      self.gui.reOrderWeekdaySaturdayCheckBox: 5,
                      self.gui.reOrderWeekdaySundayCheckBox: 6,
        }
        weekdays = []
        for checkbox in checkboxes:
            if checkbox.checkState() == Qt.Checked:
                weekdays.append(checkboxes[checkbox])

        if not weekdays:
            weekdays = tuple(xrange(7))

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
            When a "filter checkbox" is checked or unchecked, set the filters
            on the model and reset it.
        """
        table_view = self.gui.tableView
        model = table_view.model()

        filters = set()
        for checkbox_name in self._filters_values:
            checkbox = self._filterbox_byname(checkbox_name)

            if checkbox.checkState() == Qt.Checked:
                _filter = self._filter_byname(checkbox_name)
                if checkbox_name in ("message", "nameEmail"):
                    _filter = QRegExp(_filter)
                model.filter_set(checkbox_name, _filter)
                filters.add(checkbox_name)
            else:
                model.filter_unset(checkbox_name)

        #help for reading following code:
        # '&' provides with the intersection between 2 sets
        # then a sum of non empty intersections is computed
        total_filter_score = sum(1 for group in _DATE_FILTERS
            if group & filters)\
            +len(filters & _SIMPLE_FILTERS)

        for row in xrange(model.rowCount()):
            table_view.showRow(row)

        if total_filter_score:
            for row in xrange(model.rowCount()):
                score = 0
                for column in self._shown_columns:
                    index = model.createIndex(row, column)
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

    def hide_fake_models(self):
        """
            Hide all the fake models.
        """
        if [True for model in self._models.values() if model.is_fake_model()]:
            comboBox = self.gui.currentBranchComboBox
            previously_selected_index = comboBox.currentIndex()
            comboBox.clear()
            for branch, model in self._models.items():
                if not model.is_fake_model():
                    comboBox.addItem("%s" % branch.name)

            if self._model.is_fake_model():
                comboBox.setCurrentIndex(0)
            else:
                comboBox.setCurrentIndex(previously_selected_index)

    def show_fake_models(self):
        """
            Show all fake models.
        """
        if [True for model in self._models.values() if model.is_fake_model()]:
            comboBox = self.gui.currentBranchComboBox
            previously_selected_index = comboBox.currentIndex()
            comboBox.clear()
            for branch, model in self._models.items():
                comboBox.addItem("%s" % branch.name)
            comboBox.setCurrentIndex(previously_selected_index)

    def toggle_modifications(self, show_modifications):
        """
            When the toggleModifications button is pressed, change the
            displayed model.
        """
        if show_modifications:
            self.gui.tableView.setModel(self._model)
            self.show_fake_models()
        else:
            self.hide_fake_models()
            # if the displayed model is not a fake model nor a QGitModel
            if hasattr(self._model, 'get_orig_q_git_model'):
                orig_model = self._model.get_orig_q_git_model()
                self.gui.tableView.setModel(orig_model)
