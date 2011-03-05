
from PyQt4.QtGui import QGraphicsScene, QApplication, QWidget, QGraphicsItem, \
        QPainterPath, QBrush, QGraphicsView, QGraphicsSceneDragDropEvent, \
        QFont, QPainter, QColor, QGraphicsTextItem, QPolygonF, QGraphicsObject,\
        QDrag, QPixmap
from PyQt4.QtCore import QRectF, Qt, SIGNAL, QString, QPointF, QObject, QEvent, QMimeData, QPoint
from graphics_widget_ui import Ui_Form
import sys

COMMIT_WIDTH = 150
COMMIT_HEIGHT = 40

ARROW_BASE_WIDTH = 6
ARROW_TIP_WIDTH = 10
ARROW_HEIGHT = 30
ARROW_BASE_X = (COMMIT_WIDTH - ARROW_BASE_WIDTH) / 2

FONT_SIZE = 18

GREEN = QColor(0, 150, 0)
BLUE = QColor(0, 0, 150)
BLACK = QColor(0, 0 ,0)
GRAY = QColor(150, 150, 150)
WHITE = QColor(255, 255, 255)

class Arrow(QGraphicsObject, QGraphicsItem):

    def __init__(self, x_offset, y_offset, parent=None):
        super(Arrow, self).__init__(parent=parent)
        self._parent = parent

        self.color = BLACK

        self.path = QPainterPath()
        self.setAcceptDrops(True)
        self.setAcceptHoverEvents(True)

        self.x_offset = x_offset
        self.y_offset = y_offset
        
#        self.rect = QRectF(x_offset + ARROW_BASE_X,
#                           y_offset - ARROW_HEIGHT,
#                           ARROW_WIDTH, ARROW_HEIGHT)
#        self.path.addRect(self.rect)
        self.setup_display()

    def setup_display(self):
        polygon = QPolygonF(
            [QPointF(self.x_offset + ARROW_BASE_X,                                          COMMIT_HEIGHT + ARROW_HEIGHT + self.y_offset),
             QPointF(self.x_offset + ARROW_BASE_X,                                          COMMIT_HEIGHT + ARROW_HEIGHT + self.y_offset - 20),
             QPointF(self.x_offset + ARROW_BASE_X - ARROW_TIP_WIDTH / 2,                    COMMIT_HEIGHT + ARROW_HEIGHT + self.y_offset - 19),
             QPointF(self.x_offset + ARROW_BASE_X + ARROW_BASE_WIDTH / 2,                   COMMIT_HEIGHT + ARROW_HEIGHT + self.y_offset - ARROW_HEIGHT),
             QPointF(self.x_offset + ARROW_BASE_X + ARROW_BASE_WIDTH + ARROW_TIP_WIDTH / 2, COMMIT_HEIGHT + ARROW_HEIGHT + self.y_offset - 19),
             QPointF(self.x_offset + ARROW_BASE_X + ARROW_BASE_WIDTH,                       COMMIT_HEIGHT + ARROW_HEIGHT + self.y_offset - 20),
             QPointF(self.x_offset + ARROW_BASE_X + ARROW_BASE_WIDTH,                       COMMIT_HEIGHT + ARROW_HEIGHT + self.y_offset), ]
        )
        self.path.addPolygon(polygon)
#    def hoverMoveEvent(self, event):
#        print "hover arrow move"
#
#    def hoverEnterEvent(self, event):
#        print "hover arrow enter"
#
#    def hoverLeaveEvent(self, event):
#        print "hover arrow leave"

    def dragEnterEvent(self, event):
        print "Enter"

    def dragLeaveEvent(self, event):
        print "Leave"

    def dragMoveEvent(self, event):
        print "Move"

    def dropEvent(self, event):
#        print dir(event.source())
#       print dir(event)
#        print dir(event.mimeData())
        # First string is commit hash, second is the branch
        self._parent.emit(SIGNAL("commitItemInserted(QString*, QString*)"),
                  QString(event.mimeData().text()), self._parent.branch)
        print "Drop"

    def paint(self, painter, option, widget=None):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawPath(self.path)

    def boundingRect(self):
        return self.path.boundingRect()

    def shape(self):
        return self.path

