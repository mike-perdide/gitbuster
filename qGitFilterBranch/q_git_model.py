
from PyQt4.QtCore import QModelIndex, Qt, QVariant, QAbstractTableModel, SIGNAL, QDateTime
from PyQt4.QtGui import QColor
from qGitFilter.git_model import GitModel, NAMES, TEXT_FIELDS, TIME_FIELDS, NOT_EDITABLE_FIELDS, ACTOR_FIELDS
from datetime import datetime

class QGitModel(QAbstractTableModel):

    def __init__(self):
        QAbstractTableModel.__init__(self, None)
        self.git_model = GitModel()
        self.populate()
        self._filters = {}
        self._enabled_options = []

    def get_git_model(self):
        return self.git_model

    def populate(self):
        self.git_model.populate()
        self.reset()

    def parent(self, index):
        #returns the parent of the model item with the given index.
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        return self.git_model.row_count()

    def columnCount(self, parent=QModelIndex()):
        return self.git_model.column_count()

    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return QVariant()

        commits = self.git_model.get_commits()
        commit = commits[index.row()]
        column = index.column()
        field_name = self.git_model.get_columns()[column]

        if role == Qt.DisplayRole:
            value = self.git_model.data(index)
            if field_name in TIME_FIELDS:
                _tmstmp, _tz = value
                _datetime = datetime.fromtimestamp(_tmstmp).replace(tzinfo=_tz)
                if "display_weekday" in self._enabled_options:
                    date_format = "%Y-%m-%d %H:%M:%S (%a)"
                else:
                    date_format = "%Y-%m-%d %H:%M:%S"
                return QVariant(_datetime.strftime(date_format))
            elif field_name == "message":
                return QVariant(value.split("\n")[0])
            elif field_name in ACTOR_FIELDS:
                name, email = value
                if "display_email" in self._enabled_options:
                    return QVariant("%s <%s>" % (name, email))
                else:
                    return QVariant("%s" % name)
            elif field_name == "hexsha":
                return QVariant(str(value)[:7])
            return QVariant(str(value))
        elif role == Qt.EditRole:
            value = self.git_model.data(index)
            if field_name == "message":
                return QVariant(value)
            elif field_name in TIME_FIELDS:
                return value
            return self.data(index, Qt.DisplayRole)
        elif role == Qt.BackgroundColorRole:
            modified = self.git_model.get_modifed()
            if commit in modified and field_name in modified[commit]:
                return QVariant(QColor(Qt.yellow))
        elif role == Qt.ForegroundRole:
            if "filters" in self._enabled_options and self.filter_match(index):
                return QVariant(QColor(Qt.red))
        elif role == Qt.ToolTipRole:
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

        return QVariant()

    def filter_set(self, filter, value):
        self._filters[filter] = value

    def filter_unset(self, filter):
        if filter in self._filters:
            self._filters.pop(filter)

    def enable_option(self, option):
        if option not in self._enabled_options:
            self._enabled_options.append(option)

    def disable_option(self, option):
        if option in self._enabled_options:
            self._enabled_options.pop(self._enabled_options.index(option))

    def is_enabled(self, option):
        return option in self._enabled_options

    def date_match(self, index, item_date):
        filters = self._filters

        filter_after_date = None
        filter_before_date = None

        if "afterDate" in filters:
            filter_after_date = filters["afterDate"]
        if "beforeDate" in filters:
            filter_before_date = filters["beforeDate"]

        if not (filter_before_date or filter_after_date):
            return True
        elif filter_after_date and filter_before_date:
            if filter_after_date < item_date < filter_before_date:
                return True
        elif (filter_after_date and filter_after_date < item_date):
            return True
        elif (filter_before_date and
              filter_before_date > item_date):
            return True

        return False

    def weekday_match(self, index, item_weekday):
        filters = self._filters

        filter_after_weekday = None
        filter_before_weekday = None

        if "afterWeekday" in filters:
            filter_after_weekday = filters["afterWeekday"] + 1
        if "beforeWeekday" in filters:
            filter_before_weekday = filters["beforeWeekday"] + 1

        if not (filter_after_weekday or filter_before_weekday):
            return True
        elif filter_after_weekday and filter_before_weekday:
            if filter_after_weekday < item_weekday < filter_before_weekday:
                return True
        elif (filter_after_weekday and filter_after_weekday < item_weekday):
            return True
        elif (filter_before_weekday and
              filter_before_weekday > item_weekday):
            return True

        return False

    def time_match(self, index, item_time):
        filters = self._filters

        filter_after_hour = None
        filter_before_hour = None

        if "afterHour" in filters:
            filter_after_hour = filters["afterHour"]
        if "beforeHour" in filters:
            filter_before_hour = filters["beforeHour"]

        if not (filter_after_hour or filter_before_hour):
            return True
        elif filter_after_hour and filter_before_hour:
            if filter_after_hour < item_time < filter_before_hour:
                return True
        elif (filter_after_hour and filter_after_hour < item_time):
            return True
        elif (filter_before_hour and
              filter_before_hour > item_time):
            return True

        return False

    def filter_match(self, index):
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
            for filter in filters:
                if filter in date_time_filters:
                    has_date_time_filter = True

            if not has_date_time_filter:
                return False
            else:
                return self.date_match(index, item_date) and \
                       self.weekday_match(index, item_weekday) and \
                       self.time_match(index, item_time)

        elif field_name in ACTOR_FIELDS:
            if "nameEmail" in filters:
                match = str(filters["nameEmail"])
                name, email = self.git_model.data(index)
                if match in name or match in email:
                    return True

        elif field_name in TEXT_FIELDS:
            if "commit" in filters:
                match = str(filters["commit"])
                commit_message = self.git_model.data(index)
                if match in commit_message:
                    return True

        return False

    def setColumns(self, list):
        self.git_model.set_columns(list)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
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

    def setMerge(self, merge_state):
        self.git_model.set_merge(merge_state)

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and 0 <= index.row() < self.rowCount():
            self.git_model.set_data(index, value)

            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"),
                      index, index)
            return True
        return False

    def write(self):
        self.git_model.write()

    def insertRows(self, position, rows=1, index=QModelIndex()):
        print "Inserting rows"

    def removeRows(self, position, rows=1, index=QModelIndex()):
        print "Removing rows"
        return True

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled

        column = index.column()
        field_name = self.git_model.get_columns()[column]

        if field_name in NOT_EDITABLE_FIELDS:
            return Qt.ItemFlags(QAbstractTableModel.flags(self, index)|
                                Qt.NoItemFlags)
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index)|
                            Qt.ItemIsEditable)
