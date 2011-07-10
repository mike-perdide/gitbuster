from tests_q_git_model import TestsQGitModel
from tests_rebase_tab import TestsRebaseTab
from tests_confirm_dialog import TestsConfirmDialog

print "Tests started"
print "> TestsQGitModel"
to_test = TestsQGitModel()
to_test.setup_class()
to_test.all_tests()


print "> TestsRebaseTab"
to_test = TestsRebaseTab()
to_test.setup_class()
to_test.all_tests()
to_test.teardown_class()


print "> TestsConfirmDialog"
to_test = TestsConfirmDialog()
to_test.setup_class()
to_test.all_tests()
to_test.teardown_class()

print "Tests finished"
