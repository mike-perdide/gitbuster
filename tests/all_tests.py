from tests_q_git_model import TestsQGitModel
from tests_rebase_tab import TestsRebaseTab

to_test = TestsQGitModel()
to_test.setup_class()
to_test.test_get_current_branch()
to_test.test_default_branch()
to_test.test_row_count()
to_test.test_column_count()
to_test.test_data_message()
to_test.test_data_message()
to_test.test_data_author_date()
to_test.test_data_author()
to_test.test_data_committer()
to_test.test_get_branches()
to_test.test_parent()
to_test.test_set_branch_twice_fails()
to_test.test_filter_message()
to_test.test_filter_author()


to_test = TestsRebaseTab()
to_test.setup_class()
to_test.all_tests()
