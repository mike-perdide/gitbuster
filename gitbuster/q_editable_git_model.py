# q_editable_git_model.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from PyQt4.QtCore import QAbstractTableModel, QDataStream, QIODevice, \
        QModelIndex, QString, QStringList, QVariant, Qt, SIGNAL
from PyQt4.QtGui import QColor, QFont
from gfbi_core import NOT_EDITABLE_FIELDS, TIME_FIELDS
from gfbi_core.editable_git_model import EditableGitModel
from gitbuster.q_git_model import QGitModel


DELETED_FONT = QFont("Sans Serif", italic=True)
DELETED_FONT.setStrikeOut(True)


class QEditableGitModel(QGitModel):

    def __init__(self, models_dict, directory=".", fake_branch_name="",
                 from_model_row=None, parent=None):
        """
            Initializes the git model with the repository root directory.

            :param directory:
                Root directory of the git repository.

            Non editable QGitModel can be initialized with a GitModel(to limit
            the number of GitModels).
        """
        QGitModel.__init__(self,
                           directory=directory,
                           fake_branch_name=fake_branch_name,
                           parent=parent)

        if from_model_row:
            from_model, from_row = from_model_row
            git_model = from_model.get_orig_git_model()
            from_commits = git_model.get_commits()[from_row:]
        else:
            from_commits = False

        # Overwrite the non editable git_model set in QGitModel.__init__
        self.git_model = EditableGitModel(directory=directory,
                                          fake_branch_name=fake_branch_name,
                                          from_commits=from_commits)

        self._enabled_options = []
        self._all_models_dict = models_dict

        # The following is used to store the write options
        self._previous_log_option = True
        self._previous_force_option = False

        if not fake_branch_name:
            # If this is not a fake model
            self.orig_q_git_model = QGitModel(self,
                                        parent=parent,
                                        model=self.git_model.get_orig_model())
        else:
            self.orig_q_git_model = None

    def populate(self):
        """
            This populates the model.
            We may want to build orig_q_git_model too.
        """
        QGitModel.populate(self)

    def setData(self, index, value, role=Qt.EditRole):
        """
            Sets the data when the model is modified (qt model method).
        """
        if index.isValid() and 0 <= index.row() < self.rowCount():
            column = index.column()
            field_name = self.git_model.get_columns()[column]

            if field_name in TIME_FIELDS or field_name in ("parents", "tree", "children"):
                new_value = value
            else:
                new_value = unicode(value.toString())

            self.git_model.set_data(index, new_value)
            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"),
                      index, index)
            return True
        return False

    def insertRows(self, position, rows=1, index=QModelIndex()):
        """
            Inserts a given number of rows in the model, starting at the given
            position.
        """
        self.beginInsertRows(QModelIndex(), position, position + rows - 1)
        self.git_model.insert_rows(position, rows)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows=1, index=QModelIndex()):
        """
            Removes a given number of rows in the model, starting at the given
            position.
        """
        parents_index = self.get_columns().index("parents")

        commit_to_delete = self.git_model.get_commits()[position]
        # Storing the parents and children commits of the deleted commit.
        parents = self.git_model.c_data(commit_to_delete, "parents")
        children = self.git_model.c_data(commit_to_delete, "children")
        # They will be propagated respectively to the children and the parents
        # of the deleted commit.

        for child in children:
            row_of_child = self.git_model.row_of(child)
            new_parents = list(self.git_model.c_data(child, "parents"))
            parents_position = new_parents.index(commit_to_delete)

            # Removing only the deleted commit from the parents
            new_parents.pop(parents_position)
            for parent in parents:
                new_parents.insert(parents_position, parent)
            self.setData(self.createIndex(row_of_child, parents_index),
                         new_parents)

        children_column = self.get_columns().index("children")
        for parent in parents:
            row_of_parent = self.git_model.row_of(parent)
            new_children = list(self.git_model.c_data(parent, "children"))
            children_position = new_children.index(commit_to_delete)

            # Removing only the deleted commit from the children
            new_children.pop(children_position)
            for child in children:
                new_children.insert(children_position, child)
            self.setData(self.createIndex(row_of_parent, children_column),
                         new_children)

        self.git_model.remove_rows(position, rows)

        self.reset()
        return True

    def data(self, index, role):
        """
            Returns the data of the model.
        """
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return QVariant()

        if role == Qt.FontRole:
            return self._data_font(index)
        else:
            return QGitModel.data(self, index, role)

    def _data_font(self, index):
        """
            Returns a striked + italic font for items that were deleted.
        """
        if self.git_model.is_deleted(index):
            return DELETED_FONT

        return QVariant()

    def _data_background(self, index, field_name):
        """
            Returns a yellow background that should be displayed for the given
            index if the index is modified, or calls the QGitModel method
            instead.
        """
        commits = self.git_model.get_commits()
        commit = commits[index.row()]
        conflicting_commit = self.git_model.get_conflicting_commit()

        modifications = self.git_model.get_modifications()
        if conflicting_commit is not None and commit == conflicting_commit:
            return QVariant(QColor(Qt.red))
        elif self.git_model.is_modified(index) or self.is_fake_model():
            return QVariant(QColor(Qt.yellow))

        return QGitModel._data_background(self, index, field_name)

    def flags(self, index):
        """
            Returns the flags for the given index.
        """
        if not index.isValid():
            return Qt.ItemFlags(QAbstractTableModel.flags(self, index) |
                                Qt.ItemIsDropEnabled |
                                Qt.NoItemFlags)

        column = index.column()
        field_name = self.git_model.get_columns()[column]

        # Neither first commits nor deleted commits can be edited.
        if field_name not in NOT_EDITABLE_FIELDS and \
           not self.is_first_commit(index) and\
           not self.is_deleted(index):
            return Qt.ItemFlags(QGitModel.flags(self, index) |
                                Qt.ItemIsEditable)

        return QGitModel.flags(self, index)

    def get_git_model(self):
        "Returns the editable git_model."
        return self.git_model

    def get_orig_git_model(self):
        "Returns the original git_model."
        return self.git_model.get_orig_model()

    def get_orig_q_git_model(self):
        "Returns the original q_git_model."
        return self.orig_q_git_model

    def item_inserted(self, inserted_commit_hash):
        """
            XXX: we now use refresh_position !
            USE "Row inserted"
           If we need to insert a commit C between A and B like this:
                HEAD - B - C - A (initial commit)
            We just need to do:
                - set B as the new column end
                - set C as the below commit of B
                - set A as the below commit of C
                - call the move_at_the_column_end method on C

            See also CommitItem.move_at_the_column_end.
        """
        new_commit_item = self.add_commit_item(inserted_commit_hash)
        original_previous = self.sender().get_previous()

        new_commit_item.set_previous(original_previous)
        self.sender().set_previous(new_commit_item)

        self.sender().set_as_the_new_column_end()
        self.sender().move_at_the_column_end()

    def get_conflicting_index(self):
        """
            Returns the conflicting index.
            Here the important information is the row rather than the column.
        """
        conflicting_row = self.git_model.get_conflicting_row()
        return self.createIndex(conflicting_row, 0)

    def mimeTypes(self):
        types = QStringList()
        types.append("application/vnd.text.list")
        return types

    def dropMimeData(self, mime_data, action, row, col_unused, parent_unused,
                     filling_empty_model=False):
        if action == Qt.IgnoreAction:
            return True

        if not mime_data.hasFormat("application/vnd.text.list"):
            return False

        if not filling_empty_model and row == self.rowCount():
            # It's forbidden to insert before the first commit (last row of the
            # model).
            return False

        if row != -1:
            begin_row = row
        else:
            return False

        encoded_data = mime_data.data("application/vnd.text.list")
        stream = QDataStream(encoded_data, QIODevice.ReadOnly)
        new_items = []
        rows = 0

        while not stream.atEnd():
            text = stream.readQString()
            item_branch, item_row_s = str(text).split(' ')

            new_items.append([int(item_row_s),])
            rows += 1

        # Now new_items contains 1 element lists with the row of the inserted
        # commit. We will complete these lists with the actual Commit object.
        # item_branch contains the name of the branch.

        for (branch, model) in self._all_models_dict.items():
            if branch.name == item_branch:
                item_model = model

        # We're going to store the data to be inserted in a dictionnary before
        # inserting the rows. This is to avoid problems when copying rows from
        # a model to somewhere above in the same model. The insertion of rows
        # causes a shift of all the rows, including the ones to be copied from.
        data_to_be_inserted = {}
        insert_row = begin_row
        for item in new_items:
            item_row = item[0]

            for column, field in enumerate(self.get_columns()):
                item_index = self.createIndex(item_row, column)
                data = item_model.data(item_index, Qt.EditRole)
                data_to_be_inserted[(insert_row, column)] = data

            insert_row += 1

        self.start_history_event()

        parents_col = self.get_columns().index("parents")
        children_col = self.get_columns().index("children")

        _row = begin_row
        for item in new_items:
            replaced_row = _row
            replaced_index = self.createIndex(replaced_row, 0)
            while self.is_deleted(replaced_index):
                replaced_row += 1
                replaced_index = self.createIndex(replaced_row, 0)
            replaced_commit = self.git_model.get_commits()[replaced_index.row()]

            new_parents = [replaced_commit,]
            new_children = list(self.git_model.c_data(replaced_commit,
                                                      "children"))

            self.insertRows(_row, 1, QModelIndex())

            for column, field in enumerate(self.get_columns()):
                index = self.createIndex(_row, column)
                self.setData(index, data_to_be_inserted[(_row, column)])

            self.setData(self.createIndex(_row, children_col), new_children)
            self.setData(self.createIndex(_row, parents_col), [replaced_commit,])

            this_commit = self.git_model.get_commits()[_row]
            # Updating parent's children and children parent's
            for child in new_children:
                row_of_child = self.git_model.row_of(child)
                _parents = list(self.git_model.c_data(child, "parents"))
                parents_position = _parents.index(replaced_commit)

                # Removing only the replaced commit from the parents
                _parents.pop(parents_position)
                _parents.insert(parents_position, this_commit)
                self.setData(self.createIndex(row_of_child, parents_col),
                             _parents)

            for parent in new_parents:
                row_of_parent = self.git_model.row_of(parent)
                self.setData(self.createIndex(row_of_parent, children_col),
                             [this_commit,])

            _row += 1

        self.reset()

        return True

    def name_to_display(self):
        """
            Returns the name that should be displayed for this model.
            It can be the name of the current branch, the name of the remote
            reference, or the new branch name.
        """
        return self.get_new_branch_name() or QGitModel.name_to_display(self)

    def should_be_written(self):
        """
            Returns True if the model is a fake model, or if there are
            modifications in the commits, or if the name is modified.
        """
        return (self.is_fake_model() or
                self.get_modified_count() > 0 or
                self.get_deleted_count() > 0 or
                self.is_name_modified())

    # Beyond this point, abandon all hope of seeing anything more than
    # "proxying methods" (for instance, progress() calls git_model.progress())
    def is_name_modified(self):
        "See GitModel for more help."
        return self.git_model.is_name_modified()

    def progress(self):
        "See GitModel for more help."
        return self.git_model.progress()

    def setMerge(self, merge_state):
        "See GitModel for more help."
        self.git_model.set_merge(merge_state)

    def write(self, log, force_committed_date, dont_populate=True):
        "See GitModel for more help."
        if log is None:
            log = self._previous_log_option
        else:
            self._previous_log_option = log

        if force_committed_date is None:
            force_committed_date = self._previous_force_option
        else:
            self._previous_force_option = force_committed_date

        self.git_model.write(log, force_committed_date, dont_populate)

    def is_write_success(self):
        "See GitModel for more help."
        return self.git_model.is_write_success()

    def is_finished_writing(self):
        "See GitModel for more help."
        return self.git_model.is_finished_writing()

    def get_modified_count(self):
        "See GitModel for more help."
        return self.git_model.get_modified_count()

    def get_deleted_count(self):
        "See GitModel for more help."
        return self.git_model.get_deleted_count()

    def is_deleted(self, index):
        "See GitModel for more help."
        return self.git_model.is_deleted(index)

    def is_inserted_commit(self, index):
        "See GitModel for more help."
        return self.git_model.is_inserted_commit(index)

    def is_fake_model(self):
        "See GitModel for more help."
        return self.git_model.is_fake_model()

    def reorder_commits(self, dates, time, weekdays):
        "See GitModel for more help."
        self.start_history_event()
        self.git_model.reorder_commits(dates, time,
                                       weekdays)
        self.reset()

    def get_to_rewrite_count(self):
        "See GitModel for more help."
        return self.git_model.get_to_rewrite_count()

    def start_history_event(self):
        "See GitModel for more help."
        self.git_model.start_history_event()
        # Here we inform the main window to start a new history event
        self.emit(SIGNAL("newHistoryEvent"))

    def undo_history(self):
        "See GitModel for more help."
        self.git_model.undo_history()
        self.reset()

    def redo_history(self):
        "See GitModel for more help."
        self.git_model.redo_history()
        self.reset()

    def is_conflicting_commit(self, row):
        "See GitModel for more help."
        return self.git_model.is_conflicting_commit(row)

    def get_unmerged_files(self):
        "See GitModel for more help."
        return self.git_model.get_unmerged_files()

    def set_conflict_solutions(self, solutions):
        "See GitModel for more help."
        return self.git_model.set_conflict_solutions(solutions)

    def is_valid_branch_name(self, name):
        "See GitModel for more help."
        return self.git_model.is_valid_branch_name(name)

    def set_new_branch_name(self, name):
        "See GitModel for more help."
        new_name = self.git_model.set_new_branch_name(name)
        return new_name

    def get_new_branch_name(self):
        "See GitModel for more help."
        return self.git_model.get_new_branch_name()

    def write_errors(self):
        "See GitModel for more help."
        return self.git_model.write_errors()
