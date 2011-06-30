# rebase_main_class.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from PyQt4.QtCore import QObject, Qt, SIGNAL
from PyQt4.QtGui import QApplication, QCheckBox, QGridLayout, QKeySequence,\
     QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QTableView, QWidget, \
     QFont
connect = QObject.connect

from gitbuster.conflicts_dialog import ConflictsDialog
from gitbuster.util import SetNameAction, DummyRemoveAction
from gitbuster.branch_view import BranchView


class RebaseMainClass(QWidget):

    def __init__(self, parent, directory, models):
        QWidget.__init__(self, parent)
        self.hide()

        self._parent = parent
        self._models = None
        self._clicked_commit = None
        self._copy_data = ""

        self._ui = self._parent._ui

        self._checkboxes = {}
        self._number_of_models = 0

        self.reset_interface(models)

        self._ui.detailsGroupBox.hide()
        QObject.connect(self._ui.conflictsButton,
                        SIGNAL("clicked()"),
                        self.conflicts)

    def reset_interface(self, models):
        """
            Resets the rebase tab (usually after a directory change).
        """
        self._checkboxes = {}
        self._models = models
        self._number_of_models = 0

        checkbox_layout = self._ui.branchCheckboxLayout
        for item in [checkbox_layout.itemAt(id)
                     for id in xrange(checkbox_layout.count())]:
            item.widget().hide()
            item.widget().close()
            checkbox_layout.removeItem(item)

        view_layout = self._ui.viewLayout
        for item in [view_layout.itemAt(id)
                     for id in xrange(view_layout.count())]:
            item.widget().hide()
            item.widget().close()
            view_layout.removeItem(item)

        for model in self._models.values():
            self.create_model_interface(model)

    def create_model_interface(self, model):
        """
            This method sets up the interface for the model in the rebase tab.
        """
        position = self._number_of_models
        branch = model.get_current_branch() or model.get_remote_ref()

        checkbox = QCheckBox(self._ui.centralwidget)
        checkbox.setText(QApplication.translate("MainWindow",
                                            branch.name,
                                            None, QApplication.UnicodeUTF8))
        self._ui.branchCheckboxLayout.addWidget(checkbox, position / 2,
                                                       position%2, 1, 1)

        branch_view = BranchView(self, model, checkbox, self._models)
        self._ui.viewLayout.addWidget(branch_view, 0, self._number_of_models)

        signals = "activated(const QModelIndex&)", "clicked(const QModelIndex&)"
        for signal in signals:
            connect(branch_view, SIGNAL(signal), self.commit_clicked)

        connect(branch_view, SIGNAL("newBranchFromCommit"),
                self.fwd_new_branch_from_commit)
        connect(branch_view, SIGNAL("newHistAction"), self.fwd_new_hist_action)

        connect(branch_view, SIGNAL("newCopiedData"), self.set_copy_data)

        if hasattr(branch, 'path') and branch == self._parent.current_branch:
            checkbox.setCheckState(Qt.Checked)
            branch_view.show()
        else:
            branch_view.hide()

        connect(checkbox, SIGNAL("stateChanged(int)"), self.checkbox_clicked)

        self._checkboxes[checkbox] = (branch_view, model)
        self._number_of_models += 1

    def fwd_new_hist_action(self, action):
        """
            Simple signal forwarder to MainWindow.
        """
        self.emit(SIGNAL("newHistAction"), action)

    def fwd_new_branch_from_commit(self, indexes):
        """
            Simple signal forwarder to MainWindow.
        """
        self.emit(SIGNAL("newBranchFromCommit"), indexes)

    def add_new_model(self, model):
        """
            Add a new model to this tab.
        """
        self.create_model_interface(model)
        checkbox = [checkbox for checkbox in self._checkboxes
                    if self._checkboxes[checkbox][1] == model][0]
        checkbox.setCheckState(Qt.Checked)

    def remove_model(self, model):
        """
            Remove a model from this tab.
        """
        checkbox = [checkbox for checkbox in self._checkboxes
                    if self._checkboxes[checkbox][1] == model][0]

        branch_view, model = self._checkboxes[checkbox]

        view_layout = self._ui.viewLayout

        for item in [view_layout.itemAt(id)
                     for id in xrange(view_layout.count())
                     if view_layout.itemAt(id).widget() == branch_view]:
            print "Hiding", item.widget()
            item.widget().hide()
            item.widget().close()
            view_layout.removeItem(item)

    def remove_rows(self):
        """
            This forwards the remove row command to the focused branch view.
        """
        if self.focused_branch_view():
            self.focused_branch_view().remove_rows()

    def focused_branch_view(self):
        """
            Returns the branch_view that has the focus.
        """
        for branch_view, model in self._checkboxes.values():
            if branch_view.tableview_has_focus():
                return branch_view

    def checkbox_clicked(self, value):
        checkbox = self.sender()
        branch_view, model = self._checkboxes[checkbox]
        branch_view.setVisible(value)

    def commit_clicked(self, index):
        self._clicked_commit = index
        model = index.model()
        row = index.row()

        labels = {
            'hexsha':           self._ui.hexshaHolderLabel,
            'authored_date':    self._ui.authoredDateHolderLabel,
            'committed_date':   self._ui.commitDateHolderLabel,
            'author_name':      self._ui.authorHolderLabel,
            'committer_name':   self._ui.committerHolderLabel,
            'message':          self._ui.messageHolderTextEdit}

        for field in labels:
            column = model.get_columns().index(field)
            index = model.createIndex(row, column)

            if "date" in field:
                data = model.data(index, Qt.DisplayRole)
            else:
                data = model.data(index, Qt.EditRole)

            labels[field].setText(data.toString())

        if hasattr(model, 'is_conflicting_commit') and \
           model.is_conflicting_commit(index.row()):
            self._ui.conflictsButton.show()
        else:
            self._ui.conflictsButton.hide()

        self._ui.detailsGroupBox.show()

    def hide_fake_models(self):
        """
            Hide all the fake models.
        """
        for checkbox, info in self._checkboxes.items():
            branch_view, model = info
            if model.is_fake_model():
                branch_view.hide()
                checkbox.setEnabled(False)

    def show_fake_models(self):
        """
            Show all fake models.
        """
        for checkbox, info in self._checkboxes.items():
            branch_view, model = info
            if model.is_fake_model():
                if checkbox.isChecked():
                    branch_view.show()
                checkbox.setEnabled(True)

    def toggle_modifications(self, show_modifications):
        """
            When the toggleModifications button is pressed, change the displayed
            model.
        """
        for branch_view, model in self._checkboxes.values():
            if show_modifications:
                branch_view.show_modifications()
                self.show_fake_models()
            else:
                self.hide_fake_models()
                branch_view.hide_modifications()

    def conflicts(self):
        """
            When the conflicts button is clicked, display the conflict details
            dialog.
        """
        model = self._clicked_commit.model()

        unmerged_files = model.get_unmerged_files()
        dialog = ConflictsDialog(unmerged_files, parent=self._parent)
        ret = dialog.exec_()

        if ret:
            solutions = dialog.get_solutions()
            model.set_conflict_solutions(solutions)

            # Applying with None will make the q_editable_model re-use the
            # previous parameters for log and force options.
            self._parent.apply_models([model,], None, None)

    def get_copy_data(self):
        """
            Returns the copied data (mimeData of selected indexes).
        """
        return self._copy_data

    def set_copy_data(self, data):
        """
            Sets the copied data with the given mimeData.
        """
        self._copy_data = data

    def get_branch_view(self, branch_name):
        """
            This is intended for test purposes. This method returns the branch
            view widget related to the given branch name.
        """
        for branch_view, model in self._checkboxes.values():
            if model.name_to_display() == branch_name:
                return branch_view

    def add_history_action(self, action):
        """
            Forwards to the main window.
        """
        self.parent().add_history_action(action)
