
from PyQt4.QtCore import QModelIndex, Qt, QVariant, QAbstractTableModel, SIGNAL
from PyQt4.QtGui import QColor
from time import struct_time, strftime
from qGitFilter.git_model import GitModel

AVAILABLE = {'actor':'Actor', 'author':'Author',
             'authored_date':'Authored Date', 'committed_date':'Committed Date',
             'committer':'Committer', 'count':'Count', 'diff':'Diff',
             'diffs':'Diffs', 'find_all':'Find All', 'id':'Id',
             'id_abbrev':'Id Abbrev', 'lazy_properties':'Lazy Properties',
             'list_from_string':'List From String', 'message':'Message',
             'parents':'Parents', 'repo':'Repo', 'stats':'Stats',
             'summary':'Summary', 'tree':'Tree'}
TEXT_FIELDS = ['author', 'committer', 'id', 'id_abbrev', 'message', 'summary']
TIME_FIELDS = ['authored_date', 'committed_date']

class QGitModel(QAbstractTableModel):

    def __init__(self):
        QAbstractTableModel.__init__(self, None)
        self.git_model = GitModel()
        self.populate()

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
            if isinstance(value, struct_time):
                return QVariant(strftime("%d/%m/%Y %H:%M:%S %Z", value))
            if field_name == "author" or field_name == "committer":
                return QVariant("%s <%s>" % (value.name, value.email))
            return QVariant(str(value))
        elif role == Qt.EditRole:
            return commit
        elif role == Qt.BackgroundColorRole:
            modified = self.git_model.get_modifed()
            if commit in modified and field_name in modified[commit]:
                return QVariant(QColor(Qt.yellow))

        return QVariant()

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
            return QVariant(AVAILABLE[field_name])

        return QVariant(int(section + 1))

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and 0 <= index.row() < len(self._commits):
            self.git_model.set_data(index, value)

            self.dirty = True
            #emit dataChanged
            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"),
                      index, index)
            return True
        return False


    def insertRows(self, position, rows=1, index=QModelIndex()):
        print "Inserting rows"

    def removeRows(self, position, rows=1, index=QModelIndex()):
        print "Removing rows"
        return True


