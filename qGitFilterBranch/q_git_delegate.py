from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qGitFilter.git_model import TEXT_FIELDS, TIME_FIELDS, ACTOR_FIELDS

class QGitDelegate(QItemDelegate):

    def __init__(self):
        QItemDelegate.__init__(self, None)

    def createEditor(self, parent, option, index):
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

    def commitAndCloseEditor(self):
        editor = self.sender()
        if isinstance(editor, (QTextEdit, QLineEdit)):
            self.emit(SIGNAL("commitData(QWidget*)"), editor)
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

    def setModelData(self, editor, model, index):
        model = index.model()
        columns = model.get_git_model().get_columns()
        field_name = columns[index.column()]

        if field_name in TEXT_FIELDS:
            model.setData(index, str(editor.toPlainText()))
        elif field_name in TIME_FIELDS:
            model.setData(index, editor.dateTime().toTime_t())
        elif field_name in ACTOR_FIELDS:
            value = str(editor.text())

            if model.is_enabled("display_email"):
                try:
                    name = value.split(' <')[0]
                    email = value.split(' <')[1].split('>')[0]
                except:
                    name = ""
                    email = ""
                finally:
                    if name != "" and email != "":
                        model.setData(index, (name, email))
            else:
                orig_name, orig_email = model.get_git_model().data(index)
                name = value
                model.setData(index, (name, orig_email))

