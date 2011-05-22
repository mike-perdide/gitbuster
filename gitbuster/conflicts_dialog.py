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

        self._u_files = model.get_unmerged_files()
        u_files = self._u_files

        for status in [u_info["git_status"] for u_info in u_files.values()]:
            status_item = QTreeWidgetItem(self._ui.treeWidget)
            status_item.setText(0, QString(GIT_STATUSES[status]))

            for u_path in [u_path for u_path in u_files
                           if u_files[u_path]["git_status"] == status]:
                file_item = QTreeWidgetItem(status_item)
                file_item.setText(0, QString(u_path))
                self.tree_items[file_item] = u_path

        connect(self._ui.treeWidget,
                SIGNAL("itemClicked(QTreeWidgetItem *, int)"),
                self.item_clicked)

        self._radio_choices = {self._ui.deleteRadioButton       : "delete",
                               self._ui.addRadioButton          : "add",
                               self._ui.addCustomRadioButton    : "add_custom"}
        for button in self._radio_choices:
            connect(button, SIGNAL("clicked()"), self.radio_button_clicked)

        # Hide every widget of the conflict details layout.
        self.show_all_details(False)

    def show_all_details(self, show):
        conDetLayout = self._ui.conflictDetailsGridLayout

        for item_id in xrange(conDetLayout.count()):
            conDetLayout.itemAt(item_id).widget().setVisible(show)

    def radio_button_clicked(self):
        if self.sender() == self._ui.addCustomRadioButton:
            self._ui.conflictTextEdit.setEnabled(True)
        else:
            self._ui.conflictTextEdit.setEnabled(False)

    def item_clicked(self, item, column):

        if item.childCount():
            # This is a top level item (a git status item)
            # Hide every widget of the conflict details layout.
            self.show_all_details(False)
        else:
            # This is a file item
            # Show every widget of the conflict details layout.
            self.show_all_details(True)

            u_path = self.tree_items[item]
            u_info = self._u_files[u_path]
            tmp_path = u_info["tmp_path"]
            diff = u_info["diff"]
            orig_content = u_info["orig_content"]
            git_status = u_info["git_status"]

            add_available_states = ('DU', 'UD', 'UA', 'AU')
            delete_available_states = ('DD', 'DU', 'UD', 'UA', 'AU')

            if git_status in add_available_states:
                self._ui.addRadioButton.show()
            else:
                self._ui.addRadioButton.hide()

            if git_status in delete_available_states:
                self._ui.deleteRadioButton.show()
            else:
                self._ui.deleteRadioButton.hide()

            if git_status == 'DD':
                conflict_content = \
                        "<font color=#FF0000>The file isn't present after " + \
                        "the merge conflict."
                self._ui.conflictTextEdit.setText(QString(conflict_content))
                self._ui.addCustomRadioButton.hide()
            else:
                conflict_content = open(tmp_path).read()
                self._ui.conflictTextEdit.setText(QString(conflict_content))
                self._ui.addCustomRadioButton.show()

            if git_status == 'AU':
                diff_text_edit_content = \
                        "<font color=#FF0000>The file isn't present in " + \
                        "the conflicting commit tree."
                self._ui.diffTextEdit.setText(QString(diff_text_edit_content))
            else:
                self._ui.diffTextEdit.setText(QString(diff))

            if git_status in ('UA', 'DU', 'DD'):
                # The file wasn't present in the tree before the merge conflict
                orig_text_edit_content = \
                        "<font color=#FF0000>The file wasn't present in " + \
                        "the tree before the merge conflict."
                self._ui.origTextEdit.setHtml(QString(orig_text_edit_content))
            else:
                orig_text_edit_content = orig_content
                self._ui.origTextEdit.setText(QString(orig_text_edit_content))
