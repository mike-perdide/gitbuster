# branch_name_dialog.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QDialog, QCheckBox, QApplication, QLabel
from PyQt4.QtCore import QString, Qt
from gitbuster.branch_name_dialog_ui import Ui_Dialog


class BranchNameDialog(QDialog):

    def __init__(self, models):
        QDialog.__init__(self)

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)

    def get_new_name(self):
        return msgBox.nameLineEdit.text().toString()
