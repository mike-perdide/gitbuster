# The goal of this game is to change the modifications of X and update master
import git
from pprint import pprint
from subprocess import Popen, PIPE
import os
handle = Popen("./gen_fake_git.sh", shell=True, stdout=PIPE, stderr=PIPE)
handle.wait()

os.chdir("/tmp/tests_git")
repo = git.Repo("/tmp/tests_git")

commits = list(repo.iter_commits())

pprint([(commit, commit.message.strip()) for commit in commits])

def run(command):
    handle = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    return handle.stdout.read().strip()

def get_commit_from_message(message):
    return [commit for commit in commits
            if commit.message.strip().startswith(message)][0]

init_commit = get_commit_from_message("Initial commit")
commit_A = get_commit_from_message("A (1')")
commit_B = get_commit_from_message("B (2')")
commit_C = get_commit_from_message("C (3')")

commit_1 = get_commit_from_message("1")
commit_2 = get_commit_from_message("2")
commit_3 = get_commit_from_message("3")

commit_T = get_commit_from_message("T")
commit_U = get_commit_from_message("U")
commit_V = get_commit_from_message("V")

mergeABC = get_commit_from_message("Merge ABC (conflicts)")
mergeABC123 = get_commit_from_message("Merge ABC123")

commit_X = get_commit_from_message("X")

updated_refs = {}

# Let's change X's content
repo.git.checkout(init_commit.hexsha)
run("git cherry-pick -n %s" % commit_X.hexsha)
open("X", "w").write("XXX\n")
run("git add X")
new_tree = run("git write-tree")
parent_string = " ".join(["-p %s" % parent.hexsha
                         for parent in commit_X.parents])
open("tmp_message", "w").write(commit_X.message)
new_sha = run("git commit-tree %s %s < tmp_message" % (new_tree, parent_string))

updated_refs[commit_X] = new_sha

# Now, X has been changed, some of the subtrees need to be rewritten,
# some don't.
def children_commits_to_rewrite(updated_parent):
    to_rewrite = []
    for commit in commits:
        if updated_parent in commit.parents:
            to_rewrite.append(commit)
    return to_rewrite

def all_should_be_updated(updated_parent):
    should_be_updated = set()
    print "What should be updated if we update", updated_parent.message.strip()
    for commit in children_commits_to_rewrite(updated_parent):
        print commit.message.strip(), "should be updated"

    for commit in children_commits_to_rewrite(updated_parent):
        should_be_updated.add(commit)
        should_be_updated.update(all_should_be_updated(commit))
    return should_be_updated

should_be_updated = all_should_be_updated(commit_X)
print len(should_be_updated)

def update_commit(commit):
    print "Updating", commit.message.strip().split('\n')[0]
    if len(commit.parents) != 1:
        # This is a merge
        for parent in commit.parents:
            if parent in should_be_updated and parent not in updated_refs:
                # Meaning one of the parent branches of the merge hasn't been
                # rewritten yet => skip for now
                print "Not ready to update the merge commit yet."
                return
        ref_update(commit)
    else:
        ref_update(commit)

def ref_update(commit):
    _parent = commit.parents[0]
    _parent_sha = updated_refs[_parent]

    run("git checkout -f %s" % _parent_sha)

    if len(commit.parents) == 1:
        # This is not a merge
        run("git cherry-pick -n %s" % commit.hexsha)
    else:
        # This is a merge
        run("git cherry-pick -n -m 1 %s" % commit.hexsha)

    new_tree = run("git write-tree")

    parent_string = ""
    for parent in commit.parents:
        if parent in updated_refs:
            _parent = updated_refs[parent]
        else:
            _parent = parent

        parent_string += "-p %s " % _parent

    open("tmp_message", "w").write(commit.message)
    new_sha = run("git commit-tree %s %s < tmp_message" % (new_tree, parent_string))

    updated_refs[commit] = new_sha

    for c in children_commits_to_rewrite(commit):
        update_commit(c)

#repo.git.checkout(new_sha)
for commit in children_commits_to_rewrite(commit_X):
    update_commit(commit)

#pprint([(commit, commit.message, updated_refs[commit])
#        for commit in updated_refs])
repo.git.checkout(updated_refs[mergeABC123])
