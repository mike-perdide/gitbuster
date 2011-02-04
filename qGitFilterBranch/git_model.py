# git_model.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of qGitFilterBranch and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

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
TEXT_FIELDS = ['message', 'summary']
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
    """
        Thread meant to execute and follow the progress of the git command
        process.
    """

    def __init__(self, parent, args, oldest_commit_modified_parent,
                 log, script):
        """
            Initialization of the GitFilterBranchProcess thread.

            :param parent:
                GitModel object, parent of this thread.
            :param args:
                List of arguments that will be passed on to git filter-branch.
            :param oldest_commit_modified_parent:
                The oldest modified commit's parent.
            :param log:
                If set to True, the git filter-branch command will be logged.
            :param script:
                If set to True, the git filter-branch command will be written in
                a script that can be distributed to other developpers of the
                project.
        """
        Thread.__init__(self)

        self._args = args
        if oldest_commit_modified_parent == "HEAD":
            self._oldest_commit = "HEAD"
        else:
            self._oldest_commit = oldest_commit_modified_parent + ".."

        self._log = log
        self._script = script
        self._parent = parent

        self._output = []
        self._errors = []
        self._progress = None
        self._finished = False


    def run(self):
        """
            Main method of the script. Launches the git command and
            logs/generate scripts if the options are set.
        """
        clean_pipe = "|tr '\r' '\n'"
        command = "git filter-branch "
        command += self._args + self._oldest_commit

        process = Popen(command + clean_pipe, shell=True,
                        stdout=PIPE, stderr=PIPE)

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
                handle.write(line.rstrip() + "\n")
            handle.write("===== git errors: =====\n")
            for line in self._errors:
                handle.write(line + "\n")
            handle.close()

        if self._script:
            # Generate migration script
            handle = open("migration.sh", "w")
            handle.write("#/bin/sh\n# Generated by qGitFilterBranch on " +
                         datetime.now().strftime("%a %b %d %H:%M:%S %Y") +
                         "\n")
            handle.write(command + "\n")
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
    """
        This mimics the qModelIndex, so that we can use it in the
        GitModel.data() method when populating the model.
    """

    def __init__(self, row=0, column=0):
        """
            Initialization of the Index object.

            :param row:
                Row number, integer.

            :param column:
                Column number, integer.
        """
        self._row = row
        self._column = column

    def row(self):
        """
            Returns the row number.
        """
        return self._row

    def column(self):
        """
            Returns the column number.
        """
        return self._column


class Timezone(tzinfo):
    """
        Timezone class used to preserve the timezone information when handling
        the commits information.
    """

    def __init__(self, tz_string):
        """
            Initialize the Timezone object with it's string representation.

            :param tz_string:
                Representation of the offset to UTC of the timezone. (i.e. +0100
                for CET or -0400 for ECT)
        """
        self.tz_string = tz_string

    def utcoffset(self, dt):
        """
            Returns the offset to UTC using the string representation of the
            timezone.

            :return:
                Timedelta object representing the offset to UTC.
        """
        sign = 1 if self.tz_string[0] == '+' else -1
        hour = sign * int(self.tz_string[1:-2])
        min = sign * int(self.tz_string[2:])
        return timedelta(hours=hour, minutes=min)

    def tzname(self, dt):
        """
            Returns the offset to UTC string representation.

            :return:
                Offset to UTC string representation.
        """
        return self.tz_string

    def dst(self, dt):
        """
            Returns a timedelta object representing a whole number of minutes
            with magnitude less than one day.

            :return:
                timedelta(0)
        """
        return timedelta(0)


