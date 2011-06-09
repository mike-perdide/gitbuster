# branch_name_dialog.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from PyQt4.QtGui import QDialog
from PyQt4.QtCore import QString, SIGNAL
from gitbuster.branch_name_dialog_ui import Ui_Dialog

from gfbi_core.validation import validate_branch_name

RED = QString("background-color: red")
WHITE = QString("background-color: white")

class BranchNameDialog(QDialog):

    def __init__(self, parent):
        QDialog.__init__(self, parent)

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)

        self.connect_signals()

    def connect_signals(self):
        self.connect(self._ui.nameLineEdit,
                     SIGNAL("textChanged (const QString&)"),
                     self.check_name)

    def check_name(self, potential_name):
        try:
            validate_branch_name(potential_name)
            self._ui.nameLineEdit.setStyleSheet(WHITE)
        except ValueError:
            self._ui.nameLineEdit.setStyleSheet(RED)

    def get_new_name(self):
        return str(self._ui.nameLineEdit.text())

    def accept(self):
        try:
            validate_branch_name(self._ui.nameLineEdit.text())
            QDialog.accept(self)
        except ValueError:
            pass
