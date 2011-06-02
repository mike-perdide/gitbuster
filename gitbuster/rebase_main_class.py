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

from gitbuster.branch_name_dialog import BranchNameDialog
from gitbuster.conflicts_dialog import ConflictsDialog
from gitbuster.util import SetNameAction, DummyRemoveAction


class ButtonLineEdit(QWidget):
    """
    This widget provides a button that displays a changeable text,
    and the text can be edited in place thanks to a lineedit
    """

    def __init__(self, history_mgr, model, checkbox, parent=None):
        QWidget.__init__(self, parent)

        #data stored here for convenience
        self.history_mgr = history_mgr
        self.model = model
        self.new_name = model.get_old_branch_name()
        self.checkbox = checkbox

        #widgets. Maybe we should use designer here.
        name_label_font = QFont()
        name_label_font.setBold(True)
        self.current_name_label = QLabel(self)
        self.current_name_label.setMinimumHeight(23)
        self.current_name_label.setToolTip("Branch name. Click to change.")
        self.current_name_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.current_name_label.setFont(name_label_font)
        self.label = QLabel()
        self.editor = QLineEdit(self)
        self.valid_button = QPushButton("Ok")
        #layout
        self.box = QGridLayout(self)
        self.box.addWidget(self.current_name_label, 0, 0, 1, 3)
        self.box.addWidget(self.label, 1, 0, 1, 1)
        self.box.addWidget(self.editor, 1, 1, 1, 1)
        self.box.addWidget(self.valid_button, 1, 2, 1, 1)

        #initial state of the widget
        self._readmode()

        #initial load of data
        branch = self.model.get_current_branch() or self.model.get_remote_ref()
        self.current_name_label.setText(branch.name)

        #make it live
        QObject.connect(self.current_name_label,
                        SIGNAL("customContextMenuRequested(const QPoint&)"),
                        self.context_menu)
        QObject.connect(self.editor, SIGNAL("returnPressed()"), self.go_read)
        QObject.connect(self.valid_button, SIGNAL("clicked()"), self.go_read)

    def _iter_widgets(self):
        """
        yields widgets and their belonging to edit (True) or read (False) mode
        """
        yield self.valid_button, True
        yield self.editor, True
        yield self.label, True
        yield self.current_name_label, False

    def _editmode(self):
        for widget, is_edit in self._iter_widgets():
            widget.setVisible(is_edit)

    def go_edit(self):
        self._editmode()
        name = self.model.get_current_branch().name
        self.label.setText(u"<span>"
            "Change &#147;<i>%(name)s</i>&#148; into"
            "</span>" %
            {'name': name})
        self.editor.setText(self.new_name or name)

    def _readmode(self):
        for widget, is_edit in self._iter_widgets():
            widget.setVisible(not is_edit)

    def go_read(self):
        old_name = self.new_name
        new_name = unicode(self.editor.text()).strip()
        old_branch_name = self.model.get_old_branch_name()

        if self.new_name == new_name:
            # The name hasn't changed.
            self._readmode()
            return

        valid_name, error = self.model.is_valid_branch_name(new_name)

        if not valid_name:
            # The branch name isn't valid.
            QMessageBox.warning(self, "Naming error", error.args[0])
            return

        # The branch name is valid.
        self.new_name = new_name

        # Setting the new branch name on the model and creating history events
        self.model.start_history_event()
        self.model.set_new_branch_name(new_name)
        action = SetNameAction(old_name, new_name,
                               self.checkbox,
                               self.current_name_label,
                               old_branch_name)
        self.history_mgr.add_history_action(action)

        # Displaying the new branch name
        if new_name != old_branch_name:
            self.current_name_label.setText(new_name + "  (new name)")
        else:
            self.current_name_label.setText(new_name)
        self.checkbox.setText(new_name)

        self._readmode()

    def context_menu(self, q_point):
        """
            Creates a menu with the actions:
                - edit
                - delete (not implemented yet)
                - copy to new branch (not implemented yet)
        """
        menu = QMenu(self)
        edit_action = menu.addAction("edit")

        choosed_action = menu.exec_(self.sender().mapToGlobal(q_point))

        if choosed_action == edit_action:
            self.go_edit()

    def reset_displayed_name(self):
        """
            When the apply is finished, we may want to check that the model's
            branch name is not new anymore.
        """
        branch = self.model.get_current_branch() or self.model.get_remote_ref()
        self.current_name_label.setText(branch.name)