class GitModel:
    """
        This class represents the list of commits of the current branch of a
        given repository. This class is meant to be Qt-free so that it can be
        used in other ways than qGitFilterBranch.
    """

    def __init__(self, directory="."):
        """
            Initializes the model with the repository root directory.

            :param directory:
                Root directory of the git repository.
        """
        self._directory = directory
        self._repo = Repo(directory)
        self._current_branch = self._repo.active_branch
        self._modified = {}
        self._dirty = False
        self._columns = []
        self.populate()
        self._did = False
        self._merge = False
        self._show_modifications = True
        self._git_process = None

    def populate(self, filter_count=0, filter_score=None):
        """
            Populates the model, by constructing a list of the commits of the
            current branch of the given repository.

            :param filter_count:
                The number of display filters configured.
            :param filter_score:
                The filter method used to determine whether a field matches the
                configured criteria. The return value is 0 if the field doesn't
                match. The return value is 1 or more if the fields matches one
                or more.
        """
        self._commits = []
        self._unpushed = []

        branch_rev = self._current_branch.commit
        if self._current_branch.tracking_branch():
            remote_commits_head = self._current_branch.tracking_branch().commit
        else:
            remote_commits_head = None

        pushed = False
        for commit in self._repo.iter_commits(rev=branch_rev):
            self._commits.append(commit)

            if commit.hexsha == remote_commits_head.hexsha:
                pushed = True
            if not pushed:
                self._unpushed.append(commit)

        if filter_score:
            iter = 0
            filtered_commits = {}

            for commit in self._repo.iter_commits():
                for field_index in range(len(self._columns)):
                    index = Index(row=iter, column=field_index)
                    if commit not in filtered_commits:
                        filtered_commits[commit] = 0
                    filtered_commits[commit] += filter_score(index)
                iter += 1

            self._commits = []
            for commit in self._repo.iter_commits():
                if filtered_commits[commit] >= filter_count:
                    self._commits.append(commit)

    def is_commit_pushed(self, commit):
        """
            Returns True if the commit has been pushed to the remote branch.

            :param commit:
        """
        return not commit in self._unpushed

    def get_branches(self):
        """
            Returns the repository avalaible branches.
        """
        return self._repo.branches

    def get_current_branch(self):
        """
            Returns the model's current branch.
        """
        return self._current_branch

    def set_current_branch(self, branch):
        """
            Sets the model's current branch.

            :param branch:
                The desired branch to modelize.
        """
        self._current_branch = branch

    def get_commits(self):
        """
            Returns the commit list.
        """
        return self._commits

    def get_modified(self):
        """
            Returns the modified values dictionnary.
        """
        return self._modified

    def get_columns(self):
        """
            Returns the selected fields names.
        """
        return self._columns

    def row_count(self):
        """
            Returns the count of commits.
        """
        return len(self._commits)

    def column_count(self):
        """
            Returns the count of selected fields names.
        """
        return len(self._columns)

    def data(self, index):
        """
            This method uses the index row to select the commit and the index
            column to select the field to return.

            :param index:
                The index of the wanted information.

            :return:
                Depending on the index column, one of the commit fields.
        """
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
        """
            Set the merge option, meaning that the committed and authored
            notions are merged. For instance, if the committed date is changed
            in the set_data() method, the authored date will be set with the
            same value.

            :param merge_state:
                Boolean, sets the merge option.
        """
        self._merge = merge_state

    def set_columns(self, list):
        """
            Set the fields that will be returned as columns.

            :param list:
                A list of commit field names.
        """
        self._columns = []
        for item in list:
            if item in NAMES:
                self._columns.append(item)

    def set_data(self, index, value):
        """
            Set the given value to the commit and the field determined by the
            index.

            :param index:
                The index of the commit and the field that should be modified.
            :param value:
                The value that will be assigned.
        """
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
        """
            This method is used in set_data() to assign the given value to the
            given field of the given commit.

            :param commit:
                The commit that will be modified.
            :param field:
                The field that will be modified.
            :param value:
                The value that will be assigned.
        """
        if commit not in self._modified:
            self._modified[commit] = {}
        self._modified[commit][field] = value

    def is_modified(self, index):
        """
            Returns True if the commit field determined by the index has been
            modified (if there is a corresponding entry in the self._modified
            dict).

            :param index:
                Index of the field of the commit.

            :return:
                True if the field of the commit is modified else False.
        """
        commit = self._commits[index.row()]
        column = index.column()
        field_name = self._columns[column]

        if commit in self._modified and field_name in self._modified[commit]:
            return True
        return False

    def original_data(self, index):
        """
            Returns the original data, even if the commit field pointed by the
            index has been modified.

            :param index:
                Index of the field of the commit.

            :return:
                The original value of the field of the commit.
        """
        commit = self._commits[index.row()]
        column = index.column()

        value = eval("commit."+self._columns[column])
        return value

    def toggle_modifications(self):
        """
            Toggle the show/hide modifications option. If unset, data() will act
            like original_data(). If not, it will return the modified value of
            the field of the commit, if it has been modified.
        """
        if self._show_modifications:
            self._show_modifications = False
        else:
            self._show_modifications = True

    def show_modifications(self):
        """
            Returns the current toggleModifications option state.
        """
        return self._show_modifications

    def write(self, log, script):
        """
            Start the git filter-branch command and therefore write the
            modifications stored in _modified.

            :param log:
                Boolean, set to True to log the git command.
            :param script:
                Boolean, set to True to generate a git filter-branch script that
                can be used by on every checkout of the repository.
        """
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
            # Behold, thee who wanders in this portion of the source code.  What
            # you see here may look like the ramblings of a deranged man. You
            # may partially be right, but here me out before lighting the pyre.
            # The command given to the commit-filter argument is to be
            # interpreted in a bash environment. Therefore, if we want to use
            # newlines, we need to use ' quotes. BUT, and that's where I find it
            # gets hairy. If we already have single quotes in the commit
            # message, we need to escape it. Since escaping single quotes in
            # single quotes string doesn't work, we need to: close the single
            # quote string, open double quotes string, escape the single quote,
            # close the double quotes string, and then open a new single quote
            # string for the rest of the commit message.
                    value = self._modified[commit][field]
                    message = value.replace('\\', '\\\\')
                    message = message.replace('$', '\\\$')
                    # Backslash overflow !
                    message = message.replace('"', '\\\\\\"')
                    message = message.replace("'", "'\"\\\\\\'\"'")
                    message = message.replace('(', '\(')
                    message = message.replace(')', '\)')
                    commit_content += "echo '%s' > ../message;" % message
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
                                                       log, script)
            self._git_process.start()

    def is_finished_writing(self):
        """
            Returns False if the git command process isn't finished else True.
        """
        if self._git_process is not None:
            return self._git_process.is_finished()
        return True

    def progress(self):
        """
            Returns the git command process progress.
        """
        if self._git_process is not None:
            return self._git_process.progress()
        return 0

    def oldest_modified_commit_parent(self):
        """
            Returns a string with the oldest modified commit's parent hexsha or
            HEAD if the oldest modified commit is HEAD.

            :return:
                The hexsha of the last modified commit's parent.
        """
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
        """
            Erase all modifications: set _modified to {}.
        """
        self._modified = {}
