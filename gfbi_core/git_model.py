# git_model.py
# Copyright (C) 2011 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gfbi_core and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from time import mktime
from datetime import datetime

import sys
try:
    from git import Repo
except:
    print """Couldn't import git. You might want to install GitPython from:
    http://pypi.python.org/pypi/GitPython/"""
    sys.exit(1)
try:
    from git import __version__
    str_maj, str_min, str_rev = __version__.split(".")
    _maj, _min, _rev = int(str_maj), int(str_min), int(str_rev)
    if  _maj < 0 or (_maj == 0 and _min < 3) or \
        (_maj == 0 and _min == 3 and _rev < 1):
        raise Exception()
except:
    print "This project needs GitPython (>=0.3.1)."
    sys.exit(1)

from git.objects.util import altz_to_utctz_str
from subprocess import Popen, PIPE
from os import chdir
from random import random
#from random import uniform

from gfbi_core.util import Timezone, Index
from gfbi_core.git_filter_branch_process import git_filter_branch_process
from gfbi_core.non_continuous_timelapse import non_continuous_timelapse

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

class GitModel:
    """
        This class represents the list of commits of the current branch of a
        given repository. This class is meant to be Qt-free so that it can be
        used in other ways than gitbuster.
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

            if remote_commits_head is not None and \
               commit.hexsha == remote_commits_head.hexsha:
                pushed = True
            if not pushed:
                self._unpushed.append(commit)

        if filter_score:
            iterator = 0
            filtered_commits = {}

            for commit in self._repo.iter_commits():
                for field_index in range(len(self._columns)):
                    index = Index(row=iterator, column=field_index)
                    if commit not in filtered_commits:
                        filtered_commits[commit] = 0
                    filtered_commits[commit] += filter_score(index)
                iterator += 1

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

    def set_columns(self, column_list):
        """
            Set the fields that will be returned as columns.

            :param list:
                A list of commit field names.
        """
        self._columns = []
        for item in column_list:
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
            # may partially be right, but ear me out before lighting the pyre.
            # The command given to the commit-filter argument is to be
            # interpreted in a bash environment. Therefore, if we want to use
            # newlines, we need to use ' quotes. BUT, and that's where I find it
            # gets hairy, if we already have single quotes in the commit
            # message, we need to escape it. Since escaping single quotes in
            # single quotes string doesn't work, we need to: close the single
            # quote string, open double quotes string, escape the single quote,
            # close the double quotes string, and then open a new single quote
            # string for the rest of the commit message. Now light the pyre.
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
                return None

        else:
            return False

    def erase_modifications(self):
        """
            Erase all modifications: set _modified to {}.
        """
        self._modified = {}

    def reorder_commits(self, dates, times, weekdays):
        """
            This method reorders the commits given specified timelapses and
            weekdays.
        """
        timelapse = non_continuous_timelapse(dates, times, weekdays)

        ## Random method
        #delta = truc_truc.get_total_seconds() / (how_many_commits + 1)
        #max_error = delta / 2
        #
        #time_cursor = 0
        #for commit in xrange(how_many_commits):
        #    time_cursor += delta
        #    # The next lines sets the commit_time to time_cursor, plus or less
        #    # an error
        #    new_commit_time = time_cursor + int((random() * 2 - 1) * max_error)

        # Uniform method
        total_seconds = timelapse.get_total_seconds()
        distribution = [int(random() * total_seconds)
                        for commit in xrange(len(self._commits))]
        distribution.sort()

        index = 0
        for commit in self._commits:
            this_distribution = distribution[index]
            new_commit_time = timelapse.datetime_from_seconds(this_distribution)
            self.set_field_data(commit, "authored_date",
                                int(mktime(new_commit_time.timetuple())))
            self.set_field_data(commit, "committed_date",
                                int(mktime(new_commit_time.timetuple())))

            index += 1
