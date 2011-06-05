from PyQt4.QtGui import QApplication
from PyQt4.QtCore import Qt

from subprocess import Popen, PIPE
import os
import sys

from gitbuster.main_window import MainWindow
from gitbuster.branch_view import ButtonLineEdit
from template_test import TemplateTest


class TestsRebaseTab(TemplateTest):

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

    def test_all_checkboxes_are_displayed(self):
        error = "All the branches aren't displayed in the checkbox group."
        checkboxes = self.get_checkboxes()
        checkboxes_names = set((unicode(checkbox.text())
                               for checkbox in checkboxes))
        TEST_names = set(self.TEST_branches)

        self.check(checkboxes_names, TEST_names, error)

    def test_only_one_checkbox_is_checked(self):
        error = "More than one checkbox is checked."
        checked_checkboxes = self.get_checked_checkboxes()
        self.check(len(checked_checkboxes), 1, error)

    def test_only_one_branch_is_displayed(self):
        error = "More than one branch is displayed."
        displayed_widgets = self.get_displayed_branch_widgets()
        self.check(len(displayed_widgets), 1, error)

    def test_displayed_branch_data_is_correct(self):
        error = "The displayed content isn't correct"


    def test_checking_one_checkbox_displays_branch(self):
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

if __name__ == "__main__":
    to_test = TestsRebaseTab()
    to_test.setup_class()
    to_test.test_all_checkboxes_are_displayed()
    to_test.test_only_one_checkbox_is_checked()
    to_test.test_only_one_branch_is_displayed()
    to_test.test_checking_one_checkbox_displays_branch()
