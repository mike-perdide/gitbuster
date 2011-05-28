from gitbuster.q_git_model import QGitModel
from subprocess import Popen, PIPE
import time


class TemplateTest:

    @classmethod
    def setup_class(cls):
        cls.TEST_dir = "/tmp/tests_git"
        cls.TEST_column_count = 10
        cls.TEST_wallace_author_name = "Author 'Wallace' Groom"
        cls.TEST_wallace_author_email = "author-wallace@groom.com"
        cls.TEST_master_author_name = "Author 'Master' Groom"
        cls.TEST_master_author_email = "author-master@groom.com"

        cls.TEST_committer_name = "Committer Groom"
        cls.TEST_committer_email = "committer@groom.com"

        cls.TEST_master_branch = None
        cls.TEST_wallace_branch = None
        cls.TEST_master_branch_model = None
        cls.TEST_wallace_branch_model = None
        cls.TEST_master_branch_commits = None
        cls.TEST_wallace_branch_commits = None
        cls.TEST_date = None
        cls.TEST_time = None
        cls.TEST_branches = None
        cls.TEST_current_branch_name = ""

        cls.TEST_date = None
        cls.TEST_time = None

        format = "%d/%m/%Y %H:%M"
        cls.TEST_date, cls.TEST_time = time.strftime(format).split(" ")

    @classmethod
    def run_command(cls, command):
        handle = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
        handle.wait()
        return handle.stdout.readlines(), handle.stderr.readlines()

    @classmethod
    def read_commits_from_log(cls):
        stdout, stderr = cls.run_command("git log --pretty='format:%h %s'")
        commits_storage_list = []
        for line in stdout:
            short_hexsha = line.split(" ")[0]
            message = " ".join(line.split(" ")[1:]).strip()

            commits_storage_list.append((short_hexsha, message))

        return commits_storage_list

    @classmethod
    def set_test_values(cls):
        """
            This will set the global branches, wallace_branch_name,
            wallace_branch_commits, TEST_wallace_branch_model,
            TEST_master_branch_model.
        """
        dummy_model = QGitModel(cls.TEST_dir)

        branches = dummy_model.get_branches()
        cls.TEST_master_branch = [branch for branch in branches
                                   if branch.name == 'master'][0]
        master_model = cls.TEST_master_branch_model = QGitModel(cls.TEST_dir)
        master_model.set_current_branch(cls.TEST_master_branch)
        master_model.populate()

        cls.TEST_wallace_branch = [branch for branch in branches
                               if branch.name == 'wallace_branch'][0]
        wallace_model = cls.TEST_wallace_branch_model = QGitModel(cls.TEST_dir)
        wallace_model.set_current_branch(cls.TEST_wallace_branch)
        wallace_model.populate()

        cls.run_command("git checkout master")
        cls.TEST_master_branch_commits = cls.read_commits_from_log()

        cls.run_command("git checkout wallace_branch")
        cls.TEST_wallace_branch_commits = cls.read_commits_from_log()

        stdout, stderr = cls.run_command("git branch")
        cls.TEST_branches = []
        for line in stdout:
            branch_name = line.split(' ')[-1].strip()
            if line[0] == '*':
                cls.TEST_current_branch_name = branch_name
            cls.TEST_branches.append(branch_name)

    @classmethod
    def check(cls, tested_value, correct_value, err):
        assert tested_value == correct_value, err + \
                " '%s' instead of '%s'." % (tested_value, correct_value)
