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
from subprocess import Popen, PIPE
from threading import Thread
from os.path import join
import os
from os import chdir
import fcntl

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
              'committed_date'  : 'GIT_COMMITTER_DATE' }


def add_assign(env_filter, field, value):
    env_filter += "export " + ENV_FIELDS[field] + ";\n"
    env_filter += ENV_FIELDS[field] + "='%s'" % value + ";\n"
    return env_filter


class GitFilterBranchProcess(Thread):

    def __init__(self, parent, args, oldest_commit_modified_parent, log):
        Thread.__init__(self)

        self._args = args
        if oldest_commit_modified_parent == "HEAD":
            self._oldest_commit = "HEAD"
        else:
            self._oldest_commit = oldest_commit_modified_parent + ".."

        self._log = log
        self._parent = parent

        self._output = []
        self._progress = None
        self._finished = False

    def run(self):
        clean_pipe = "|tr '\r' '\n'"
        command = "git filter-branch "
        command += self._args + self._oldest_commit + clean_pipe

        process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)

        # Setting the stdout file descriptor to non blocking.
        fcntl.fcntl(
                process.stdout.fileno(),
                fcntl.F_SETFL,
                fcntl.fcntl(process.stdout.fileno(),
                            fcntl.F_GETFL) | os.O_NONBLOCK,
            )

        while True:
            try:
                line = process.stdout.readline()
            except IOError, e:
                continue

            if not line:
                break

            clean_line = line.replace('\r', '\n')
            self._output.append(clean_line)
            if "Rewrite" in clean_line:
                progress = float(line.split('(')[1].split('/')[0])
                total = float(line.split('/')[1].split(')')[0])
                self._progress = progress/total

        process.wait()
        self._finished = True

        self._errors = process.stderr.readlines()
        if self._log:
            log_file = "./qGitFilterBranch.log"
            handle = open(log_file, "a")
            handle.write("=======================\n")
            handle.write("Operation date :" +
                         datetime.now().strftime("%a %b %d %H:%M:%S %Y") +
                        "\n")
            handle.write("===== Command: ========\n")
            handle.write(command + "\n")
            handle.write("===== git output: =====\n")
            for line in self._output:
                handle.write(line + "\n")
            handle.write("===== git errors: =====\n")
            for line in self._errors:
                handle.write(line + "\n")
            handle.close()

        if self._errors:
            for line in self._errors:
                print line
        else:
            self._parent.erase_modifications()

    def progress(self):
        """
            Returns the progress percentage
        """
        return self._progress

    def output(self):
        """
            Returns the output as a list of lines
        """
        return list(self._output)

    def errors(self):
        """
            Returns the errors as a list of lines
        """
        return list(self._errors)

    def is_finished(self):
        """
            Returns self._finished
        """
        return self._finished


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

    def __init__(self, directory="."):
        self._directory = directory
        self._repo = Repo(directory)
        self._modified = {}
        self._dirty = False
        self._columns = []
        self.populate()
        self._did = False
        self._merge = False
        self._show_modifications = True
        self._git_process = None

    def populate(self, filter_method=None):
        self._commits = []

        for commit in self._repo.iter_commits():
            self._commits.append(commit)

        if filter_method:
            iter = 0
            max_filters = 0
            filtered_commits = {}

            for commit in self._repo.iter_commits():
                for field_index in range(len(self._columns)):
                    index = Index(row=iter, column=field_index)
                    if commit not in filtered_commits:
                        filtered_commits[commit] = 0
                    if filter_method(index):
                        filtered_commits[commit] += 1
                        if filtered_commits[commit] > max_filters:
                            max_filters = filtered_commits[commit]
                iter += 1

            self._commits = []
            for commit in self._repo.iter_commits():
                if filtered_commits[commit] == max_filters:
                    self._commits.append(commit)

    def get_commits(self):
        return self._commits

    def get_modified(self):
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

        if self._show_modifications and self.is_modified(index):
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

        value = eval("commit."+self._columns[column])
        return value

    def toggle_modifications(self):
        if self._show_modifications:
            self._show_modifications = False
        else:
            self._show_modifications = True

    def show_modifications(self):
        return self._show_modifications

    def write(self, log=False):
        env_filter = ""
        commit_filter = ""

        for commit in self._modified:
            hexsha = commit.hexsha
            env_header = "if [ \"\$GIT_COMMIT\" = '%s' ]; then " % hexsha
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
                    message = value.replace('\\', '\\\\')
                    message = message.replace('$', '\\\$')
                    message = message.replace("'", "\\'")
                    message = message.replace('"', '\\\\\\"')
                    message = message.replace('(', '\(')
                    message = message.replace(')', '\)')
                    commit_content += "echo %s > ../message;" % message
                elif field in TIME_FIELDS:
                    _timestamp = self._modified[commit][field]
                    _utc_offset = altz_to_utctz_str(commit.author_tz_offset)
                    _tz = Timezone(_utc_offset)
                    _dt = datetime.fromtimestamp(_timestamp).replace(tzinfo=_tz)
                    value = _dt.strftime("%a %b %d %H:%M:%S %Y %Z")
                    env_content = add_assign(env_content, field, value)

            if env_content:
                env_filter += env_header + env_content +"fi\n"

            if commit_content:
                commit_filter += commit_header + commit_content + "fi;"

        options = ""
        if env_filter:
            options += '--env-filter "%s" ' % env_filter
        if commit_filter:
            commit_filter += 'git commit-tree \\"\$@\\"\n'
            options += '--commit-filter "%s" ' % commit_filter

        if options:
            chdir(self._directory)

            command = 'rm -fr "$(git rev-parse --git-dir)/refs/original/"'
            process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
            process.wait()

            command = 'rm -fr .git-rewrite"'
            process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
            process.wait()

            oldest_commit_parent = self.oldest_modified_commit_parent()

            self._git_process = GitFilterBranchProcess(self, options,
                                                       oldest_commit_parent,
                                                       log)
            self._git_process.start()

    def is_finished_writing(self):
        if self._git_process is not None:
            return self._git_process.is_finished()
        return True

    def progress(self):
        if self._git_process is not None:
            return self._git_process.progress()
        return 0

    def oldest_modified_commit_parent(self):
        if self._commits:
            reverted_list = list(self._commits)
            reverted_list.reverse()

            parent = None
            for commit in reverted_list:
                if commit in self._modified:
                    break
                parent = commit

            if parent:
                return str(parent.hexsha)
            else:
                return "HEAD"

        else:
            return False

    def erase_modifications(self):
        self._modified = {}
