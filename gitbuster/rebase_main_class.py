# rebase_main_class.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from gitbuster.branch_view_ui import Ui_BranchView
from PyQt4.QtGui import QWidget, QCheckBox, QApplication, QTableView, QLabel, \
                        QKeySequence, QShortcut, QMenu
from PyQt4.QtCore import QString, SIGNAL, Qt, QPointF, QObject, QModelIndex

from gitbuster.graphics_items import CommitItem, Arrow
from gitbuster.conflicts_dialog import ConflictsDialog


class RebaseMainClass(QObject):

    def __init__(self, parent, directory, models):
        QObject.__init__(self, parent)

        self.parent = parent
        self._models = models
        self._checkboxes = {}
        self._clicked_commit = None

        self._ui = self.parent._ui
        iter = 0

        for branch, model in models.items():
            checkbox = QCheckBox(self._ui.centralwidget)
            checkbox.setText(QApplication.translate("MainWindow",
                                                branch.name,
                                                None, QApplication.UnicodeUTF8))
            self._ui.branchCheckboxLayout.addWidget(checkbox, iter/2,
                                                           iter%2, 1, 1)

            branch_view = QTableView(parent)
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

            label = QLabel(parent)
            label.setText(branch.name)

            # Insert the view in the window's layout
            self._ui.viewLayout.addWidget(label, 0, iter)
            self._ui.viewLayout.addWidget(branch_view, 1, iter)

            iter += 1

            if branch == self.parent.current_branch:
                checkbox.setCheckState(Qt.Checked)
            else:
                branch_view.hide()
                label.hide()

            self._checkboxes[checkbox] = (label, branch_view, model)
            QObject.connect(checkbox,
                            SIGNAL("stateChanged(int)"),
                            self.checkbox_clicked)

        shortcut = QShortcut(QKeySequence(QKeySequence.Delete), parent)
        QObject.connect(shortcut, SIGNAL("activated()"), self.remove_rows)

        self._ui.detailsGroupBox.hide()
        QObject.connect(self._ui.conflictsButton,
                        SIGNAL("clicked()"),
                        self.conflicts)

    def context_menu(self, q_point):
        menu = QMenu()
        branch_view = self.sender()
        menu.exec_(branch_view.mapToGlobal(q_point))

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

        selected_indexes = branch_view.selectedIndexes()
        model = branch_view.model()

        ordered_list = []
        for index in selected_indexes:
            if index.isValid() and index.row() not in ordered_list:
                ordered_list.insert(0, index.row())

        if ordered_list:
            model.start_history_event()

        for row in ordered_list:
            model.removeRows(row)

    def checkbox_clicked(self, value):
        checkbox = self.sender()
        label, branch_view, model = self._checkboxes[checkbox]
        label.setVisible(value)
        branch_view.setVisible(value)

    def commit_clicked(self, index):
        self._clicked_commit = index
        branch_view = self.focused_branch_view()
        model = branch_view.model()
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

        if model.is_conflicting_commit(index.row()):
            self._ui.conflictsButton.show()
        else:
            self._ui.conflictsButton.hide()

        self._ui.detailsGroupBox.show()

    def toggle_modifications(self, show_modifications):
        """
            When the toggleModifications button is pressed, change the displayed
            model.
        """
        for label, branch_view, model in self._checkboxes.values():
            if show_modifications:
                branch_view.setModel(model)
            else:
                branch_view.setModel(model.get_orig_q_git_model())

    def conflicts(self):
        dialog = ConflictsDialog(self._clicked_commit.model())
        ret = dialog.exec_()
