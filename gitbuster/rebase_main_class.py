# rebase_main_class.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from gitbuster.branch_view_ui import Ui_BranchView
from PyQt4.QtGui import QWidget, QGraphicsObject, QGraphicsScene, QPainter, \
                        QCheckBox, QApplication, QTableView, QLabel, \
                        QKeySequence, QShortcut
from PyQt4.QtCore import QString, SIGNAL, Qt, QPointF, QObject

from gitbuster.graphics_items import CommitItem, Arrow


class BranchViewWidget(QWidget):

    def __init__(self, model):
        super(BranchViewWidget, self).__init__()
        self._ui = Ui_BranchView()
        self._ui.setupUi(self)

        self.column_y_offset = 0

        self.view = self._ui.graphicsView
        self.scene = model.get_scene()
#        self.scene.setModel(model)
        self.view.setScene(self.scene)
        self.view.centerOn(QPointF(0, 0))

        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setAcceptDrops(True)

        branch = str(model.get_current_branch())
        self._ui.label.setText(QString(branch))
        self.populate()

    def init(self):
        """
            Populate the scene
        """
        pass

    def layoutChanged(self):
        pass

    def populate(self):
        commits = {"master": ["aaaa","bbbb","cccc"],
                   "branch": ["dddd","eeee","ffff"] }



    def get_column_y_offset(self):
        return self.column_y_offset

    def set_column_y_offset(self, offset):
        self.column_y_offset = offset


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

            signal = SIGNAL("pressed")
            for commit_item in model.get_commit_items():
                QObject.connect(commit_item, signal, self.pressed_commit_item)

            self._checkboxes[checkbox] = (label, branch_view)
            QObject.connect(checkbox,
                            SIGNAL("stateChanged(int)"),
                            self.checkboxClicked)

            shortcut = QShortcut(QKeySequence(QKeySequence.Delete), branch_view)
            QObject.connect(shortcut, SIGNAL("activated()"), self.removeRows)

    def removeRows(self):
        """
            When <Del> is pressed, this method removes the selected rows of the
            table view.

            We delete the rows starting with the last one, in order to use the
            correct indexes.
        """
        branch_view = self.sender().parentWidget()
        selected_indexes = branch_view.selectedIndexes()
        ordered_list = []
        for index in selected_indexes:
            if index.isValid() and index.row() not in ordered_list:
                ordered_list.insert(0, index.row())

        for row in ordered_list:
            branch_view.model().removeRows(row)

    def checkboxClicked(self, value):
        checkbox = self.sender()
        for widget in self._checkboxes[checkbox]:
            widget.setVisible(value)

#    def set_matching_commits_mode(self, bool):
#        self.matching_commits = bool
#        if bool:
#            self.hints.setup_display(step=1)
#            self.hints.update()
#        else:
#            self.commit_item_finished_hovering()

    def pressed_commit_item(self, commit_item):
        """
            Triggers the display of the detail of commit_item.commit.

            This method is called when the users presses a commitItem (similar
            to the QPushButton "pushed()" signal).
        """
        commit = commit_item.get_commit()
        model = commit_item.get_model()
        row = model.row_of(commit)

        ui = self.parent._ui
        display_widgets_methods = (
            ('hexsha', ui.hexshaHolderLabel.setText),
            ('authored_date', ui.authoredDateHolderLabel.setText),
            ('committed_date', ui.commitDateHolderLabel.setText),
            ('author', ui.authorHolderLabel.setText),
            ('committer', ui.commiterHolderLabel.setText),
            ('message', ui.messageHolderTextEdit.append)
        )

        model_columns = model.get_columns()
        print model_columns
        for col_name, display_method in display_widgets_methods:
            col = model_columns.index(col_name)

            index = model.index(row, col)
            data = model.data(index, Qt.DisplayRole)

            display_method(data.toString())

#    def insert_commit(self, name, branch):
#        self.clear_scene()
#        self.commits[str(branch)].append(name)
#        print self.commits
#        self.populate()

#    def commit_item_hovered(self, commit_name):
#        if self.matching_commits:
#            self.hints.setup_display(step=2)
#            self.hints.update()
#            for commit_item in self.commit_items:
#                if commit_item.get_name() != commit_name:
#                    commit_item.gray(True)
#
#    def commit_item_finished_hovering(self):
#        for commit_item in self.commit_items:
#            commit_item.gray(False)

#class my_env_filter(QGraphicsObject):
#
#    def eventFilter(self, obj, event):
#        if event.type() == QEvent.KeyPress:
#            if event.key() == Qt.Key_Alt:
#                self.emit(SIGNAL("setMatchingMode(bool)"), True)
#                return True
#        elif event.type() == QEvent.KeyRelease:
#            if event.key() == Qt.Key_Alt:
#                self.emit(SIGNAL("setMatchingMode(bool)"), False)
#        return False
