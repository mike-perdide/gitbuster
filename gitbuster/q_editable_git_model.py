# q_editable_git_model.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtCore import QModelIndex, Qt, QVariant, QAbstractTableModel, \
                         QDateTime, SIGNAL
from PyQt4.QtGui import QColor, QGraphicsScene
from gfbi_core.git_model import GitModel
from gfbi_core.editable_git_model import EditableGitModel
from gfbi_core import NAMES, TEXT_FIELDS, TIME_FIELDS, NOT_EDITABLE_FIELDS, \
                      ACTOR_FIELDS
from datetime import datetime
from gitbuster.q_git_model import QGitModel

class QEditableGitModel(QGitModel):

    def __init__(self, directory="."):
        """
            Initializes the git model with the repository root directory.

            :param directory:
                Root directory of the git repository.

            Non editable QGitModel can be initialized with a GitModel(to limit
            the number of GitModels).
        """
        QGitModel.__init__(self)

        # Overwrite the non editable git_model set in QGitModel.__init__
        self.git_model = EditableGitModel(directory=directory)

        self.orig_q_git_model = QGitModel(self,
                                          model=self.git_model.get_orig_model())
        self.populate()
        self._enabled_options = []
        self._scene = QGraphicsScene()

    def get_to_rewrite_count(self):
        """
            Returns the number of commits to will be rewritten. That means the
            number of commit between HEAD and the oldest modified commit.
        """
        oldest_commit_parent = str(self.git_model.oldest_modified_commit_parent())

        if oldest_commit_parent is False:
            return 0

        if oldest_commit_parent is None:
            return len(self.git_model.get_commits())

        for count, commit in enumerate(self.git_model.get_commits()):
            if commit.hexsha == oldest_commit_parent:
                return count + 1

    def setData(self, index, value, role=Qt.EditRole):
        """
            Sets the data when the model is modified (qt model method).
        """
        if index.isValid() and 0 <= index.row() < self.rowCount():
            self.git_model.set_data(index, value)

            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"),
                      index, index)
            return True
        return False

    def insertRows(self, position, rows=1, index=QModelIndex()):
        print "Inserting rows"

    def removeRows(self, position, rows=1, index=QModelIndex()):
        print "Removing rows"
        return True

    def _data_background(self, index, field_name):
        commits = self.git_model.get_commits()
        commit = commits[index.row()]

        modifications = self.git_model.get_modifications()
        if commit in modifications and field_name in modifications[commit]:
            return QVariant(QColor(Qt.yellow))
        else:
            return QGitModel._data_background(self, index, field_name)

    def flags(self, index):
        """
            Returns the flags for the given index.
        """
        if not index.isValid():
            return Qt.ItemIsEnabled

        column = index.column()
        field_name = self.git_model.get_columns()[column]

        if field_name in NOT_EDITABLE_FIELDS:
            return Qt.ItemFlags(QAbstractTableModel.flags(self, index)|
                                Qt.NoItemFlags)
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index)|
                            Qt.ItemIsEditable)

    def get_git_model(self):
        "Returns the editable git_model."
        return self.git_model

    def get_orig_git_model(self):
        "Returns the original git_model."
        return self.git_model.get_orig_model()

    def get_orig_q_git_model(self):
        "Returns the original q_git_model."
        return self.orig_q_git_model

    # Beyond this point, abandon all hope of seeing anything more than "proxying
    # methods" (for instance, progress() calls git_model.progress())
    def progress(self):
        "See GitModel for more help."
        return self.git_model.progress()

    def setMerge(self, merge_state):
        "See GitModel for more help."
        self.git_model.set_merge(merge_state)

    def write(self, log, script):
        "See GitModel for more help."
        self.git_model.write(log, script)

    def is_finished_writing(self):
        "See GitModel for more help."
        return self.git_model.is_finished_writing()

    def get_modified_count(self):
        "See GitModel for more help."
        return len(self.git_model.get_modifications())

    def reorder_commits(self, dates, time, weekdays):
        "See GitModel for more help."
        self.git_model.reorder_commits(dates, time,
                                       weekdays)
        self.reset()

    def add_commit_item(self, commit):
        """
            Adds a commit item to the scene and connects the correct signals.
        """
        commit_item = CommitItem(commit, self)
        self.scene.addItem(commit_item)
        commit_item.moveBy(COLUMN_X_OFFSET, 0)

        self.connect(commit_item,
                     SIGNAL("commitItemInserted(QString*)"),
                     self.item_inserted)

        return commit_item

    def item_inserted(self, inserted_commit_hash):
        """
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
