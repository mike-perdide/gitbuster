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
        self._solutions = {}
        self._current_path = ""
        self._radio_choices = {self._ui.deleteRadioButton       : "delete",
                               self._ui.addRadioButton          : "add",
                               self._ui.addCustomRadioButton    : "add_custom"}

        self._u_files = model.get_unmerged_files()
        self._model = model
        u_files = self._u_files

        for status in [u_info["git_status"] for u_info in u_files.values()]:

            status_item = QTreeWidgetItem(self._ui.treeWidget)
            status_item.setText(0, QString(GIT_STATUSES[status]))
            status_item.setExpanded(True)

            for u_path in [u_path for u_path in u_files
                           if u_files[u_path]["git_status"] == status]:
                file_item = QTreeWidgetItem(status_item)
                file_item.setText(0, QString(u_path))
                self.tree_items[file_item] = u_path

        self.connect_signals()

        # Hide every widget of the conflict details layout.
        self.show_all_details(False)

    def connect_signals(self):
        connect(self._ui.treeWidget,
                SIGNAL("itemClicked(QTreeWidgetItem *, int)"),
                self.item_clicked)

        for button in self._radio_choices:
            connect(button, SIGNAL("clicked()"), self.radio_button_clicked)

        # Hide every widget of the conflict details layout.
        self.show_all_details(False)

        connect(self._ui.applySolutionsButton, SIGNAL("clicked()"),
                self.apply_solutions)

    def show_all_details(self, show):
        conDetLayout = self._ui.conflictDetailsGridLayout

        for item_id in xrange(conDetLayout.count()):
            conDetLayout.itemAt(item_id).widget().setVisible(show)

        # The none radio button should always be hidden.
        self._ui.noneRadioButton.hide()

    def radio_button_clicked(self):
        if self.sender() == self._ui.addCustomRadioButton:
            self._ui.conflictTextEdit.setEnabled(True)
        else:
            self._ui.conflictTextEdit.setEnabled(False)

    def set_choice(self):
        """
            When called, this method uses the current path and the radio buttons
            to find out what choice must be saved.
        """
        checked_radios = [radio for radio in self._radio_choices
                          if radio.isChecked()]
        assert len(checked_radios) < 2, \
                "There should not be more than one checked radio button."

        if checked_radios:
            choice = self._radio_choices[checked_radios[0]]
            custom_content = ""
            if choice == "add_custom":
                custom_content = str(self._ui.conflictTextEdit.toPlainText())

            self._solutions[self._current_path] = (choice, custom_content)

    def item_clicked(self, item, column):
        """
            When a QTreeWidgetItem is clicked, display the details of the
            related unmerged file.

            :param item:
                The clicked QTreeWidgetItem.

            :param column:
                The clicked column (unused).
        """
        # Before changing the item, store the solutions if the user made some
        self.set_choice()

        if item.childCount():
            # This is a top level item (a git status item)
            # Hide every widget of the conflict details layout.
            self.show_all_details(False)
        else:
            # This is a file item
            # Show every widget of the conflict details layout.
            self.show_all_details(True)

            u_path = self.tree_items[item]
            self._current_path = u_path
            self._ui.filepathLabel.setText(QString(u_path))

            # Reset the solution radio buttons
            for radio in self._radio_choices:
                self._ui.noneRadioButton.setChecked(True)

            # If the user already chose a solution, check the right radio button
            if u_path in self._solutions:
                pre_choice = self._solutions[u_path][0]
                for radio, choice in self._radio_choices.items():
                    if pre_choice == choice:
                        radio.setChecked(True)

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

    def apply_solutions(self):
        """
            When the "Apply solutions" button is clicked, check that all
            conflicts have been marked as resolved, and pass it on to
            the model.
        """
        # Saved the current path edited
        self.set_choice()

        all_solved = True
        for u_file in self._u_files:
            tree_item = [item for item in self.tree_items
                         if self.tree_items[item] == u_file][0]

            if u_file not in self._solutions:
                all_solved = False
                tree_item.setBackgroundColor(0, Qt.red)
            else:
                tree_item.setBackgroundColor(0, Qt.transparent)

        if all_solved:
            self._model.set_conflict_solutions(self._solutions)
            self._model.write(True, True)
            self.accept()
