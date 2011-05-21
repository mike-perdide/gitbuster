"""
    This test script aims at testing QGitModel, without any modifications.
"""
from gitbuster.q_git_model import QGitModel
from PyQt4.QtCore import Qt
from subprocess import Popen, PIPE
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
        wallace_branch_commits, wallace_branch_model, master_branch_model.
    """
    global TEST_branches
    global TEST_wallace_branch_name
    global TEST_wallace_branch_commits
    global wallace_branch_model
    global master_branch_model
    wallace_branch_model = QGitModel(TEST_DIR)

    branches = wallace_branch_model.get_branches()
    master_brch = [branch for branch in branches if branch.name == 'master'][0]
    master_branch_model = QGitModel(TEST_DIR)
    master_branch_model.set_current_branch(master_brch)

    stdout, stderr = run_command("git branch")
    for line in stdout:
        branch_name = line.split(' ')[-1].strip()
        if line[0] == '*':
            TEST_wallace_branch_name = branch_name
        TEST_branches.append(branch_name)

    read_commits_from_log(TEST_wallace_branch_commits)
    run_command("git checkout mater")

    read_commits_from_log(TEST_master_branch_commits)

def setup_tests():
    run_command("./fake_git_gen.sh")
    os.chdir(TEST_DIR)
    set_test_values(TEST_DIR)

def check(tested_value, correct_value, err):
    assert tested_value == correct_value, err + \
            " '%s' instead of '%s'." % (tested_value, correct_value)

def test_wallace_branch_init():
    model_wallace_branch = wallace_branch_model.get_current_branch().name
    error = "The wallace branch after QGitModel creation isn't correct."
    check(model_wallace_branch, TEST_wallace_branch_name, error)

def test_number_rows():
    error = "The wallace QGitModel doesn't contain the right number of rows."
    check(wallace_branch_model.rowCount(), len(TEST_wallace_branch_commits),
          error)

    error = "The master QGitModel doesn't contain the right number of rows."
    check(master_branch_model.rowCount(), len(TEST_master_branch_commits),
          error)

def test_number_columns():
    error = "The wallace QGitModel doesn't contain the right numer of columns."
    check(wallace_branch_model.columnCount(), TEST_column_count, error)

def test_message_column():
    message_column = wallace_branch_model.get_columns().index('message')
    error = "The commit's message isn't correct."
    for row, commit in enumerate(TEST_wallace_branch_commits):
        index = wallace_branch_model.createIndex(row, message_column)

        check(str(wallace_branch_model.data(index, Qt.EditRole).toString()),
              commit[1], error)

    for row, commit in enumerate(TEST_master_branch_commits):
        index = master_branch_model.createIndex(row, message_column)

        check(str(master_branch_model.data(index, Qt.EditRole).toString()),
              commit[1], error)

def test_number_branches():
    wallace_branches = wallace_branch_model.get_branches()

    error = "The QGitModel doesn't know the right number of branches."
    check(len(wallace_branches), len(TEST_branches), error)

setup_tests()
test_wallace_branch_init()
test_number_rows()
test_number_columns()
test_message_column()
test_number_branches()
