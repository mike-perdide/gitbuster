# rebase_main_class.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from gitbuster.branch_view_ui import Ui_BranchView
from PyQt4.QtGui import QWidget, QCheckBox, QApplication, QTableView, QLabel, \
                        QKeySequence, QShortcut
from PyQt4.QtCore import QString, SIGNAL, Qt, QPointF, QObject, QModelIndex

from gitbuster.graphics_items import CommitItem, Arrow


class RebaseMainClass(QWidget):

    def __init__(self, parent, directory, models):
        QObject.__init__(self, parent)

        self.parent = parent
        self._models = models
        self._checkboxes = {}

        _ui = self.parent._ui
        iter = 0

        for branch, model in models.items():
            checkbox = QCheckBox(self.parent._ui.centralwidget)
            checkbox.setText(QApplication.translate("MainWindow",
                                                branch.name,
                                                None, QApplication.UnicodeUTF8))
            self.parent._ui.branchCheckboxLayout.addWidget(checkbox, iter/2,
                                                           iter%2, 1, 1)

            branch_view = QTableView(self)
            branch_view.setModel(model)
            for col in xrange(1, 7):
                branch_view.hideColumn(col)
            branch_view.resizeColumnsToContents()
            branch_view.horizontalHeader().setStretchLastSection(True)
            branch_view.setSelectionMode(branch_view.ExtendedSelection)
            branch_view.setDragDropMode(branch_view.DragDrop)
            branch_view.setSelectionBehavior(branch_view.SelectRows)
            branch_view.setEditTriggers(branch_view.NoEditTriggers)

            QObject.connect(branch_view,
                            SIGNAL("activated(const QModelIndex&)"),
                            self.commit_clicked)
            QObject.connect(branch_view,
                            SIGNAL("clicked(const QModelIndex&)"),
                            self.commit_clicked)

            label = QLabel(self)
            label.setText(branch.name)

            # Insert the view in the window's layout
            _ui.viewLayout.addWidget(label, 0, iter)
            _ui.viewLayout.addWidget(branch_view, 1, iter)

            iter += 1

            if branch == self.parent.current_branch:
                checkbox.setCheckState(Qt.Checked)
            else:
                branch_view.hide()
                label.hide()

            self._checkboxes[checkbox] = (label, branch_view)
            QObject.connect(checkbox,
                            SIGNAL("stateChanged(int)"),
                            self.checkbox_clicked)

        shortcut = QShortcut(QKeySequence(QKeySequence.Delete), self)
        QObject.connect(shortcut, SIGNAL("activated()"), self.remove_rows)

        shortcut = QShortcut(QKeySequence(QKeySequence.Undo), self)
        QObject.connect(shortcut, SIGNAL("activated()"), self.undo_history)

        shortcut = QShortcut(QKeySequence(QKeySequence.Redo), self)
        QObject.connect(shortcut, SIGNAL("activated()"), self.redo_history)

    def undo_history(self):
        branch_view = self.focused_branch_view()
        model = branch_view.model()
        model.undo_history()

    def redo_history(self):
        branch_view = self.focused_branch_view()
        model = branch_view.model()
        model.redo_history()

    def focused_branch_view(self):
        """
            Returns the branch_view that has the focus.
        """
        for label, branch_view in self._checkboxes.values():
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
        selected_indexes = branch_view.selectedIndexes()
        ordered_list = []
        for index in selected_indexes:
            if index.isValid() and index.row() not in ordered_list:
                ordered_list.insert(0, index.row())

        for row in ordered_list:
            branch_view.model().removeRows(row)

    def checkbox_clicked(self, value):
        checkbox = self.sender()
        for widget in self._checkboxes[checkbox]:
            widget.setVisible(value)

    def commit_clicked(self, index):
        branch_view = self.focused_branch_view()
        _ui = self.parent._ui
        model = branch_view.model()
        row = index.row()

        labels = {
            'hexsha' :          _ui.hexshaHolderLabel,
            'authored_date' :   _ui.authoredDateHolderLabel,
            'committed_date' :  _ui.commitDateHolderLabel,
            'author_name' :     _ui.authorHolderLabel,
            'committer_name' :  _ui.committerHolderLabel,
            'message' :         _ui.messageHolderTextEdit
        }

        for field in labels:
            column = model.get_columns().index(field)
            index = model.index(row, column, QModelIndex())

            if "date" in field:
                data = model.data(index, Qt.DisplayRole)
            else:
                data = model.data(index, Qt.EditRole)

            labels[field].setText(data.toString())
