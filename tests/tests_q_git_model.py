"""
    This test script aims at testing QGitModel, without any modifications.
"""
from gitbuster.q_git_model import QGitModel
from PyQt4.QtCore import Qt, QModelIndex
from subprocess import Popen, PIPE
import trace
import sys
import time

import os

TEST_DIR = "/tmp/tests_git"
TEST_column_count = 10
TEST_author_name = "Author Groom"
TEST_author_email = "author@groom.com"
TEST_committer_name = "Committer Groom"
TEST_committer_email = "committer@groom.com"

def run_command(command):
    handle = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    handle.wait()
    return handle.stdout.readlines(), handle.stderr.readlines()

def read_commits_from_log():
    stdout, stderr = run_command("git log --pretty='format:%h %s'")
    commits_storage_list = []
    for line in stdout:
        short_hexsha = line.split(" ")[0]
        message = " ".join(line.split(" ")[1:]).strip()

        commits_storage_list.append((short_hexsha, message))

    return commits_storage_list

def set_test_values(dir):
    """
        This will set the global branches, wallace_branch_name,
        wallace_branch_commits, TEST_wallace_branch_model, TEST_master_branch_model.
    """
    global TEST_branches
    global TEST_current_branch_name
    global TEST_wallace_branch_commits
    global TEST_master_branch_commits
    global TEST_wallace_branch_model
    global TEST_master_branch_model
    global TEST_master_branch
    global TEST_wallace_branch
    dummy_model = QGitModel(TEST_DIR)

    branches = dummy_model.get_branches()
    TEST_master_branch = [branch for branch in branches
                          if branch.name == 'master'][0]
    TEST_master_branch_model = QGitModel(TEST_DIR)
    TEST_master_branch_model.set_current_branch(TEST_master_branch)
    TEST_master_branch_model.populate()

    TEST_wallace_branch = [branch for branch in branches
                           if branch.name == 'wallace_branch'][0]
    TEST_wallace_branch_model = QGitModel(TEST_DIR)
    TEST_wallace_branch_model.set_current_branch(TEST_wallace_branch)
    TEST_wallace_branch_model.populate()

    run_command("git checkout master")
    TEST_master_branch_commits = read_commits_from_log()

    run_command("git checkout wallace_branch")
    TEST_wallace_branch_commits = read_commits_from_log()

    stdout, stderr = run_command("git branch")
    TEST_branches = []
    for line in stdout:
        branch_name = line.split(' ')[-1].strip()
        if line[0] == '*':
            TEST_current_branch_name = branch_name
        TEST_branches.append(branch_name)

def setup_tests():
    global TEST_date
    global TEST_time

    run_command("./fake_git_gen.sh")
    TEST_date, TEST_time = time.strftime("%d/%m/%Y %H:%M").split(" ")
    os.chdir(TEST_DIR)
    set_test_values(TEST_DIR)

def check(tested_value, correct_value, err):
    assert tested_value == correct_value, err + \
            " '%s' instead of '%s'." % (tested_value, correct_value)

def test_get_current_branch():
    error = "The branch of the QGitModel isn't correct."

    model_branch = TEST_master_branch_model.get_current_branch().name
    check(model_branch, "master", error)

    model_branch = TEST_wallace_branch_model.get_current_branch().name
    check(model_branch, "wallace_branch", error)

def test_default_branch():
    dummy_model = QGitModel(TEST_DIR)
    default_branch_name = dummy_model.get_current_branch().name
    error = "The default branch should be the current branch of the repository."
    check(TEST_current_branch_name, default_branch_name, error)

def test_row_count():
    error = "The %s QGitModel doesn't contain the right number of rows."
    check(TEST_wallace_branch_model.rowCount(), len(TEST_wallace_branch_commits),
          error % TEST_wallace_branch_model.get_current_branch().name)

    check(TEST_master_branch_model.rowCount(), len(TEST_master_branch_commits),
          error % TEST_master_branch_model.get_current_branch().name)

def test_column_count():
    error = "The wallace QGitModel doesn't contain the right numer of columns."
    check(TEST_wallace_branch_model.columnCount(), TEST_column_count, error)

