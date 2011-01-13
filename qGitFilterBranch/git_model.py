from time import struct_time
from datetime import datetime, tzinfo, timedelta

from sys import exit
try:
    from git import Repo
except:
    print """Couldn't import git. You might want to install GitPython from:
    http://pypi.python.org/pypi/GitPython/"""
    exit(1)
try:
    from git import __version__
    str_maj, str_min, str_rev = __version__.split(".")
    maj, min, rev = int(str_maj), int(str_min), int(str_rev)
    if  maj < 0 or (maj == 0 and min < 3) or \
        (maj == 0 and min == 3 and rev < 1):
        raise Exception()
except:
    print "This project needs GitPython (>=0.3.1)."
    exit(1)

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

ENV_FIELDS = {'author_name'     : 'GIT_AUTHOR_NAME',
              'author_email'    : 'GIT_AUTHOR_EMAIL',
              'authored_date'   : 'GIT_AUTHOR_DATE',
              'committer_name'  : 'GIT_COMMITTER_NAME',
              'committer_email' : 'GIT_COMMITTER_EMAIL',
              'committer_date'  : 'GIT_COMMITTER_DATE' }


def add_assign(env_filter, field, value):
    env_filter += "export " + ENV_FIELDS[field] + ";\n"
    env_filter += ENV_FIELDS[field] + "='%s'" % value + ";\n"
    return env_filter


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
            elif field == "message":
                value = commit.message.rstrip()
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
            self.set_field_data(commit, field_name, value)

            if self._merge:
                if field_name == "committed_date":
                    self.set_field_data(commit, "authored_date", value)
                elif field_name == "authored_date":
                    self.set_field_data(commit, "committed_date", value)
                elif field_name == "author":
                    self.set_field_data(commit, "committer", value)
                elif field_name == "committer":
                    self.set_field_data(commit, "author", value)

            self.dirty = True

    def set_field_data(self, commit, field, value):
        if commit not in self._modified:
            self._modified[commit] = {}
        self._modified[commit][field] = value

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
        env_filter = ""
        commit_filter = ""

        for commit in self._modified:
            hexsha = commit.hexsha
            env_header = "if [ \"\$GIT_COMMIT\" = '%s' ]\nthen\n" % hexsha
            commit_header = str(env_header)

            env_content = ""
            commit_content = ""

            for field in self._modified[commit]:
                if field in ACTOR_FIELDS:
                    name, email = self._modified[commit][field]
                    if field == "author":
                        env_content = add_assign(env_content,
                                                 "author_name", name)
                        env_content = add_assign(env_content,
                                                 "author_email", email)
                    elif field == "committer":
                        env_content = add_assign(env_content,
                                                 "committer_name", name)
                        env_content = add_assign(env_content,
                                                 "committer_email", email)
                elif field == "message":
                    value = self._modified[commit][field]
                    commit_content += "echo '%s' > ../message\n" % value
                else:
                    value = self._modified[commit][field]
                    export_list += "export " + ENV_FIELDS[field] + ";"
                    set_list += ENV_FIELDS[field] + "='%s'" % value

            if env_content:
                env_filter += env_header + env_content +"fi\n"

            if commit_content:
                commit_filter += commit_header + commit_content + "fi\n"

        options = ""
        if env_filter:
            options += '--env-filter "%s" ' % env_filter
        if commit_filter:
            commit_filter += 'git commit-tree \\"\$@\\"\n'
            options += '--commit-filter "%s" ' % commit_filter

        if options:
            oldest_commit_parent = ""
            command = "git filter-branch " + options + oldest_commit_parent
            print command
