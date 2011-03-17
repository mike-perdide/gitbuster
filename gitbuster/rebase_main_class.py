# rebase_main_class.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from gitbuster.branch_view_ui import Ui_BranchView
from PyQt4.QtGui import QWidget, QGraphicsObject, QGraphicsScene, QPainter
from PyQt4.QtCore import QString, SIGNAL, Qt, QPointF
from gitbuster.graphics_items import CommitItem, Arrow

COLUMN_X_OFFSET = 50

class BranchViewWidget(QWidget):

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
