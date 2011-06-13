from gfbi_core.util import Index
from gfbi_core.editable_git_model import EditableGitModel


class ModelGrapher:

    def __init__(self, model):
        self._model = model
        self._parents_index = model.get_columns().index("parents")

    def preprocess_commits(self, model):
        head_commit = model.get_commits()[0]

        preprocessed = []
        self.prep_commit(head_commit, preprocessed)
        return preprocessed

    def prep_commit(self, commit, preprocessed, col=0):
        existing_row = [item for item in preprocessed
                        if item and item[1] == commit]
        if existing_row:
            preprocessed[preprocessed.index(existing_row[0])] = None
        preprocessed.append((col, commit))

        row = self._model.row_of(commit)
        parents = self._model.data(Index(row, self._parents_index))

        if len(parents) != 1:
            newcol = col + 1
        else:
            newcol = col

        for _commit in reversed(parents):
            self.prep_commit(_commit, preprocessed, newcol)
            newcol -= 1

    def graph_model(self):
        preprocessed = self.preprocess_commits(self._model)

        awaiting_closure = {}
        column = 0
        commit = None
        message_column = self._model.get_columns().index("message")
        for coord in preprocessed:
            if coord:
                if coord[0] < column:
                    awaiting_closure[column] = commit
                column = coord[0]
                commit = coord[1]
                row = self._model.row_of(commit)
                message = self._model.data(Index(row, message_column))
                display_string = "| " * (column) + "o"

                new_awaiting_closure = {}
                for awaiting_col, awaiting_commit in awaiting_closure.items():
                    if awaiting_commit.parents[0] == commit:
                        display_string += "/ "
                        awaiting_closure.pop(awaiting_col)
                        if awaiting_closure:
                            for awaiting_col in awaiting_closure:
                                _com = awaiting_closure[awaiting_col]
                                new_awaiting_closure[awaiting_col - 1] = _com
                    else:
                        display_string += " |"

                print display_string,
                print "\t\t" + message.split("\n")[0]

if __name__ == "__main__":
    ModelGrapher(EditableGitModel("/tmp/tests_git")).graph_model()
