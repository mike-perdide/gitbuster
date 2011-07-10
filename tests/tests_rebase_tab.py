from PyQt4.QtGui import QApplication
from PyQt4.QtCore import Qt

from subprocess import Popen, PIPE
import os
import sys

from gitbuster.main_window import MainWindow
from gitbuster.branch_view import ButtonLineEdit
from gfbi_core.gfbi_repo import Repo

from template_test import TemplateTest


class TestsRebaseTab(TemplateTest):

    @classmethod
    def setup_class(cls):
        TemplateTest.setup_class()
        cls.gen_fake_2()
        os.chdir(cls.TEST_dir)
        cls.set_test_values()

        cls.app = QApplication(sys.argv)
        cls.window = MainWindow(directory=cls.TEST_dir)
        cls.window.show()
        cls.gui = cls.window._ui
        cls.window._ui.mainTabWidget.setCurrentIndex(0)

    def test_all_checkboxes_are_displayed(self):
        print "Test all checkboxes are displayed"
        self.run_command("./fake_git_gen_2.sh")
        self.window.refresh(force=True)

        error = "All the branches aren't displayed in the checkbox group."
        checkboxes = self.get_checkboxes()
        checkboxes_names = set((unicode(checkbox.text())
                               for checkbox in checkboxes))
        TEST_names = set(self.TEST_branches)

        self.check(checkboxes_names, TEST_names, error)

    def test_only_one_checkbox_is_checked(self):
        print "Test only one checkbox is checked"
        self.run_command("./fake_git_gen_2.sh")
        self.window.refresh(force=True)

        error = "More than one checkbox is checked."
        checked_checkboxes = self.get_checked_checkboxes()
        self.check(len(checked_checkboxes), 1, error)

    def test_only_one_branch_is_displayed(self):
        print "Test only one branch is displayed"
        self.run_command("./fake_git_gen_2.sh")
        self.window.refresh(force=True)

        error = "More than one branch is displayed."
        displayed_widgets = self.get_displayed_branch_widgets()
        self.check(len(displayed_widgets), 1, error)

    def test_displayed_branch_data_is_correct(self):
        error = "The displayed content isn't correct"


    def test_checking_one_checkbox_displays_branch(self):
        print "Test checking one checkbox displays the branch"
        self.run_command("./fake_git_gen_2.sh")
        self.window.refresh(force=True)

        error = "Checking the %s checkbox didn't display the right widgets."

        unchecked_checkboxes = self.get_unchecked_checkboxes()
        an_unchecked_checkbox = unchecked_checkboxes.pop()

        before_the_check = self.get_displayed_branch_widgets()
        # Check the unechecked checkbox
        an_unchecked_checkbox.setCheckState(Qt.Checked)

        after_the_check = self.get_displayed_branch_widgets()

        self.check(len(after_the_check - before_the_check), 1,
                   error % (an_unchecked_checkbox.text()))

        newly_added = (after_the_check - before_the_check)