def test_data_message():
    message_column = TEST_wallace_branch_model.get_columns().index('message')
    error = "The commit's message isn't correct."
    for row, commit in enumerate(TEST_wallace_branch_commits):
        index = TEST_wallace_branch_model.createIndex(row, message_column)

        check(str(TEST_wallace_branch_model.data(index, Qt.EditRole).toString()),
              commit[1], error)

    for row, commit in enumerate(TEST_master_branch_commits):
        index = TEST_master_branch_model.createIndex(row, message_column)

        check(str(TEST_master_branch_model.data(index, Qt.EditRole).toString()),
              commit[1], error)

def test_data_commit_date():
    date_error = "The commit date isn't correct."
    time_error = "The commit time isn't correct."
    model = TEST_wallace_branch_model
    commit_date_col = model.get_columns().index('committed_date')
    for row, commit in enumerate(TEST_wallace_branch_commits):
        index = model.createIndex(row, commit_date_col)

        tested_datetime = str(model.data(index, Qt.DisplayRole).toString())
        assert TEST_date in tested_datetime, date_error
        assert TEST_time in tested_datetime, time_error

def test_data_author_date():
    date_error = "The author date isn't correct."
    time_error = "The author time isn't correct."
    model = TEST_wallace_branch_model
    author_date_col = model.get_columns().index('authored_date')
    for row, author in enumerate(TEST_wallace_branch_commits):
        index = model.createIndex(row, author_date_col)

        tested_datetime = str(model.data(index, Qt.DisplayRole).toString())
        assert TEST_date in tested_datetime, date_error
        assert TEST_time in tested_datetime, time_error

def test_data_author():
    error = "The author %s isn't correct."
    model = TEST_wallace_branch_model

    author_name_col = model.get_columns().index('author_name')
    author_email_col = model.get_columns().index('author_email')

    for row, author in enumerate(TEST_wallace_branch_commits):
        index = model.createIndex(row, author_name_col)

        tested_author_name = str(model.data(index, Qt.DisplayRole).toString())
        check(tested_author_name, TEST_author_name, error % "name")

        email_index = model.createIndex(row, author_email_col)
        tested_author_email = str(model.data(email_index,
                                               Qt.DisplayRole).toString())
        check(tested_author_email, TEST_author_email, error % "email")

def test_data_committer():
    error = "The committer %s isn't correct."
    model = TEST_wallace_branch_model

    committer_name_col = model.get_columns().index('committer_name')
    committer_email_col = model.get_columns().index('committer_email')

    for row, committer in enumerate(TEST_wallace_branch_commits):
        name_index = model.createIndex(row, committer_name_col)
        tested_committer_name = str(model.data(name_index,
                                               Qt.DisplayRole).toString())
        check(tested_committer_name, TEST_committer_name, error % "name")

        email_index = model.createIndex(row, committer_email_col)
        tested_committer_email = str(model.data(email_index,
                                               Qt.DisplayRole).toString())
        check(tested_committer_email, TEST_committer_email, error % "email")

def test_get_branches():
    wallace_branches = TEST_wallace_branch_model.get_branches()

    error = "The QGitModel doesn't know the right number of branches."
    check(len(wallace_branches), len(TEST_branches), error)

def test_parent():
    index = TEST_wallace_branch_model.createIndex(0, 0)
    assert isinstance(TEST_wallace_branch_model.parent(index), QModelIndex)

def test_row_of():
    commits = TEST_wallace_branch_model.get_git_model().get_commits()

def test_set_branch_twice_fails():
    fails = False
    dummy_model = QGitModel(TEST_DIR)
    dummy_model.set_current_branch(TEST_wallace_branch)
    try:
        dummy_mode.set_current_branch(TEST_master_branch)
    except Exception, err:
        fails = True

    assert fails, "We were able to set the current branch of the model twice."

def wallace_tests():
    test_get_current_branch()
    test_row_count()
    test_column_count()
    test_data_message()
    test_data_commit_date()
    test_data_author_date()
    test_data_author()
    test_data_committer()
    test_get_branches()
    test_parent()
    test_set_branch_twice_fails()
    test_filter_message()

setup_tests()
wallace_tests()
# we should test the master branch model
