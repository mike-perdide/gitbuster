from gfbi_core.util import Index
from gfbi_core.editable_git_model import EditableGitModel

def graph_model(model):
    head_commit = model.get_commits()[0]
    global parents_index
    parents_index = model.get_columns().index("parents")
    print_commit(model, head_commit)

def print_commit(model, commit, offset=0):
    row = model.row_of(commit)
    print_single(model, commit)
    sub_trees  = len(model.data(Index(row, parents_index)))
    if sub_trees == 2:
    for _commit in model.data(Index(row, parents_index)):
        print_single(model, _commit, before=0, after=1)

def print_single(model, commit, before=0, after=0):
    row = model.row_of(commit)
    print "| " * before + "o" + " |" * after + "\t\t\t" + model.data(Index(row, 7)).split("\n")[0]


graph_model(EditableGitModel("/tmp/tests_git"))
