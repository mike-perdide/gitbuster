from time import struct_time
from datetime import datetime, tzinfo, timedelta
from git import Repo
from git.objects.util import altz_to_utctz_str

NAMES = {'actor':'Actor', 'author':'Author',
             'authored_date':'Authored Date', 'committed_date':'Committed Date',
             'committer':'Committer', 'count':'Count', 'diff':'Diff',
             'diffs':'Diffs', 'find_all':'Find All', 'hexsha':'Id',
             'lazy_properties':'Lazy Properties',
             'list_from_string':'List From String', 'message':'Message',
             'parents':'Parents', 'repo':'Repo', 'stats':'Stats',
             'summary':'Summary', 'tree':'Tree'}
TEXT_FIELDS = ['hexsha', 'message', 'summary']
ACTOR_FIELDS = ['author', 'committer']
TIME_FIELDS = ['authored_date', 'committed_date']
NOT_EDITABLE_FIELDS = ['hexsha']

class Index:

    def __init__(self, row=0, column=0):
        self._row = row
        self._column = column

    def row(self):
        return self._row

    def column(self):
        return self._column


class Timezone(tzinfo):
    def __init__(self, tz_string):
        self.tz_string = tz_string

    def utcoffset(self, dt):
        sign = 1 if self.tz_string[0] == '+' else -1
        hour = sign * int(self.tz_string[1:-2])
        min = sign * int(self.tz_string[2:])
        return timedelta(hours=hour, minutes=min)

    def tzname(self, dt):
        return self.tz_string

    def dst(self, dt):
        return timedelta(0)

class GitModel:

    def __init__(self):
        self._repo = Repo(".")
        self._modified = {}
        self._dirty = False
        self._columns = []
        self.populate()
        self._did = False
        self._merge = False

    def populate(self):
        self._commits = []
        for commit in self._repo.iter_commits():
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
        field = self._columns[column]

        if self.is_modified(index):
            modified = self._modified[commit]
            if field in TIME_FIELDS:
                if field == 'authored_date':
                    _timestamp = modified[field]
                    _offset = altz_to_utctz_str(commit.author_tz_offset)
                    _tz = Timezone(_offset)
                elif field == 'committed_date':
                    _timestamp = modified[field]
                    _offset = altz_to_utctz_str(commit.committer_tz_offset)
                    _tz = Timezone(_offset)
                value = (_timestamp, _tz)
            else:
                value = modified[field]
        else:
            if field in TIME_FIELDS:
                if field == 'authored_date':
                    _timestamp = commit.authored_date
                    _utc_offset = altz_to_utctz_str(commit.author_tz_offset)
                    _tz = Timezone(_utc_offset)
                elif field == 'committed_date':
                    _timestamp = commit.committed_date
                    _utc_offset = altz_to_utctz_str(commit.committer_tz_offset)
                    _tz = Timezone(_utc_offset)
                value = (_timestamp, _tz)
            elif field in ACTOR_FIELDS:
                actor = eval("commit." + field)
                value = (actor.name, actor.email)
            else:
                value = eval("commit." + field)
        return value

    def set_merge(self, merge_state):
        self._merge = merge_state

    def set_columns(self, list):
        self._columns = []
        for item in list:
            if item in NAMES:
                self._columns.append(item)

    def set_data(self, index, value):
        commit = self._commits[index.row()]
        column = index.column()
        field_name = self._columns[column]

        if field_name in TIME_FIELDS:
            reference, tz = self.data(index)
        else:
            reference = self.data(index)

        if reference != value:
            if commit not in self._modified:
                self._modified[commit] = {}

            self._modified[commit][field_name] = value
            if self._merge:
                if field_name == "committed_date":
                    self._modified[commit]["authored_date"] = value
                elif field_name == "authored_date":
                    self._modified[commit]["committed_date"] = value
                elif field_name == "author":
                    self._modified[commit]["committer"] = value
                elif field_name == "committer":
                    self._modified[commit]["author"] = value

            self.dirty = True

    def is_modified(self, index):
        commit = self._commits[index.row()]
        column = index.column()
        field_name = self._columns[column]

        if commit in self._modified and field_name in self._modified[commit]:
            return True
        return False

    def original_data(self, index):
        commit = self._commits[index.row()]
        column = index.column()
        field_name = self._columns[column]

        value = eval("commit."+self._columns[column])
        return value

    def write(self):
        from pprint import pprint
        pprint(self._modified)

