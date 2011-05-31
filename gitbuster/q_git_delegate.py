# q_git_delegate.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from PyQt4.QtCore import QDateTime, QVariant, Qt, SIGNAL, QRect
from PyQt4.QtGui import QDateTimeEdit, QItemDelegate, QLineEdit, QTextEdit
from gfbi_core import ACTOR_FIELDS, TEXT_FIELDS, TIME_FIELDS


class QGitDelegate(QItemDelegate):

    def __init__(self, view):
        QItemDelegate.__init__(self, None)
        self._view = view
        self._selected_indexes = None

    def createEditor(self, parent, option, index):
        if len(self._view.selectedIndexes()) > 1:
            self._selected_indexes = self._view.selectedIndexes()

        columns = index.model().get_git_model().get_columns()
        field_name = columns[index.column()]

        if field_name in TEXT_FIELDS:
            editor = QTextEdit(parent)
        elif field_name in ACTOR_FIELDS:
            editor = QLineEdit(parent)
        elif field_name in TIME_FIELDS:
            editor = QDateTimeEdit(parent)
            editor.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        else:
            return QItemDelegate.createEditor(self, parent, option,
                                              index)
        self.connect(editor, SIGNAL("returnPressed()"),
                     self.commitAndCloseEditor)
        return editor

    def updateEditorGeometry(self, editor, option, index):
        """
            Here we're gonna make the text edit of the message column bigger.
        """
        model = index.model()
        columns = model.get_git_model().get_columns()
        field_name = columns[index.column()]

        if field_name != "message":
            QItemDelegate.updateEditorGeometry(self, editor, option, index)
            return

        message = model.data(index, Qt.EditRole)

        new_geometry = option.rect
        new_height = 27 * message.toString().count("\n") or option.rect.height()

        new_geometry.setHeight(new_height)
        editor.setGeometry(new_geometry)

    def commitAndCloseEditor(self):
        editor = self.sender()
        if isinstance(editor, (QTextEdit, QLineEdit)):
            self.emit(SIGNAL("closeEditor(QWidget*)"), editor)

    def setEditorData(self, editor, index):
        columns = index.model().get_git_model().get_columns()
        field_name = columns[index.column()]

        if field_name in TEXT_FIELDS or field_name in ACTOR_FIELDS:
            text = index.model().data(index, Qt.EditRole).toString()
            editor.setText(text)
        elif field_name in TIME_FIELDS:
            timestamp, tz = index.model().data(index, Qt.EditRole)
            _q_datetime = QDateTime()
            _q_datetime.setTime_t(timestamp)
            editor.setDateTime(_q_datetime)

    def setModelData(self, editor, model, index, ignore_history=False):
        model = index.model()
        columns = model.get_git_model().get_columns()
        field_name = columns[index.column()]

        if field_name in TEXT_FIELDS:
            data = QVariant(editor.toPlainText())
        elif field_name in TIME_FIELDS:
            data = (editor.dateTime().toTime_t(),
                    model.data(index, Qt.EditRole)[1])
        elif field_name in ACTOR_FIELDS:
            data = QVariant(editor.text())

        if not ignore_history:
            # Start a new history event, only for the first modified index.
            # That way, an undo will undo all the selected indexes.
            model.start_history_event()

        model.setData(index, data)

        if self._selected_indexes:
            edited_column = index.column()

            selected_indexes = list(self._selected_indexes)
            self._selected_indexes = None

            for selected_index in selected_indexes:
                if selected_index.column() == edited_column:
                    self.setModelData(editor, model, selected_index,
                                      ignore_history=True)
