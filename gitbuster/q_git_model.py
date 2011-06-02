# q_git_model.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from PyQt4.QtCore import QAbstractTableModel, QDateTime, QModelIndex, \
    QVariant, Qt, QMimeData, QDataStream, QByteArray, QIODevice, QString
from PyQt4.QtGui import QColor
from datetime import datetime
from gfbi_core import ACTOR_FIELDS, NAMES, TEXT_FIELDS, TIME_FIELDS
from gfbi_core.git_model import GitModel


class QGitModel(QAbstractTableModel):

    def __init__(self, directory=".",  model=None, fake_branch_name="",
                 parent=None, remote_ref=None):
        """
            Initializes the git model with the repository root directory.

            Here, we allow the QGitEditableModel to set the GitModel used.
            We do that in order to reduce the number of GitModel instanciated.

            :param directory:
                Root directory of the git repository.

            :param model:
                As given by QGitEditableModel.get_model().get_orig_model().

        """
        QAbstractTableModel.__init__(self, parent)
        if not model:
            self.git_model = GitModel(directory=directory,
                                      remote_ref=remote_ref)
        else:
            self.git_model = model
        self._filters = {}
        self._enabled_options = []
        self._directory = directory
        self._parent = parent

    def populate(self):
        """
            Populates the git model, see git_model.GitModel.populate for more
            infos. Moreover, it counts the number of filters that should be
            applied.
        """
        self.git_model.populate()
        self.reset()

    def parent(self, index):
        #returns the parent of the model item with the given index.
        return QModelIndex()

    def data(self, index, role):
        """
            Returns the data of the model.
        """
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return QVariant()

        column = index.column()
        field_name = self.git_model.get_columns()[column]

        if role == Qt.DisplayRole:
            return self._data_display(index, field_name)
        elif role == Qt.EditRole:
            return self._data_edit(index, field_name)
        elif role == Qt.BackgroundColorRole:
            return self._data_background(index, field_name)
        elif role == Qt.ForegroundRole:
            return self._data_foreground(index, field_name)
        elif role == Qt.ToolTipRole:
            return self._data_tooltip(index, field_name)

        return QVariant()

    def _data_display(self, index, field_name):
        value = self.git_model.data(index)
        if field_name in TIME_FIELDS:
            _tmstmp, _tz = value
            _datetime = datetime.fromtimestamp(_tmstmp).replace(tzinfo=_tz)
            if "display_weekday" in self._enabled_options:
                date_format = "%d/%m/%Y %H:%M:%S (%a)"
            else:
                date_format = "%d/%m/%Y %H:%M:%S"
            return QVariant(_datetime.strftime(date_format))
        elif field_name == "message":
            return QVariant(value.split("\n")[0])
        elif field_name == "hexsha":
            return QVariant(value[:7])

        return QVariant(value)

    def _data_edit(self, index, field_name):
        value = self.git_model.data(index)
        if field_name == "message":
            return QVariant(value)
        elif field_name in TIME_FIELDS or field_name in ("parents", "tree"):
            return value
        return self._data_display(index, field_name)

    def _data_background(self, index, field_name):
        commits = self.git_model.get_commits()
        commit = commits[index.row()]

        if self.git_model.is_commit_pushed(commit):
            return QVariant(QColor(Qt.lightGray))

    def _data_foreground(self, index, field_name):
        if "filters" in self._enabled_options and self.filter_score(index):
            return QVariant(QColor(Qt.red))
        return QVariant()

    def _data_tooltip(self, index, field_name):
        value = self.git_model.data(index)
        if field_name == "hexsha":
            return QVariant(str(value))
        elif field_name in TIME_FIELDS:
            _tmstmp, _tz = value
            _datetime = datetime.fromtimestamp(_tmstmp).replace(tzinfo=_tz)
            if "display_weekday" in self._enabled_options:
                date_format = "%Y-%m-%d %H:%M:%S %Z (%a)"
            else:
                date_format = "%Y-%m-%d %H:%M:%S %Z"
            return QVariant(_datetime.strftime(date_format))
        elif field_name == "message":
            return QVariant(value)

    def filter_set(self, model_filter, value):
        """
            Activates a filter/sets a filter value.

            :param model_filter:
                The filter to be set.
            :param value:
                The value of the filter.
        """
        self._filters[model_filter] = value

    def filter_unset(self, model_filter):
        """
            Deactivates a filter.

            :param model_filter:
                The filter to be deactivated.
        """
        if model_filter in self._filters:
            self._filters.pop(model_filter)

    def enable_option(self, option):
        """
            Enables a display option.

            :param option:
                The option to enable.
        """
        if option not in self._enabled_options:
            self._enabled_options.append(option)

    def disable_option(self, option):
        """
            Disables a display option.

            :param option:
                The option to disable.
        """
        if option in self._enabled_options:
            self._enabled_options.pop(self._enabled_options.index(option))

    def is_enabled(self, option):
        """
            Return True if the display option is enabled.
        """
        return option in self._enabled_options

    def date_match(self, item_date):
        """
            Returns True if item_date matches the date filters.

            :param item_date:
                The date that will be evaluated.
        """
        filters = self._filters

        filter_after_date = None
        filter_before_date = None

        if "afterDate" in filters:
            filter_after_date = filters["afterDate"]
        if "beforeDate" in filters:
            filter_before_date = filters["beforeDate"]

        if filter_after_date and filter_before_date:
            if filter_after_date < item_date < filter_before_date:
                return 1
        elif (filter_after_date and filter_after_date < item_date):
            return 1
        elif (filter_before_date and
              filter_before_date > item_date):
            return 1

        return 0

    def weekday_match(self, item_weekday):
        """
            Returns True if item_weekday matches the weekday filters.

            :param item_weekday:
                The weekday that will be evaluated.
        """
        filters = self._filters

        filter_after_weekday = None
        filter_before_weekday = None

        if "afterWeekday" in filters:
            filter_after_weekday = filters["afterWeekday"] + 1
        if "beforeWeekday" in filters:
            filter_before_weekday = filters["beforeWeekday"] + 1

        if filter_after_weekday and filter_before_weekday:
            if filter_after_weekday < item_weekday < filter_before_weekday:
                return 1
        elif (filter_after_weekday and filter_after_weekday < item_weekday):
            return 1
        elif (filter_before_weekday and
              filter_before_weekday > item_weekday):
            return 1

        return 0

    def time_match(self, item_time):
        """
            Returns True if item_time matches the time filters.

            :param item_time:
                The time that will be evaluated.
        """
        filters = self._filters

        filter_after_hour = None
        filter_before_hour = None

        if "afterHour" in filters:
            filter_after_hour = filters["afterHour"]
        if "beforeHour" in filters:
            filter_before_hour = filters["beforeHour"]

        if filter_after_hour and filter_before_hour:
            if filter_after_hour < item_time < filter_before_hour:
                return 1
        elif (filter_after_hour and filter_after_hour < item_time):
            return 1
        elif (filter_before_hour and
              filter_before_hour > item_time):
            return 1

        return 0

    def filter_score(self, index):
        """
            Returns the number of filters matching the given index.

            :param index:
                The index of the item that will be checked against the filters.
        """
        column = index.column()
        field_name = self.git_model.get_columns()[column]
        filters = self._filters

        if field_name in TIME_FIELDS:
            filters = self._filters
            timestamp, tz = self.git_model.data(index)
            _q_datetime = QDateTime()
            _q_datetime.setTime_t(timestamp)

            item_date = _q_datetime.date()
            item_weekday = item_date.dayOfWeek()
            item_time = _q_datetime.time()

            date_time_filters = ("afterWeekday", "beforeWeekday",
                                 "beforeDate", "afterDate",
                                 "beforeHour", "afterHour")
            has_date_time_filter = False
            for model_filter in filters:
                if model_filter in date_time_filters:
                    has_date_time_filter = True

            if not has_date_time_filter:
                return 0
            else:
                return self.date_match(item_date) + \
                       self.weekday_match(item_weekday) + \
                       self.time_match(item_time)

        elif field_name in ACTOR_FIELDS:
            if "nameEmail" in filters:
                regexp = filters["nameEmail"]
                value = self.git_model.data(index)
                if regexp.isValid() and regexp.indexIn(value) != -1:
                    return 1

        elif field_name in TEXT_FIELDS:
            if "message" in filters:
                regexp = filters["message"]
                commit_message = self.git_model.data(index)
                if regexp.isValid() and regexp.indexIn(commit_message) != -1:
                    return 1

        elif field_name == "hexsha":
            if "localOnly" in filters:
                commits = self.git_model.get_commits()
                commit = commits[index.row()]
                if not self.git_model.is_commit_pushed(commit):
                    return 1

        return 0

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
            Returns the headers (qt model method).
        """
        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return QVariant(int(Qt.AlignLeft|Qt.AlignVCenter))
            return QVariant(int(Qt.AlignRight|Qt.AlignVCenter))

        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            field_name = self.git_model.get_columns()[section]
            return QVariant(NAMES[field_name])

        return QVariant(int(section + 1))

    def flags(self, index):
        """
            Returns the flags for the given index.
        """
        # XXX varies if editable
        if not index.isValid():
            return Qt.ItemIsEnabled
        elif self.is_first_commit(index):
            # The first commit can't be dragged and dropped
            return QAbstractTableModel.flags(self, index)

        return Qt.ItemFlags(QAbstractTableModel.flags(self, index)|
                            Qt.ItemIsDragEnabled)

    def mimeData(self, indexes):
        mime_data = QMimeData()
        encoded_data = QByteArray()

        stream = QDataStream(encoded_data, QIODevice.WriteOnly)

        ref = self.get_current_branch() or self.get_remote_ref()
        for index in indexes:
            if index.isValid() and index.column() == 0:
                text = QString(ref.name + " ")
                text += QString(str(index.row()))
                stream.writeQString(text)

        mime_data.setData("application/vnd.text.list", encoded_data)
        return mime_data

    # Beyond this point, abandon all hope of seeing anything more than "proxying
    # methods" (for instance, progress() calls git_model.progress())
    def get_git_model(self):
        "See GitModel for more help."
        return self.git_model

    def rowCount(self, parent=QModelIndex()):
        "See GitModel for more help."
        return self.git_model.row_count()

    def columnCount(self, parent=QModelIndex()):
        "See GitModel for more help."
        return self.git_model.column_count()

    def get_branches(self):
        "See GitModel for more help."
        return self.git_model.get_branches()

    def get_current_branch(self):
        "See GitModel for more help."
        return self.git_model.get_current_branch()

    def set_current_branch(self, branch):
        "See GitModel for more help."
        return self.git_model.set_current_branch(branch)

    def get_remote_ref(self):
        "See GitModel for more help."
        return self.git_model.get_remote_ref()

    def reorder_commits(self, dates, time, weekdays):
        "See GitModel for more help."
        self.git_model.reorder_commits(dates, time,
                                       weekdays)
        self.reset()

    def row_of(self, commit):
        "See GitModel for more help."
        return self.git_model.row_of(commit)

    def get_columns(self):
        "See GitModel for more help."
        return self.git_model.get_columns()

    def get_old_branch_name(self):
        "See GitModel for more help."
        return self.git_model.get_old_branch_name()

    def is_first_commit(self, index):
        "See GitModel for more help."
        return self.git_model.is_first_commit(index)