class CommitItem(QGraphicsObject, QGraphicsItem):

    def __init__(self, x_offset, y_offset, color, commit, branch,
                 background_item=True):
        super(CommitItem, self).__init__()
        self.setAcceptDrops(True)

        if background_item:
            self.setAcceptHoverEvents(True)
        else:
            self.setFlags(QGraphicsItem.ItemIsMovable |
                          QGraphicsItem.ItemIsSelectable)

        self.x_offset = x_offset
        self.y_offset = y_offset

        self.commit = commit
        self.branch = branch
        self.color = self.orig_color = color
        self.path = self.setup_display(x_offset, y_offset)

        self.orig_x = self.x()
        self.orig_y = self.y()
        self.setCursor(Qt.OpenHandCursor)

    def setup_display(self, x_offset, y_offset):
        path = QPainterPath()

        self.rect = QRectF(x_offset + 0,
                      y_offset + 0,
                      COMMIT_WIDTH, COMMIT_HEIGHT)
        path.addRoundedRect(self.rect, 10, 10)

        self.font = QFont()
        self.font.setFamily("Helvetica")
        self.font.setPointSize(FONT_SIZE)
        path.addText(
            x_offset + (COMMIT_WIDTH - len(self.commit.name()) * (FONT_SIZE - 4)) / 2 + 4,
            y_offset + (COMMIT_HEIGHT + FONT_SIZE) / 2 ,
            self.font, QString(self.commit.name()))
        return path

    def boundingRect(self):
        return self.path.boundingRect()

    def shape(self):
        return self.path

    def paint(self, painter, option, widget=None):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawPath(self.path)

    def mousePressEvent(self, event):
        QGraphicsItem.mousePressEvent(self, event)
        self.being_moved = True
        self.setZValue(100)
        self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        drag = QDrag(event.widget())
        data = QMimeData()
        data.setText(self.commit.name())

        drag.setMimeData(data)

        #data.setColorData(GREEN)
        pixmap = QPixmap(COMMIT_WIDTH, COMMIT_HEIGHT)
        pixmap.fill(WHITE)
        painter = QPainter(pixmap)
        painter.translate(0, 0)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawPath(self.setup_display(0, 0))
        painter.end()

        pixmap.setMask(pixmap.createHeuristicMask())
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(0, 0))
        drag.start()
#        QGraphicsItem.mouseMoveEvent(self, event)
        self.reinit_position()

    def mouseReleaseEvent(self, event):
        QGraphicsItem.mouseReleaseEvent(self, event)
        self.being_moved = False
        self.setZValue(0)

    def reinit_position(self):
        self.setX(self.orig_x)
        self.setY(self.orig_y)

    def dragEnterEvent(self, event):
        print "item drag enter"

    def dragLeaveEvent(self, event):
        print "item drag leave"

    def dragMoveEvent(self, event):
        print "item drag move"

    def dropEvent(self, event):
        print "item drop event"

    def hoverMoveEvent(self, event):
#        self.setCursor(Qt.OpenHandCursor)
        self.emit(SIGNAL("hoveringOverCommitItem(QString*)"),
                  QString(self.commit.name()))

    def hoverEnterEvent(self, event):
        self.emit(SIGNAL("hoveringOverCommitItem(QString*)"),
                  QString(self.commit.name()))

    def hoverLeaveEvent(self, event):
        self.emit(SIGNAL("finishedHovering(void)"))

    def get_commit(self):
        return self.commit

    def get_name(self):
        return self.commit.name()

    def gray(self, bool_value):
        if bool_value:
            self.color = GRAY
        else:
            self.color = self.orig_color
        self.update()

class Commit(object):

    def __init__(self, name):
        super(Commit, self).__init__()
        self._name = name

    def name(self):
        return self._name

