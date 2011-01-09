from time import struct_time
from git import Repo

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

class Index:

    def __init__(self, row=0, column=0):
        self.row = row
        self.column = column

    def row(self):
        return self.row

    def column(self):
        return self.column


class GitModel:

    def __init__(self):
        self._repo = Repo(".")
        self._modified = {}
        self._dirty = False
        self._columns = []
        self.populate()

    def populate(self):
        self._commits = []
        for commit in self._repo.commits(max_count=self._repo.commit_count()):
            self._commits.append(commit)

    def get_commits(self):
        return self._commits

    def get_modifed(self):
        return self._modified

    def get_columns(self):
        return self._columns

    def row_count(self):
        return len(self._commits)

    def column_count(self):
        return len(self._columns)

    def data(self, index):
        commit = self._commits[index.row()]
        column = index.column()

        value = eval("commit."+self._columns[column])
        return value

    def set_columns(self, list):
        self._columns = []
        for item in list:
            if item in AVAILABLE:
                self._columns.append(item)

    def set_data(self, index, value):
        commit = self._commits[index.row()]
        column = index.column()
        field_name = self._columns[column]

        if commit not in self._modified:
            self._modified[commit] = {}
        
        if field_name in TEXT_FIELDS: 
            self._modified[commit][field_name] = value
        elif field_name in TIME_FIELDS:
            time_value = struct_time(value)
            self._modified[commit][field_name] = time_value
        else:
            return
        self.dirty = True

