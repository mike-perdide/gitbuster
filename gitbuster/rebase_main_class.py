# rebase_main_class.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from gitbuster.branch_view_ui import Ui_BranchView
from PyQt4.QtGui import QWidget, QGraphicsObject, QGraphicsScene, QPainter, QAbstractItemView
from PyQt4.QtCore import QString, SIGNAL, Qt, QPointF
from gitbuster.graphics_items import CommitItem, Arrow

COLUMN_X_OFFSET = 50

class BranchViewWidget(QAbstractItemView, QWidget):

    def __init__(self, model):
        super(BranchViewWidget, self).__init__()
        self._ui = Ui_BranchView()
        self._ui.setupUi(self)

        self.column_y_offset = 0

        self.view = self._ui.graphicsView
        self.scene = QGraphicsScene()
#        self.scene.setModel(model)
        self.view.setScene(self.scene)
        self.view.centerOn(QPointF(0, 0))

        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setAcceptDrops(True)

#        self._ui.label.setText(QString(branch))
        self._ui.label.setText("map")
        self.populate()

        self.connect(self.scene, SIGNAL("reset()"), self.reset)
        self.connect(self, SIGNAL("clearScene"), self.clearScene)

    def visualRect(self, index):
        """
            Returns the rectangle on the viewport occupied by the item at index.
            If your item is displayed in several areas then visualRect should
            return the primary area that contains index and not the complete
            area that index might encompasses, touch or cause drawing.

            :return:
                QRect
        """
        return QRect()

    def scrollTo(self, index, hint=QAbstractItemView.EnsureVisible):
        """
            Scrolls the view if necessary to ensure that the item at index is
            visible. The view will try to position the item according to the
            given hint.

            :param index:
                QModelIndex
            :param hint:
                ScrollHint
        """
        pass

    def indexAt(self, point):
        """
            Returns the model index of the item at the viewport coordinates
            point.

            :return:
                QModelIndex
            :param point:
                QPoint
        """
        pass

    def moveCursor(self, cursorAction, modifiers):
        """
            Returns a QModelIndex object pointing to the next object in the
            view, based on the given cursorAction and keyboard modifiers
            specified by modifiers.

            :return:
                QModelIndex
            :param cursorAction:
                CursorAction
            :param modifiers:
                Qt.KeyboardModifiers
        """
        pass

    def horizontalOffset(self):
        """
            Returns the horizontal offset of the view.

            :return:
                int
        """
        return 0

    def verticalOffset(self):
        """
            Returns the vertical offset of the view.

            :return:
                int
        """
        return 0

    def isIndexHidden(self, index):
        """
            Returns true if the item referred to by the given index is hidden in
            the view, otherwise returns false.

            Hiding is a view specific feature. For example in TableView a column
            can be marked as hidden or a row in the TreeView.

            :return:
                boolean
            :param index:
                QModelIndex
        """
        pass

    def setSelection(self, rect, command):
        """
            Applies the selection flags to the items in or touched by the
            rectangle, rect.

            When implementing your own itemview setSelection should call
            selectionModel()->select(selection, flags) where selection is either
            an empty QModelIndex or a QItemSelection that contains all items
            that are contained in rect.

            :param rect:
                QRect
            :param command:
                QItemSelectionModel.SelectionFlags
        """
        pass

    def visualRegionForSelection(self, selection):
        """
            Returns the region from the viewport of the items in the given
            selection.

            :return:
                QRegion
            :param selection:
                QItemSelection
        """
        pass

    def rowsInserted(self, parent, start, end):
        """
            This slot is called when rows are inserted. The new rows are those
            under the given parent from start to end inclusive. The base class
            implementation calls fetchMore() on the model to check for more
            data.

            :param parent:
                QModelIndex
            :param start:
                int
            :param end:
                int
        """
        pass

    def rowAboutToBeRemoved(self, parent, start, end):
        """
            This slot is called when rows are about to be removed. The deleted
            rows are those under the given parent from start to end inclusive.

            :param parent:
                QModelIndex
            :param start:
                int
            :param end:
                int
        """
        pass

    def dataChanged(self, top_left_index, bottom_right_index):
        """
            This slot is called when items are changed in the model. The changed
            items are those from topLeft to bottomRight inclusive. If just one
            item is changed topLeft == bottomRight.

            :param top_left_index:
                QModelIndex
            :param bottom_right_index:
                QModelIndex
        """
        pass

#    def traverseTroughtIndexes(self, index):
#        """
#            :return:
#                QModelIndex
#            :param index:
#                QModelIndex
#        """
#        pass

    def toggleRenderHints(self):
        pass
    
    def reset(self):
        """
            Reset the internal state of the view.

            Warning: This function will reset open editors, scroll bar
            positions, selections, etc. Existing changes will not be committed.
            If you would like to save your changes when resetting the view, you
            can reimplement this function, commit your changes, and then call
            the superclass' implementation.
        """
        self.emit("clearScene()")
        pass

    def init(self):
        """
            Populate the scene
        """
        next_commit_item = None
        for commit in commits["master"]:
            commit_item = self.add_commit_item(commit)

            if next_commit_item is not None:
                next_commit_item.set_previous(commit_item)
            next_commit_item = commit_item

    def layoutChanged(self):
        pass

    def populate(self):
        commits = {"master": ["aaaa","bbbb","cccc"],
                   "branch": ["dddd","eeee","ffff"] }


    def add_commit_item(self, commit):
        """
            Adds a commit item to the scene and connects the correct signals.
        """
        commit_item = CommitItem(commit, self)
        self.scene.addItem(commit_item)
        commit_item.moveBy(COLUMN_X_OFFSET, 0)

        self.connect(commit_item,
                     SIGNAL("commitItemInserted(QString*)"),
                     self.item_inserted)

        return commit_item

    def get_column_y_offset(self):
        return self.column_y_offset

    def set_column_y_offset(self, offset):
        self.column_y_offset = offset

    def item_inserted(self, inserted_commit_hash):
        """
           If we need to insert a commit C between A and B like this:
                HEAD - B - C - A (initial commit)
            We just need to do:
                - set B as the new column end
                - set C as the below commit of B
                - set A as the below commit of C
                - call the move_at_the_column_end method on C

            See also CommitItem.move_at_the_column_end.
        """
        new_commit_item = self.add_commit_item(inserted_commit_hash)
        original_previous = self.sender().get_previous()

        new_commit_item.set_previous(original_previous)
        self.sender().set_previous(new_commit_item)

        self.sender().set_as_the_new_column_end()
        self.sender().move_at_the_column_end()


class RebaseMainClass:

    def __init__(self, parent, directory, models):
        self.parent = parent
        self._models = models

        _ui = self.parent._ui
        for model in models.values():
            branch_view = BranchViewWidget(model)
            branch_view.setModel(model)
            _ui.graphicsViewLayout.insertWidget(0, branch_view)

    def set_matching_commits_mode(self, bool):
        self.matching_commits = bool
        if bool:
            self.hints.setup_display(step=1)
            self.hints.update()
        else:
            self.commit_item_finished_hovering()

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = GraphicsWidget()
    widget.show()
    sys.exit(app.exec_())
