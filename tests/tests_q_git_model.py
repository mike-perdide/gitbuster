"""
    This test script aims at testing QGitModel, without any modifications.
"""
from PyQt4.QtCore import Qt, QModelIndex
from gitbuster.q_git_model import QGitModel
from gfbi_core.util import GfbiException

from template_test import TemplateTest
import os


class TestsQGitModel(TemplateTest):

    @classmethod
    def setup_class(cls):
        TemplateTest.setup_class()
        cls.run_command("./fake_git_gen.sh")
        os.chdir(cls.TEST_dir)
        cls.set_test_values()

    def test_get_current_branch(self):
        error = "The branch of the QGitModel isn't correct."

        model_branch = self.TEST_master_branch_model.get_current_branch().name
        self.check(model_branch, "master", error)

        model_branch = self.TEST_wallace_branch_model.get_current_branch().name
        self.check(model_branch, "wallace_branch", error)

    def test_default_branch(self):
        error = "The default branch should be the current branch of the repository."
        dummy_model = QGitModel(self.TEST_dir)
        default_branch_name = dummy_model.get_current_branch().name
        self.check(self.TEST_current_branch_name, default_branch_name, error)

    def test_row_count(self):
        error = "The %s QGitModel doesn't contain the right number of rows."
        wallace_model = self.TEST_wallace_branch_model
        self.check(wallace_model.rowCount(wallace_model),
                   len(self.TEST_wallace_branch_commits),
                   error % wallace_model.get_current_branch().name)

        master_model = self.TEST_master_branch_model
        self.check(master_model.rowCount(),
                   len(self.TEST_master_branch_commits),
                   error % master_model.get_current_branch().name)

    def test_column_count(self):
        error = "The wallace QGitModel doesn't contain the right numer of columns."
        model = self.TEST_wallace_branch_model
        self.check(model.columnCount(), self.TEST_column_count, error)

    def test_data_message(self):
        error = "The commit's message isn't correct."

        model = self.TEST_wallace_branch_model
        message_column = model.get_columns().index('message')
        for row, commit in enumerate(self.TEST_wallace_branch_commits):
            index = model.createIndex(row, message_column)

            self.check(str(model.data(index, Qt.EditRole).toString()),
                       commit[1], error)

        model = self.TEST_master_branch_model
        for row, commit in enumerate(self.TEST_master_branch_commits):
            index = model.createIndex(row, message_column)

            self.check(str(model.data(index, Qt.EditRole).toString()),
                       commit[1], error)

    def test_data_commit_date(self):
        date_error = "The commit date isn't correct."
        time_error = "The commit time isn't correct."
        model = self.TEST_wallace_branch_model
        commit_date_col = model.get_columns().index('committed_date')
        for row, commit in enumerate(self.TEST_wallace_branch_commits):
            index = model.createIndex(row, commit_date_col)

            tested_datetime = str(model.data(index, Qt.DisplayRole).toString())
            assert self.TEST_date in tested_datetime, date_error
            assert self.TEST_time in tested_datetime, time_error

    def test_data_author_date(self):
        date_error = "The author date isn't correct."
        time_error = "The author time isn't correct."
        model = self.TEST_wallace_branch_model
        author_date_col = model.get_columns().index('authored_date')
        for row, author in enumerate(self.TEST_wallace_branch_commits):
            index = model.createIndex(row, author_date_col)

            tested_datetime = str(model.data(index, Qt.DisplayRole).toString())
            assert self.TEST_date in tested_datetime, date_error
            assert self.TEST_time in tested_datetime, time_error

    def test_data_author(self):
        error = "The author %s isn't correct."
        model = self.TEST_master_branch_model

        author_name_col = model.get_columns().index('author_name')
        author_email_col = model.get_columns().index('author_email')

        for row, author in enumerate(self.TEST_master_branch_commits):
            index = model.createIndex(row, author_name_col)
            author_name = str(model.data(index, Qt.DisplayRole).toString())
            self.check(author_name,
                       self.TEST_master_author_name, error % "name")

            index = model.createIndex(row, author_email_col)
            author_email = str(model.data(index, Qt.DisplayRole).toString())
            self.check(author_email,
                       self.TEST_master_author_email, error % "email")

    def test_data_committer(self):
        error = "The committer %s isn't correct."
        model = self.TEST_wallace_branch_model

        committer_name_col = model.get_columns().index('committer_name')
        committer_email_col = model.get_columns().index('committer_email')

        for row, committer in enumerate(self.TEST_wallace_branch_commits):
            index = model.createIndex(row, committer_name_col)
            committer_name = str(model.data(index, Qt.DisplayRole).toString())
            self.check(committer_name, self.TEST_committer_name, error % "name")

            index = model.createIndex(row, committer_email_col)
            committer_email = str(model.data(index, Qt.DisplayRole).toString())
            self.check(committer_email,
                       self.TEST_committer_email, error % "email")

    def test_get_branches(self):
        error = "The QGitModel doesn't know the right number of branches."
        wallace_branches = self.TEST_wallace_branch_model.get_branches()
        self.check(len(wallace_branches), len(self.TEST_branches), error)

    def test_parent(self):
        index = self.TEST_wallace_branch_model.createIndex(0, 0)
        model = self.TEST_wallace_branch_model
        assert isinstance(model.parent(index), QModelIndex)

#    def test_row_of():
#        commits = self.TEST_wallace_branch_model.get_git_model().get_commits()

    def test_set_branch_twice_fails(self):
        fails = False
        dummy_model = QGitModel(self.TEST_dir)
        dummy_model.set_current_branch(self.TEST_wallace_branch)
        try:
            dummy_model.set_current_branch(self.TEST_master_branch)
        except GfbiException, err:
            fails = True

        assert fails, "We were able to set the current branch of the model twice."

    def test_filter_message(self):
        dummy_model = QGitModel(self.TEST_dir)
        dummy_model.set_current_branch(self.TEST_master_branch)
        dummy_model.populate()
        message = "rodney"
        dummy_model.filter_set("message", message)

        error = "On the master branch model, wrong message filter score for %d:%d"
        message_column = dummy_model.get_columns().index('message')
        for row, commit in enumerate(self.TEST_master_branch_commits):
            index = dummy_model.createIndex(row, message_column)
            score = dummy_model.filter_score(index)

            if message in commit[1]:
                self.check(score, 1, error % (row, message_column))
            else:
                self.check(score, 0, error % (row, message_column))

    def test_filter_author(self):
        dummy_model = QGitModel(self.TEST_dir)
        dummy_model.set_current_branch(self.TEST_wallace_branch)
        dummy_model.populate()
        author = "Wallace"
        author_email = "-wallace"

        error = "On the wallace branch model, wrong author_name filter score for %d:%d"
        error_email = "On the wallace branch model, wrong author_email filter score for %d:%d"
        author_name_column = dummy_model.get_columns().index('author_name')
        author_email_column = dummy_model.get_columns().index('author_email')
        for row, commit in enumerate(self.TEST_wallace_branch_commits):
            dummy_model.filter_set("nameEmail", author)
            index = dummy_model.createIndex(row, author_name_column)
            score = dummy_model.filter_score(index)

            dummy_model.filter_set("nameEmail", author_email)
            index_email = dummy_model.createIndex(row, author_email_column)
            score_email = dummy_model.filter_score(index_email)

            if row != dummy_model.rowCount() - 1:
                self.check(score, 1, error % (row, author_name_column))
                self.check(score_email, 1,
                           error_email % (row, author_email_column))
            else:
                self.check(score, 0, error % (row, author_name_column))
                self.check(score_email, 0,
                           error_email % (row, author_email_column))