class RebaseMainClass(QObject):

    def __init__(self, parent, directory, models):
        QObject.__init__(self, parent)

        self.parent = parent
        self._models = None
        self._clicked_commit = None
        self._copy_data = ""
        self._oldtext = ""

        self._ui = self.parent._ui

        self._checkboxes = {}
        self._number_of_models = 0

        self.reset_interface(models)

        shortcut = QShortcut(QKeySequence(QKeySequence.Delete), parent)
        QObject.connect(shortcut, SIGNAL("activated()"), self.remove_rows)

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

        branch_view = QTableView(self.parent)
        branch_view.setModel(model)

        show_fields = ("hexsha", "message")
        for column, field in enumerate(model.get_columns()):
            if not field in show_fields:
                branch_view.hideColumn(column)

        branch_view.resizeColumnsToContents()
        branch_view.horizontalHeader().setStretchLastSection(True)
        branch_view.setSelectionMode(branch_view.ExtendedSelection)
        branch_view.setDragDropMode(branch_view.DragDrop)
        branch_view.setSelectionBehavior(branch_view.SelectRows)
        branch_view.setEditTriggers(branch_view.NoEditTriggers)
        branch_view.setContextMenuPolicy(Qt.CustomContextMenu)

        QObject.connect(branch_view,
                        SIGNAL("activated(const QModelIndex&)"),
                        self.commit_clicked)
        QObject.connect(branch_view,
                        SIGNAL("clicked(const QModelIndex&)"),
                        self.commit_clicked)

        QObject.connect(branch_view,
                        SIGNAL("customContextMenuRequested(const QPoint&)"),
                        self.context_menu)

        name = ButtonLineEdit(self.parent, model, checkbox)
        place = position * 7

        self._ui.viewLayout.addWidget(name, 0, place)
        self._ui.viewLayout.addWidget(branch_view, 1, place)

        if hasattr(branch, 'path') and branch == self.parent.current_branch:
            checkbox.setCheckState(Qt.Checked)
        else:
            branch_view.hide()
            name.hide()

        self._checkboxes[checkbox] = (name, branch_view, model)
        QObject.connect(checkbox,
                        SIGNAL("stateChanged(int)"),
                        self.checkbox_clicked)
        self._number_of_models += 1

    def context_menu(self, q_point):
        """
            Creates a menu with the actions:
                - copy
                - delete
                - paste after
                - paste before
        """
        menu = QMenu(self.parent)
        branch_view = self.sender()

        indexes = branch_view.selectedIndexes()
        selected_rows = set([index.row() for index in indexes])

        copy_action = menu.addAction("Copy")
        delete_action = menu.addAction("Delete")
        paste_after_action = menu.addAction("Paste after")
        paste_after_action.setDisabled(self._copy_data == "")
        paste_before_action = menu.addAction("Paste before")
        paste_before_action.setDisabled(self._copy_data == "")
        create_branch_action = menu.addAction("Create branch from this commit")

        choosed_action = menu.exec_(branch_view.viewport().mapToGlobal(q_point))

        if choosed_action == delete_action:
            self.remove_rows()

        elif choosed_action == copy_action:
            self._copy_data = branch_view.model().mimeData(indexes)

        elif choosed_action == paste_after_action:
            drop_after = max(selected_rows) + 1
            branch_view.model().dropMimeData(self._copy_data, Qt.CopyAction,
                                             drop_after, 0, self.parent)

        elif choosed_action == paste_before_action:
            drop_before = min(selected_rows)
            branch_view.model().dropMimeData(self._copy_data, Qt.CopyAction,
                                             drop_before, 0, self.parent)

        elif choosed_action == create_branch_action:
            msgBox = BranchNameDialog(self)
            ret = msgBox.exec_()

            if ret:
                new_name = msgBox.get_new_name()
                from_model = branch_view.model()
                from_row = min(selected_rows)
                from_model_row = from_model, from_row
                self.parent.create_new_branch_from_model(new_name,
                                                         from_model_row)

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
        for label, branch_view, model in self._checkboxes.values():
            if branch_view.hasFocus():
                return branch_view

    def remove_rows(self):
        """
            When <Del> is pressed, this method removes the selected rows of the
            table view.

            We delete the rows starting with the last one, in order to use the
            correct indexes.
        """
        branch_view = self.focused_branch_view()
        if branch_view is None:
            return False

        selected_indexes = [index for index in branch_view.selectedIndexes()
                            if index.isValid()]
        model = branch_view.model()

        ordered_list = []
        deleted_dummies = []
        for index in selected_indexes:
            if index.row() not in ordered_list and \
               not model.is_deleted(index) and \
               not model.is_first_commit(index):
                # Don't delete deleted or first commits.
                ordered_list.insert(0, index.row())
            if model.is_inserted_commit(index):
                deleted_dummies.append(index.row())

        if ordered_list:
            model.start_history_event()
        for dummy_row in deleted_dummies:
            # Special behaviour for inserted commits: hide them
            self.parent.add_history_action(DummyRemoveAction(dummy_row,
                                                             branch_view))
            branch_view.hideRow(dummy_row)

        for row in ordered_list:
            model.removeRows(row)

    def checkbox_clicked(self, value):
        checkbox = self.sender()
        label, branch_view, model = self._checkboxes[checkbox]
        label.setVisible(value)
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
                branch_view.setModel(model)
                self.show_fake_models()
            else:
                self.hide_fake_models()
                if hasattr(model, 'get_orig_q_git_model'):
                    branch_view.setModel(model.get_orig_q_git_model())

    def conflicts(self):
        """
            When the conflicts button is clicked, display the conflict details
            dialog.
        """
        model = self._clicked_commit.model()

        unmerged_files = model.get_unmerged_files()
        dialog = ConflictsDialog(unmerged_files, parent=self.parent)
        ret = dialog.exec_()

        if ret:
            solutions = dialog.get_solutions()
            model.set_conflict_solutions(solutions)

            # Applying with None will make the q_editable_model re-use the
            # previous parameters for log and force options.
            print "applying with solutions"
            self.parent.apply_models([model,], None, None)

    def apply_finished(self, rebuild_fakes):
        """
            This method is called when the apply is finished.
            Some fake models may have been rebuild, we have to reset them on
            the views.
        """
        for name_widget, view, model in self._checkboxes.values():
            name_widget.reset_displayed_name()

            if model in rebuild_fakes:
                view.setModel(model)
                QObject.connect(view, SIGNAL("activated(const QModelIndex&)"),
                                self.commit_clicked)
                QObject.connect(view, SIGNAL("clicked(const QModelIndex&)"),
                                self.commit_clicked)

                QObject.connect(view,
                            SIGNAL("customContextMenuRequested(const QPoint&)"),
                            self.context_menu)
