# rebase_main_class.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from branch_view_ui import Ui_BranchView
from PyQt4.QtGui import QWidget, QGraphicsObject, QGraphicsScene, QPainter


class BranchViewWidget(QWidget):
    """
        This widget should be draggable.
    """
    def __init__(self):
        super(QWidget, self).__init__()
        self._ui = Ui_BranchView()
        self._ui.setupUi(self)

        self.view = self._ui.graphicsView
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)

        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setAcceptDrops(True)

        self.populate()

    def populate(self):
        self.temp_del_items = []
        self.commit_items = []

#        item_x = 0
#        color = 1
#        for branch in self.commits:
#            item_y = 0
#
#            for commit_name in self.commits[branch]:
#                commit = Commit(commit_name)
#                commit_background_item = CommitItem(item_x, item_y, 
#                                                    color, commit, branch,
#                                                    background_item=True)
#                arrow = Arrow(item_x, item_y, commit_background_item)
#                commit_display_item = CommitItem(item_x, item_y,
#                                                 color, commit, branch,
#                                                 background_item=False)
#
#                self.scene.addItem(commit_display_item)
#                self.scene.addItem(commit_background_item)
#                self.commit_items.append(commit_background_item)
#
#                item_y += COMMIT_HEIGHT + ARROW_HEIGHT
#
#            item_x += 270
#            color = BLUE

        self.connect_signals()

    def clear_scene(self):
        self.temp_del_items = self.scene.items()
        for item in self.temp_del_items:
            self.scene.removeItem(item)
#            del item

    def connect_signals(self):
        pass
        #for commit_item in self.commit_items:
        #    self.connect(commit_item,
        #                 SIGNAL("hoveringOverCommitItem(QString*)"),
        #                 self.commit_item_hovered)
        #    self.connect(commit_item,
        #                 SIGNAL("finishedHovering(void)"),
        #                 self.commit_item_finished_hovering)
        #    self.connect(commit_item,
        #                 SIGNAL("commitItemInserted(QString*, QString*)"),
        #                 self.insert_commit)


class RebaseMainClass():

    def __init__(self, parent, directory):
        self.parent = parent
        self.parent._ui.graphicsViewLayout.addWidget(BranchViewWidget())
        self.parent._ui.graphicsViewLayout.addWidget(BranchViewWidget())
        self.parent._ui.graphicsViewLayout.addWidget(BranchViewWidget())
        self.parent._ui.graphicsViewLayout.addWidget(BranchViewWidget())
        self.parent._ui.graphicsViewLayout.addWidget(BranchViewWidget())

    def set_matching_commits_mode(self, bool):
        print "setting matching"
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