class Hints(QGraphicsItem):

    def __init__(self, x_offset, y_offset):
        super(Hints, self).__init__()

        self.x_offset = x_offset
        self.y_offset = y_offset

        self.path = None
        self.setup_display()

    def setup_display(self, step=0):
        steps = ["Press Alt: matching commits mode",
                 "Keep pressing Alt and hover over a commit",
                 "That way you can see all the commits that have the same name"]
        self.path = QPainterPath()

        self.font = QFont()
        self.font.setFamily("Helvetica")
        self.font.setPointSize(FONT_SIZE)
        self.path.addText(
            self.x_offset,
            self.y_offset,
            self.font, QString(steps[step]))

    def boundingRect(self):
        return self.path.boundingRect()

    def shape(self):
        return self.path

    def paint(self, painter, option, widget=None):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(BLACK))
        painter.drawPath(self.path)

class GraphicsWidget(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self)

        self._ui = Ui_Form()
        self._ui.setupUi(self)

        self.commits = {}
        self.commits["first"] =  ["aaaaa", "bbbbb", "ccccc", "ddddd"]
        self.commits["second"] = ["ggggg", "bbbbb", "xxxxx", "aaaaa"]

        self.scene = QGraphicsScene(self)
        self.view = self._ui.graphicsView
        self.view.setScene(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.matching_commits = False
        self.view.setAcceptDrops(True)

        self.populate()

    def populate(self):
        self.temp_del_items = []
        self.commit_items = []

        self.filter = my_env_filter()
        self.scene.installEventFilter(self.filter)

        self.hints = Hints(0, -60)
        self.scene.addItem(self.hints)
        item_x = 0
        color = GREEN
        for branch in self.commits:
            item_y = 0

            for commit_name in self.commits[branch]:
                commit = Commit(commit_name)
                commit_background_item = CommitItem(item_x, item_y, 
                                                    color, commit, branch,
                                                    background_item=True)
                arrow = Arrow(item_x, item_y, commit_background_item)
                commit_display_item = CommitItem(item_x, item_y,
                                                 color, commit, branch,
                                                 background_item=False)

                self.scene.addItem(commit_display_item)
                self.scene.addItem(commit_background_item)
                self.commit_items.append(commit_background_item)

                item_y += COMMIT_HEIGHT + ARROW_HEIGHT

            item_x += 270
            color = BLUE

        self.connect_signals()

    def clear_scene(self):
        self.temp_del_items = self.scene.items()
        for item in self.temp_del_items:
            self.scene.removeItem(item)
#            del item

    def set_matching_commits_mode(self, bool):
        print "setting matching"
        self.matching_commits = bool
        if bool:
            self.hints.setup_display(step=1)
            self.hints.update()
        else:
            self.commit_item_finished_hovering()

    def connect_signals(self):
        self.connect(self.filter, SIGNAL("setMatchingMode(bool)"),
                     self.set_matching_commits_mode)

        for commit_item in self.commit_items:
            self.connect(commit_item,
                         SIGNAL("hoveringOverCommitItem(QString*)"),
                         self.commit_item_hovered)
            self.connect(commit_item,
                         SIGNAL("finishedHovering(void)"),
                         self.commit_item_finished_hovering)
            self.connect(commit_item,
                         SIGNAL("commitItemInserted(QString*, QString*)"),
                         self.insert_commit)

    def insert_commit(self, name, branch):
        self.clear_scene()
        self.commits[str(branch)].append(name)
        print self.commits
        self.populate()

    def commit_item_hovered(self, commit_name):
        if self.matching_commits:
            self.hints.setup_display(step=2)
            self.hints.update()
            for commit_item in self.commit_items:
                if commit_item.get_name() != commit_name:
                    commit_item.gray(True)

    def commit_item_finished_hovering(self):
        for commit_item in self.commit_items:
            commit_item.gray(False)

class my_env_filter(QGraphicsObject):

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Alt:
                self.emit(SIGNAL("setMatchingMode(bool)"), True)
                return True
        elif event.type() == QEvent.KeyRelease:
            if event.key() == Qt.Key_Alt:
                self.emit(SIGNAL("setMatchingMode(bool)"), False)
        return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = GraphicsWidget()
    widget.show()
    sys.exit(app.exec_())
