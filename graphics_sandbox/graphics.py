
from PyQt4.QtGui import QGraphicsScene, QApplication, QWidget, QGraphicsItem, \
        QPainterPath, QBrush, QGraphicsView, QGraphicsSceneDragDropEvent, \
        QFont, QPainter, QColor, QGraphicsTextItem, QPolygonF, QGraphicsObject
from PyQt4.QtCore import QRectF, Qt, SIGNAL, QString, QPointF, QObject
from graphics_widget_ui import Ui_Form
import sys

COMMIT_WIDTH = 150
COMMIT_HEIGHT = 30

ARROW_BASE_WIDTH = 6
ARROW_TIP_WIDTH = 15
ARROW_HEIGHT = 30
ARROW_BASE_X = (COMMIT_WIDTH - ARROW_BASE_WIDTH) / 2

FONT_SIZE = 19

GREEN = QColor(0, 150, 0)
BLACK = QColor(0, 0 ,0)
GRAY = QColor(150, 150, 150)

class Arrow(QGraphicsItem):

    def __init__(self, x_offset, y_offset, parent=None):
        super(Arrow, self).__init__(parent)

        self.color = BLACK
        self.setFlags(QGraphicsItem.ItemIsMovable)

        self.path = QPainterPath()
        
#        self.rect = QRectF(x_offset + ARROW_BASE_X,
#                           y_offset - ARROW_HEIGHT,
#                           ARROW_WIDTH, ARROW_HEIGHT)
#        self.path.addRect(self.rect)

        polygon = QPolygonF(
            [QPointF(x_offset + ARROW_BASE_X,                        y_offset),
             QPointF(x_offset + ARROW_BASE_X,                        y_offset - 20),
             QPointF(x_offset + ARROW_BASE_X - ARROW_TIP_WIDTH / 2,  y_offset - 18),
             QPointF(x_offset + ARROW_BASE_X + ARROW_BASE_WIDTH / 2, y_offset - ARROW_HEIGHT),
             QPointF(x_offset + ARROW_BASE_X + ARROW_BASE_WIDTH + ARROW_TIP_WIDTH / 2, y_offset - 18),
             QPointF(x_offset + ARROW_BASE_X + ARROW_BASE_WIDTH,     y_offset - 20),
             QPointF(x_offset + ARROW_BASE_X + ARROW_BASE_WIDTH,     y_offset), ]
        )
        self.path.addPolygon(polygon)


    def paint(self, painter, option, widget=None):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawPath(self.path)

    def boundingRect(self):
        return self.path.boundingRect()

    def shape(self):
        return self.path

class CommitItem(QGraphicsObject, QGraphicsItem):

    def __init__(self, x_offset, y_offset, color, commit):
        super(CommitItem, self).__init__()
#        QGraphicsItem.__init__(self)

        self.color = self.orig_color = color
#        self.setFlags(QGraphicsItem.ItemIsMovable)
        self.setAcceptHoverEvents(True)

        self.path = QPainterPath()

        self.rect = QRectF(0 + x_offset, 0 + y_offset,
                           COMMIT_WIDTH, COMMIT_HEIGHT)
        self.path.addRoundedRect(self.rect, 10, 10)
        
        self.font = QFont()
        self.font.setFamily("Helvetica")
        self.font.setPointSize(FONT_SIZE)
        self.path.addText(
            x_offset + (COMMIT_WIDTH - len(commit.name()) * FONT_SIZE) / 2 + 4,
            y_offset + (COMMIT_HEIGHT + FONT_SIZE) / 2 ,
            self.font, QString(commit.name()))

        self.commit = commit

    def boundingRect(self):
        return self.path.boundingRect()

    def shape(self):
        return self.path

    def paint(self, painter, option, widget=None):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawPath(self.path)

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


class GraphicsWidget(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self)

        self._ui = Ui_Form()
        self._ui.setupUi(self)

        self.scene = QGraphicsScene(self)
        self.view = self._ui.graphicsView
        self.view.setScene(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)

        self.populate()

        self.connect_signals()

    def populate(self):
        self.commit_items = []

        # First branch
        commits = {}
        commits["first"] = ("a", "b", "c", "d")
        commits["second"] = ("g", "b", "x", "t")

        item_x = 0
        color = GREEN
        for branch in commits:
            item_y = 0

            for commit_name in commits[branch]:
                commit = Commit(commit_name*5)
                commit_item = CommitItem(item_x, item_y, color, commit)
                arrow = Arrow(item_x, item_y, commit_item)
                self.scene.addItem(commit_item)
                self.commit_items.append(commit_item)

                item_y += COMMIT_HEIGHT + ARROW_HEIGHT

            item_x += 270
            color = BLUE

    def connect_signals(self):
        for commit_item in self.commit_items:
            self.connect(commit_item,
                         SIGNAL("hoveringOverCommitItem(QString*)"),
                         self.commit_item_hovered)
            self.connect(commit_item,
                         SIGNAL("finishedHovering(void)"),
                         self.commit_item_finished_hovering)

    def commit_item_hovered(self, commit_name):
        for commit_item in self.commit_items:
            if commit_item.get_name() != commit_name:
                commit_item.gray(True)

    def commit_item_finished_hovering(self):
        for commit_item in self.commit_items:
            commit_item.gray(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = GraphicsWidget()
    widget.show()
    sys.exit(app.exec_())
