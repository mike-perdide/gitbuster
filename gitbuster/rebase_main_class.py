# rebase_main_class.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from PyQt4.QtCore import QObject, Qt, SIGNAL
from PyQt4.QtGui import QApplication, QCheckBox, QGridLayout, QKeySequence,\
     QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QShortcut, QTableView,\
     QWidget, QFont
connect = QObject.connect

from gitbuster.branch_name_dialog import BranchNameDialog
from gitbuster.conflicts_dialog import ConflictsDialog
from gitbuster.util import SetNameAction, DummyRemoveAction
from gitbuster.branch_view import BranchView


class RebaseMainClass(QWidget):

    def __init__(self, parent, directory, models):
        QWidget.__init__(self, parent)

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
            checkbox_layout.removeItem(item)

        view_layout = self._ui.branchCheckboxLayout
        for item in [view_layout.itemAt(id)
                     for id in xrange(view_layout.count())]:
            item.widget().hide()
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
        self._ui.branchCheckboxLayout.addWidget(checkbox, position/2,
                                                       position%2, 1, 1)

        branch_view = BranchView(self, model, checkbox, self._models)
        branch_view.setModel(model)
        self._ui.viewLayout.addWidget(branch_view, 0, self._number_of_models)

        signals = "activated(const QModelIndex&)", "clicked(const QModelIndex&)"
        for signal in signals:
            connect(branch_view, SIGNAL(signal), self.commit_clicked)

        if hasattr(branch, 'path') and branch == self._parent.current_branch:
            checkbox.setCheckState(Qt.Checked)
        else:
            branch_view.hide()

        connect(checkbox, SIGNAL("stateChanged(int)"), self.checkbox_clicked)

        self._checkboxes[checkbox] = (branch_view, model)
        self._number_of_models += 1

    def add_new_model(self, model):
        """
            Add a new model to this tab.
        """
        self.create_model_interface(model)
        checkbox = [checkbox for checkbox in self._checkboxes
                    if self._checkboxes[checkbox][2] == model][0]
        checkbox.setCheckState(Qt.Checked)

    def focused_branch_view(self):
        """
            Returns the branch_view that has the focus.
        """
        for branch_view, model in self._checkboxes.values():
            if branch_view.hasFocus():
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
            'hexsha' :          self._ui.hexshaHolderLabel,
            'authored_date' :   self._ui.authoredDateHolderLabel,
            'committed_date' :  self._ui.commitDateHolderLabel,
            'author_name' :     self._ui.authorHolderLabel,
            'committer_name' :  self._ui.committerHolderLabel,
            'message' :         self._ui.messageHolderTextEdit
        }

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
            name, branch_view, model = info
            if model.is_fake_model():
                name.hide()
                branch_view.hide()
                checkbox.setEnabled(False)

    def show_fake_models(self):
        """
            Show all fake models.
        """
        for checkbox, info in self._checkboxes.items():
            name, branch_view, model = info
            if model.is_fake_model():
                if checkbox.isChecked():
                    name.show()
                    branch_view.show()
                checkbox.setEnabled(True)

    def toggle_modifications(self, show_modifications):
        """
            When the toggleModifications button is pressed, change the displayed
            model.
        """
        for label, branch_view, model in self._checkboxes.values():
            if show_modifications:
                branch_view.hide_modifications()
                self.show_fake_models()
            else:
                self.hide_fake_models()
                branch_view.show_modifications()

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
            print "applying with solutions"
            self._parent.apply_models([model,], None, None)

    def apply_finished(self, rebuild_fakes):
        """
            This method is called when the apply is finished.
            Some fake models may have been rebuild, we have to reset them on
            the views.
        """
        for view, model in self._checkboxes.values():
#            name_widget.reset_displayed_name()
            view.reset_displayed_name()

            if model in rebuild_fakes:
                view.set_model(model)
                QObject.connect(view, SIGNAL("activated(const QModelIndex&)"),
                                self.commit_clicked)
                QObject.connect(view, SIGNAL("clicked(const QModelIndex&)"),
                                self.commit_clicked)

                QObject.connect(view,
                            SIGNAL("customContextMenuRequested(const QPoint&)"),
                            self.context_menu)

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
