from PyQt4.QtCore import QModelIndex, Qt, QVariant, QAbstractTableModel
from git import Repo

class GitModel(QAbstractTableModel):

    def __init__(self):
        QAbstractTableModel.__init__(self, None)
        #XXX self.dirty can be removed safely if not used to consolidate model
        #    data
        self._repo = Repo(".")
        self._dirty = False
        self.populate()

    def populate(self):
        self._commits = []
        for commit in self._repo.commits(max_count=self._repo.commit_count()):
            self._commits.append(commit)

        self.reset()

    def parent(self, index):
        #returns the parent of the model item with the given index.
        print "Asking for parent"
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        return len(self._commits)

    def columnCount(self, parent=QModelIndex()):
        #'actor', 'author', 'authored_date', 'committed_date', 'committer',
        #'count', 'diff', 'diffs', 'find_all', 'id', 'id_abbrev',
        #'lazy_properties', 'list_from_string', 'message', 'parents', 'repo',
        #'stats', 'summary', 'tree'

        #id_abbrev, authored_date, committed_date, committer, summary
        return 5

    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < len(self._commits)):
            return QVariant()

        commit = self._commits[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            if column == 0:
                return QVariant(commit.id_abbrev)
            elif column == 1:
                return QVariant(commit.authored_date)
            elif column == 2:
                return QVariant(commit.committed_date)
            elif column == 3:
                return QVariant(commit.committer)
            elif column == 4:
                return QVariant(commit.summary)
        elif role == Qt.EditRole:
            return commit

        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return QVariant(int(Qt.AlignLeft|Qt.AlignVCenter))
            return QVariant(int(Qt.AlignRight|Qt.AlignVCenter))

        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            if section == 0:
                return QVariant("Name")
            elif section == 1:
                return QVariant("Delta")
            elif section == 2:
                return QVariant("Next")

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


