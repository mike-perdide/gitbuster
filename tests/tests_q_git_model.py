"""
    This test script aims at testing QGitModel, without any modifications.
"""
from gitbuster.q_git_model import QGitModel
from PyQt4.QtCore import Qt, QModelIndex
from subprocess import Popen, PIPE
import trace
import sys

import os

TEST_DIR = "/tmp/tests_git"
TEST_branches = []
TEST_wallace_branch_name = ""
TEST_wallace_branch_commits = []
TEST_column_count = 10
TEST_master_branch_commits = []

def run_command(command):
    handle = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    handle.wait()
    return handle.stdout.readlines(), handle.stderr.readlines()

def read_commits_from_log(commits_storage_list):
    stdout, stderr = run_command("git log --pretty='format:%h %s'")
    for line in stdout:
        short_hexsha = line.split(" ")[0]
        message = " ".join(line.split(" ")[1:]).strip()

        commits_storage_list.append((short_hexsha, message))

def set_test_values(dir):
    """
        This will set the global branches, wallace_branch_name,
        wallace_branch_commits, TEST_wallace_branch_model, TEST_master_branch_model.
    """
    global TEST_branches
    global TEST_current_branch_name
    global TEST_wallace_branch_commits
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

    read_commits_from_log(TEST_master_branch_commits)

    run_command("git checkout wallace_branch")
    read_commits_from_log(TEST_wallace_branch_commits)

    stdout, stderr = run_command("git branch")
    for line in stdout:
        branch_name = line.split(' ')[-1].strip()
        if line[0] == '*':
            TEST_current_branch_name = branch_name
        TEST_branches.append(branch_name)

def setup_tests():
    run_command("./fake_git_gen.sh")
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
    test_get_branches()
    test_parent()

setup_tests()
wallace_tests()
TEST_wallace_branch_model.populate()
wallace_tests()
test_set_branch_twice_fails()
