from gfbi_core.util import Index
from gfbi_core.editable_git_model import EditableGitModel
from pprint import pprint

total_branches = 1
row = 0

#def graph_model(model):
#    head_commit = model.get_commits()[0]
#    global parents_index
#    parents_index = model.get_columns().index("parents")
#    print_commit(model, head_commit)

def preprocessed_commits(model):
    head_commit = model.get_commits()[0]

    global preprocessed
    preprocessed = []
    prep_commit(head_commit)

def prep_commit(commit, col=0):
    global preprocessed
    global row
    global total_branches

    existing_row = [item for item in preprocessed if item and item[1] == commit]
    if existing_row:
#        newcol = existing_row[0][0]
        preprocessed[preprocessed.index(existing_row[0])] = None
    preprocessed.append((col, commit))

    if len(commit.parents) != 1:
        newcol = col + 1
    else:
        newcol = col

    for _commit in reversed(commit.parents):
        prep_commit(_commit, newcol)
        newcol -= 1

def postprocess_commits():
    for coord in preprocessed:
        print coord
        

#def print_commit(model, commit, offset=0):
#    global total_branches
#
#    row = model.row_of(commit)
#    print_single(model, commit)
#    sub_trees  = len(model.data(Index(row, parents_index)))
#
#    if sub_trees == 2:
#        print '|\\'
#        total_branches += 1
#
#    for _commit in model.data(Index(row, parents_index)):
#        print_single(model, _commit, before=0, after=1)
#
#def print_single(model, commit, before=0, after=0):
#    row = model.row_of(commit)
#    print "| " * before + "o" + " |" * after + "\t\t\t" + \
#            model.data(Index(row, 7)).split("\n")[0]

preprocessed_commits(EditableGitModel("/tmp/tests_git"))
#pprint(preprocessed)

awaiting_closure = {}
column = 0
commit = None
for coord in preprocessed:
    if coord:
        if coord[0] < column:
            awaiting_closure[column] = commit
        column = coord[0]
        commit = coord[1]
        message = coord[1].message
#        print "===============", message.strip()
        display_string = "| " * (column) + "o"

        new_awaiting_closure = {}
        for awaiting_col, awaiting_commit in awaiting_closure.items():
            if awaiting_commit.parents[0] == commit:
#                print "closing", awaiting_commit.message.strip(), "on column", awaiting_col
                display_string += "/ "
                awaiting_closure.pop(awaiting_col)
                if awaiting_closure:
                    for awaiting_col in awaiting_closure:
                        new_awaiting_closure[awaiting_col - 1] = awaiting_closure[awaiting_col]
            else:
                display_string += " |"

        print display_string,
        print "\t\t" + message.split("\n")[0]

#    print coord
