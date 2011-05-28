from PyQt4.QtGui import QApplication

from subprocess import Popen, PIPE
import os
import sys

from gitbuster.main_window import MainWindow
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

    def test_all_branches_are_displayed(self):
        error = "All the branches aren't displayed in the checkbox group."
        checkbox_layout = self.gui.branchCheckboxLayout
        number_of_checkboxes = checkbox_layout.count()
        checkboxes = [checkbox_layout.itemAt(id).widget()
                      for id in xrange(number_of_checkboxes)]
        checkboxes_names = set([unicode(checkbox.text())
                                for checkbox in checkboxes])
        TEST_names = set(self.TEST_branches)

        assert checkboxes_names == TEST_names, error
