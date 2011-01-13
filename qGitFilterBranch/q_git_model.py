
from PyQt4.QtCore import QModelIndex, Qt, QVariant, QAbstractTableModel, SIGNAL
from PyQt4.QtGui import QColor
from time import struct_time, strftime
from qGitFilter.git_model import GitModel, NAMES, TEXT_FIELDS, TIME_FIELDS, NOT_EDITABLE_FIELDS, ACTOR_FIELDS
from datetime import datetime

class QGitModel(QAbstractTableModel):

    def __init__(self):
        QAbstractTableModel.__init__(self, None)
        self.git_model = GitModel()
        self.populate()
        self._filters = {}

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
                return QVariant(_datetime.strftime("%d/%m/%Y %H:%M:%S %Z"))
            elif field_name == "message":
                return QVariant(value.split("\n")[0])
            elif field_name in ACTOR_FIELDS:
                name, email = value
                return QVariant("%s <%s>" % (name, email))
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
            if self.filter_match(index):
                return QVariant(QColor(Qt.red))

        return QVariant()

    def filter_set(self, filter, value):
        self._filters[filter] = value

    def filter_unset(self, filter):
        if filter in self._filters:
            self._filters.pop(filter)

    def filter_match(self, index):
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
