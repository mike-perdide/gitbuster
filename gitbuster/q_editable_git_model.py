# q_editable_git_model.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtCore import QModelIndex, Qt, QVariant, QAbstractTableModel, \
                         QDateTime, SIGNAL, QMimeData, QByteArray, \
                         QDataStream, QIODevice, QStringList, QString
from PyQt4.QtGui import QColor, QGraphicsScene
from gfbi_core.git_model import GitModel
from gfbi_core.editable_git_model import EditableGitModel
from gfbi_core import NAMES, TEXT_FIELDS, TIME_FIELDS, NOT_EDITABLE_FIELDS, \
                      ACTOR_FIELDS
from datetime import datetime
from gitbuster.q_git_model import QGitModel

class QEditableGitModel(QGitModel):

    def __init__(self, directory=".", models_dict=[]):
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
        self._enabled_options = []
        self._scene = QGraphicsScene()

        self._all_models_dict = models_dict

    def add_commit_item(self, commit, next_commit_item):
        """
            Adds a commit item to the scene and connects the correct signals.
        """
        commit_item = QGitModel.add_commit_item(self, commit, next_commit_item)

        self.connect(commit_item,
                     SIGNAL("commitItemInserted(QString*)"),
                     self.item_inserted)

        return commit_item

    def setData(self, index, value, role=Qt.EditRole):
        """
            Sets the data when the model is modified (qt model method).
        """
        if index.isValid() and 0 <= index.row() < self.rowCount():
            column = index.column()
            field_name = self.git_model.get_columns()[column]

            if field_name in TIME_FIELDS:
                new_value = value
            else:
                new_value = unicode(value.toString())

            self.git_model.set_data(index, new_value)
            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"),
                      index, index)
            return True
        return False

    def insertRows(self, position, rows=1, index=QModelIndex()):
        self.beginInsertRows(QModelIndex(), position, position + rows - 1)
        self.git_model.insert_rows(position, rows)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows=1, index=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
        self.git_model.remove_rows(position, rows)
        self.endRemoveRows()
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
            return Qt.ItemFlags(QAbstractTableModel.flags(self, index)|
                                Qt.ItemIsDropEnabled|
                                Qt.NoItemFlags)

        column = index.column()
        field_name = self.git_model.get_columns()[column]

        if field_name in NOT_EDITABLE_FIELDS:
            return Qt.ItemFlags(QAbstractTableModel.flags(self, index)|
                                Qt.ItemIsDragEnabled|
                                Qt.NoItemFlags)
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index)|
                            Qt.ItemIsDragEnabled|
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

    def get_to_rewrite_count(self):
        "See GitModel for more help."
        return self.git_model.get_to_rewrite_count()


    def mimeTypes(self):
        types = QStringList()
        types.append("application/vnd.text.list")
        return types

    def mimeData(self, indexes):
        mime_data = QMimeData()
        encoded_data = QByteArray()

        stream = QDataStream(encoded_data, QIODevice.WriteOnly)

        for index in indexes:
            if index.isValid() and index.column() == 0:
                text = QString(str(self.get_current_branch()) + " ")
                text += QString(str(index.row()))
                stream.writeQString(text)

        mime_data.setData("application/vnd.text.list", encoded_data)
        return mime_data

    def dropMimeData(self, mime_data, action, row, column, parent):
        if action == Qt.IgnoreAction:
            return True

        if not mime_data.hasFormat("application/vnd.text.list"):
            return False

        if row == self.rowCount():
            # It's forbidden to insert before the first commit (last row of the
            # model).
            return False

        if row != -1:
            begin_row = row
        else:
            return False

        encoded_data = mime_data.data("application/vnd.text.list")
        stream = QDataStream(encoded_data, QIODevice.ReadOnly)
        new_items = QStringList()
        rows = 0

        while not stream.atEnd():
            text = stream.readQString()
            new_items.append(text)
            rows += 1

        self.insertRows(begin_row, rows, QModelIndex())
        insert_row = begin_row

        for item in new_items:
            item_branch, item_row_s = str(item).split(' ')
            item_row = int(item_row_s)

            for (branch, model) in self._all_models_dict.items():
                if branch.name == item_branch:
                    item_model = model

            for column, field in enumerate(self.get_columns()):
                item_index = self.index(item_row, column, QModelIndex())
                data = item_model.data(item_index, Qt.EditRole)

                index = self.index(insert_row, column, QModelIndex())
                self.setData(index, data)

            insert_row += 1

        return True
