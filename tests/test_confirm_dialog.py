from PyQt4.QtGui import QApplication
from PyQt4.QtCore import Qt

from subprocess import Popen, PIPE
import os
import sys

from gitbuster.main_window import MainWindow
from gitbuster.confirm_dialog import ConfirmDialog
from gitbuster.branch_view import ButtonLineEdit
from template_test import TemplateTest


class TestsConfirmDialog(TemplateTest):

    @classmethod
    def setup_class(cls):
        TemplateTest.setup_class()
        cls.run_command("./fake_git_gen_2.sh")
        os.chdir(cls.TEST_dir)
        cls.set_test_values()

        cls.app = QApplication(sys.argv)
        cls.window = MainWindow(directory=cls.TEST_dir)
        cls.window.show()
        cls.gui = cls.window._ui
        cls.window._ui.mainTabWidget.setCurrentIndex(0)

        for branch, model in cls.window._models.items():
            if branch.name == "master":
                cls.master_model = model
            elif branch.name == "wallace_branch":
                cls.wallace_model = model

    def test_modified_name_appears_in_dialog(self):
        self.master_model.start_history_event()
        self.master_model.set_new_branch_name("rodrigo")

        to_write_models = [model for model in self.window._models.values()
                           if model.should_be_written()]

        msgBox = ConfirmDialog(to_write_models)

        error = "Wrong number if displayed modified models."
        self.check(len(msgBox._model_checkboxes), 1, error)

        error = "The displayed model has the wrong name."
        checkbox = msgBox._model_checkboxes[0][0]
        self.check(checkbox.text(), "rodrigo", error)

        self.window.undo_history()

    def test_inserted_commits_appears_in_dialog(self):
        data_to_drop = self.wallace_model.mimeData(
                                       [self.wallace_model.createIndex(1, 0),])
        self.master_model.dropMimeData(data_to_drop, Qt.CopyAction, 0, 0, None)

        to_write_models = [model for model in self.window._models.values()
                           if model.should_be_written()]

        msgBox = ConfirmDialog(to_write_models)

        error = "Wrong number if displayed modified models."
        self.check(len(msgBox._model_checkboxes), 1, error)

        error = "The displayed model has the wrong name."
        checkbox = msgBox._model_checkboxes[0][0]
        self.check(checkbox.text(), "master", error)

        self.window.undo_history()

    def test_remove_commit_appears_in_dialog(self):
        master_view = self.window.rebase_main_class.get_branch_view("master")

        master_view.remove_rows([0,])

        to_write_models = [model for model in self.window._models.values()
                           if model.should_be_written()]

        msgBox = ConfirmDialog(to_write_models)

        error = "Wrong number if displayed modified models."
        self.check(len(msgBox._model_checkboxes), 1, error)

        error = "The displayed model has the wrong name."
        checkbox = msgBox._model_checkboxes[0][0]
        self.check(checkbox.text(), "master", error)

        self.window.undo_history()

    def test_remote_branch_doesnt_appear_in_dialog(self):
        pass

    def test_branch_from_commit_appears_in_dialog(self):
        pass

    def all_tests(self):
        self.test_modified_name_appears_in_dialog()
        self.test_inserted_commits_appears_in_dialog()
        self.test_remove_commit_appears_in_dialog()

if __name__ == "__main__":
    to_test = TestsConfirmDialog()
    to_test.setup_class()
    to_test.all_tests()
