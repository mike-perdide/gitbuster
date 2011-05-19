# conflicts_dialog.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QDialog, QTreeWidgetItem
from PyQt4.QtCore import QString, Qt
from gitbuster.conflicts_dialog_ui import Ui_Dialog

GIT_STATUSES = {
    "DD" : "both deleted",
    "AU" : "added by us",
    "UD" : "deleted by them",
    "UA" : "added by them",
    "DU" : "deleted by us",
    "AA" : "both added",
    "UU" : "both modified"
}


class ConflictsDialog(QDialog):

    def __init__(self, model):
        QDialog.__init__(self)

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)

        u_files = model.get_unmerged_files()
        for git_status in u_files:
            status = QTreeWidgetItem(self._ui.treeWidget)
            status.setText(0, QString(GIT_STATUSES[git_status]))

            for path, tmp_file in u_files[git_status]:
                file_entry = QTreeWidgetItem(status)
                file_entry.setText(0, QString(path))


