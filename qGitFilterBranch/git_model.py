from PyQt4.QtCore import QModelIndex, Qt, QVariant, QAbstractTableModel
from time import struct_time, strftime
from git import Repo

AVAILABLE = {'actor':'Actor', 'author':'Author',
             'authored_date':'Authored Date', 'committed_date':'Committed Date',
             'committer':'Committer', 'count':'Count', 'diff':'Diff',
             'diffs':'Diffs', 'find_all':'Find All', 'id':'Id',
             'id_abbrev':'Id Abbrev', 'lazy_properties':'Lazy Properties',
             'list_from_string':'List From String', 'message':'Message',
             'parents':'Parents', 'repo':'Repo', 'stats':'Stats',
             'summary':'Summary', 'tree':'Tree'}

class GitModel(QAbstractTableModel):

    def __init__(self):
        QAbstractTableModel.__init__(self, None)
        #XXX self.dirty can be removed safely if not used to consolidate model
        #    data
        self._repo = Repo(".")
        self._dirty = False
        self._columns = []
        self.populate()

    def populate(self):
        self._commits = []
        for commit in self._repo.commits(max_count=self._repo.commit_count()):
            self._commits.append(commit)

        self.reset()

    def parent(self, index):
        #returns the parent of the model item with the given index.
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        return len(self._commits)

    def columnCount(self, parent=QModelIndex()):
        return len(self._columns)

    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < len(self._commits)):
            return QVariant()

        commit = self._commits[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            value = eval("commit."+self._columns[column])
            if isinstance(value, struct_time):
                return QVariant(strftime("%d/%m/%Y %H:%M:%S %Z", value))
            return QVariant(str(value))
        elif role == Qt.EditRole:
            return commit

        return QVariant()

    def setColumns(self, list):
        self._columns = []
        for item in list:
            if item in AVAILABLE:
                self._columns.append(item)


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return QVariant(int(Qt.AlignLeft|Qt.AlignVCenter))
            return QVariant(int(Qt.AlignRight|Qt.AlignVCenter))

        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            return QVariant(AVAILABLE[self._columns[section]])

        return QVariant(int(section + 1))

    def setData(self, index, value, role=Qt.EditRole):
        #PyQt4.QtCore.Qt.EditRole
#        if index.isValid() and 0 <= index.row() < len(self.testers):
#            tester = self.testers[index.row()]
#            column = index.column()
#            if column == 0:
#                tester.set_name(value.toString())
#            self.dirty = True
#            #emit dataChanged
#            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"),
#                      index, index)
#            return True
        return False


    def insertRows(self, position, rows=1, index=QModelIndex()):
        print "Inserting rows"

    def removeRows(self, position, rows=1, index=QModelIndex()):
        print "Removing rows"
        return True