#        name_widget = [widget for widget in newly_added
#                       if isinstance(widget, ButtonLineEdit)][0]
        # Check the name of the new displayed branch

    def test_dropping_data(self):
        print "Test dropping data"
        self.gen_fake_2()
        self.window.refresh(force=True)

        for branch, model in self.window._models.items():
            if branch.name == "master":
                master_model = model
            elif branch.name == "wallace_branch":
                wallace_model = model

        message_column = model.get_columns().index("message")


        commit_message_to_be_dropped = wallace_model.data(
                                        model.createIndex(1, message_column),
                                        Qt.EditRole).toString()
        before_drop = master_model.data(model.createIndex(0, message_column),
                                        Qt.EditRole).toString()
        color_before_drop = master_model.data(
                                model.createIndex(0, message_column),
                                Qt.BackgroundColorRole).toPyObject()

        error = "Bad test conditions: the data has already been dropped."
        assert commit_message_to_be_dropped != before_drop, error

        data_to_drop = wallace_model.mimeData([wallace_model.createIndex(1, 0),])
        master_model.dropMimeData(data_to_drop, Qt.CopyAction, 0, 0, None)

        after_drop = master_model.data(model.createIndex(0, message_column),
                                        Qt.EditRole).toString()

        error = "The data wasn't dropped properly before the first row."
        self.check(after_drop, commit_message_to_be_dropped, error)

        color_after_drop = master_model.data(
                            model.createIndex(0, message_column),
                            Qt.BackgroundColorRole).toPyObject()
        error = "The background color of the dropped commit isn't yellow."
        self.check(color_after_drop, Qt.yellow, error)

        self.window.undo_history()

        after_undo = master_model.data(model.createIndex(0, message_column),
                                        Qt.EditRole).toString()
        error = "After an undo, the dropped data is still here."
        self.check(after_undo, before_drop, error)

        color_after_undo = master_model.data(
                            model.createIndex(0, message_column),
                            Qt.BackgroundColorRole).toPyObject()
        error = "The background color hasn't change after the undo."
        self.check(color_after_undo, color_before_drop, error)

    def test_create_from_row(self):
        print "Test create from row"
        self.gen_fake_2()
        self.window.refresh(force=True)

        shown_branches = len(self.get_displayed_branch_widgets())

        for branch, model in self.window._models.items():
            if branch.name == "master":
                master_model = model
            elif branch.name == "wallace_branch":
                wallace_model = model

        self.window.create_new_branch_from_model(
                                (master_model.createIndex(0, 0),
                                 master_model.createIndex(1, 0),
                                 master_model.createIndex(2, 0)),
                                "test_branch"
        )

        after_shown_branches = len(self.get_displayed_branch_widgets())
        error = "After creating a branch from a row, wrong number of branch displayed "
        self.check(after_shown_branches, shown_branches + 1, error)

        # Check number of rows
        # Check application
        test_model = [model for model in self.window._models.values()
                      if model.name_to_display() == "test_branch"][0]
        self.window.apply_models((test_model,), True, True)

        a_repo = Repo(self.TEST_dir)
        error = "Branch from commit wasn't created"
        assert [branch for branch in a_repo.branches
                if branch.name == "test_branch"], error

        error = "Branch %s was deleted!"
        for name in ("master", "wallace_branch"):
            assert [branch for branch in a_repo.branches
                    if branch.name == name], error % name

        after_write_branches = len(self.get_displayed_branch_widgets())
        error = "After writing a branch from a row, wrong number of branch displayed "
        self.check(after_write_branches, shown_branches + 1, error)

    def test_remove_row(self):
        print "Test remove row"
        self.gen_fake_2()
        self.window.refresh(force=True)

        master_model = [model for model in self.window._models.values()
                        if model.name_to_display() == 'master'][0]
        master_model.start_history_event()
        master_view = self.window.rebase_main_class.get_branch_view("master")

        a_repo = Repo(self.TEST_dir)
        master_branch = a_repo.get_branch_from_ref("refs/heads/master")
        commits = list(a_repo.all_commits(rev=master_branch))
        orig_message = commits[1].message

        master_view.remove_rows([0,])
        self.window.apply_models((master_model,), True, True)

        post_test_repo = Repo(self.TEST_dir)
        master_branch = post_test_repo.get_branch_from_ref("refs/heads/master")
        commits = list(post_test_repo.all_commits(rev=master_branch))

        error = "The commit wasn't deleted."
        self.check(commits[0].message, orig_message, error)

        # Checking that the deleted commit isn't displayed anymore.
        master_model = [model for model in self.window._models.values()
                        if model.name_to_display() == 'master'][0]
        message_col = master_model.get_columns().index("message")
        first_message = str(master_model.data(master_model.createIndex(0,
                                                                   message_col),
                                          Qt.EditRole).toString())
        error = "The commit was deleted but is still displayed."
        self.check(first_message, orig_message, error)

    def test_insert_remove(self):
        print "Test insert remove"
        self.gen_fake_2()
        self.window.refresh(force=True)

        master_view = self.window.rebase_main_class.get_branch_view("master")

        master_model = [model for model in self.window._models.values()
                        if model.name_to_display() == "master"][0]
        wallace_model = [model for model in self.window._models.values()
                         if model.name_to_display() == "wallace_branch"][0]

        master_model.start_history_event()

        master_view.remove_rows([3,])
        data_to_drop = wallace_model.mimeData(
                                        [wallace_model.createIndex(1, 0),])
        master_model.dropMimeData(data_to_drop, Qt.CopyAction, 1, 0, None)

        a_repo = Repo(self.TEST_dir)
        commits = list(a_repo.all_commits(rev="refs/heads/master"))
        orig_message = commits[1].message

        commits = list(a_repo.all_commits(rev="refs/heads/wallace_branch"))
        inserted_message = commits[1].message

        self.window.apply_models((master_model,), True, True)

        post_test_repo = Repo(self.TEST_dir)
        commits = list(post_test_repo.all_commits(rev="refs/heads/master"))
        new_message = commits[1].message

        self.check(new_message, inserted_message, "Insertion failed")

    def get_checked_checkboxes(self):
        checkboxes = self.get_checkboxes()
        return set((checkbox for checkbox in checkboxes
                   if checkbox.isChecked()))

    def get_unchecked_checkboxes(self):
        checkboxes = self.get_checkboxes()
        return set((checkbox for checkbox in checkboxes
                   if not checkbox.isChecked()))

    def get_checkboxes(self):
        checkbox_layout = self.gui.branchCheckboxLayout
        number_of_checkboxes = checkbox_layout.count()
        checkboxes = set((checkbox_layout.itemAt(id).widget()
                          for id in xrange(number_of_checkboxes)))
        return checkboxes

    def get_displayed_branch_widgets(self):
        view_layout = self.gui.viewLayout
        widgets_count = view_layout.count()
        widgets = set((view_layout.itemAt(id).widget()
                      for id in xrange(widgets_count)))
        displayed_widgets = set((widget for widget in widgets
                                if widget.isVisible()))

        return displayed_widgets

    def all_tests(self):
        self.test_all_checkboxes_are_displayed()
        self.test_only_one_checkbox_is_checked()
        self.test_only_one_branch_is_displayed()
        self.test_checking_one_checkbox_displays_branch()
        self.test_dropping_data()
        self.test_create_from_row()
        self.test_remove_row()
        self.test_insert_remove()

    @classmethod
    def teardown_class(cls):
        cls.window.close()


if __name__ == "__main__":
    to_test = TestsRebaseTab()
    to_test.setup_class()
    to_test.all_tests()
    to_test.teardown_class()
