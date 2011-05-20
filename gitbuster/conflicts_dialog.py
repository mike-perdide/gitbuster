# conflicts_dialog.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QDialog, QTreeWidgetItem
from PyQt4.QtCore import QString, Qt, SIGNAL, QObject
from gitbuster.conflicts_dialog_ui import Ui_Dialog

connect = QObject.connect

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

        self.tree_items = {}

        u_files = model.get_unmerged_files()
        for git_status in u_files:
            status = QTreeWidgetItem(self._ui.treeWidget)
            status.setText(0, QString(GIT_STATUSES[git_status]))

            for unmerged_info in u_files[git_status]:
                file_item = QTreeWidgetItem(status)
                path = unmerged_info[0]
                file_item.setText(0, QString(path))
                self.tree_items[file_item] = unmerged_info

        connect(self._ui.treeWidget,
                SIGNAL("itemClicked(QTreeWidgetItem *, int)"),
                self.item_clicked)

    def item_clicked(self, item, column):
        if item.childCount():
            # This is a top level item (a git status item)
            pass
        else:
            # This is a file item
            path, orig_content, tmp_file, diff = self.tree_items[item]
            self._ui.conflictTextEdit.setText(QString(open(tmp_file).read()))
            self._ui.diffTextEdit.setText(QString(diff))
            self._ui.origTextEdit.setText(QString(orig_content))
