from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qGitFilter.git_model import TEXT_FIELDS, TIME_FIELDS, ACTOR_FIELDS

class QGitDelegate(QItemDelegate):

    def __init__(self):
        QItemDelegate.__init__(self, None)

    def createEditor(self, parent, option, index):
        columns = index.model().get_git_model().get_columns()
        field_name = columns[index.column()]

        if field_name in TEXT_FIELDS or field_name in ACTOR_FIELDS:
            editor = QTextEdit(parent)
        elif field_name in TIME_FIELDS:
            editor = QDateTimeEdit(parent)
        else:
            return QItemDelegate.createEditor(self, parent, option,
                                              index)
        self.connect(editor, SIGNAL("returnPressed()"),
                     self.commitAndCloseEditor)
        return editor

    def commitAndCloseEditor(self):
        editor = self.sender()
        if isinstance(editor, (QTextEdit, QLineEdit)):
            self.emit(SIGNAL("commitData(QWidget*)"), editor)
            self.emit(SIGNAL("closeEditor(QWidget*)"), editor)

    def setEditorData(self, editor, index):
        print "Setting editor data"
        columns = index.model().get_git_model().get_columns()
        field_name = columns[index.column()]

        if field_name in TEXT_FIELDS or field_name in ACTOR_FIELDS:
            text = index.model().data(index, Qt.EditRole).toString()
            editor.setText(text)

    def setModelData(self, editor, model, index):
        pass

