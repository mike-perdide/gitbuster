
from PyQt4.QtGui import QGraphicsScene, QApplication, QWidget, QGraphicsItem, QPainterPath, QBrush, QGraphicsView, QGraphicsSceneDragDropEvent
from PyQt4.QtCore import QRectF, Qt, SIGNAL
from graphics_widget_ui import Ui_Form
import sys


class Commit(QGraphicsItem):

    def __init__(self):
        QGraphicsItem.__init__(self)

        self.color = 150
        self.rect = QRectF(30, 30, 30, 30)
        self.path = QPainterPath()
        self.path.addEllipse(self.rect)

        self.setFlags(QGraphicsItem.ItemIsMovable)
        self.setActive(True)
        self.setEnabled(True)
        self.setAcceptDrops(True)
        self.setAcceptHoverEvents(True)
        self.setAcceptTouchEvents(True)
        
        print "Accept Drops:", self.acceptDrops()

    def boundingRect(self):
        return self.path.boundingRect()

    def shape(self):
        return self.path

    def paint(self, painter, option, widget=None):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawPath(self.path)

    def dragEnterEvent(self, event):
        print "Drag Enter"
        print event
        event.accept()
       
    def dragLeaveEvent(self, event):
        print "Drag Leave"
        print event
        event.accept()

    def dragMoveEvent(self, event):
        print "Drag Move"
        print event
        event.accept()

#    def dropEvent(self, event):
#        print "Drop Event"
#        event.accept()
#
#    def mouseDoubleClickEvent (self, event):
#        print event
#
#    def event(self, event):
#        print event
#
#    def mouseMoveEvent (self, event):
#        print "Mouse move", event
#        QGraphicsItem.mouseMoveEvent(self, event)
#
#    def hoverEnterEvent(self, event):
#        print "Hover enter", event
#
#    def mousePressEvent (self, event):
#        print "Mouse pressed", event
#        event.accept()
#
#    def mouseReleaseEvent (self, event):
#        print "Mouse released", event
#        event.accept()


class GraphicsWidget(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self)

        self._ui = Ui_Form()
        self._ui.setupUi(self)

        self.scene = QGraphicsScene(self)
        self.view = self._ui.graphicsView
        self.view.setScene(self.scene)

        self.populate()

    def populate(self):
        commit = Commit()
        self.scene.addItem(commit)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = GraphicsWidget()
    widget.show()
    sys.exit(app.exec_())
