# graphics_item.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from PyQt4.QtCore import QMimeData, QPoint, QPointF, QRectF, QString, Qt,\
     SIGNAL
from PyQt4.QtGui import QBrush, QColor, QDrag, QFont, QGraphicsItem,\
     QGraphicsObject, QPainter, QPainterPath, QPixmap, QPolygonF

COMMIT_WIDTH = 150
COMMIT_HEIGHT = 40

ARROW_BASE_WIDTH = 4
ARROW_TIP_WIDTH = 10
ARROW_HEIGHT = 30
ARROW_BASE_X = (COMMIT_WIDTH - ARROW_BASE_WIDTH) / 2

TOTAL_COMMIT_HEIGHT = COMMIT_HEIGHT + ARROW_HEIGHT

FONT_SIZE = 10

GREEN = QColor(0, 150, 0)
BLUE = QColor(0, 0, 150)
BLACK = QColor(0, 0 ,0)
GRAY = QColor(150, 150, 150)
WHITE = QColor(255, 255, 255)


class Arrow(QGraphicsObject):
    """
        This item need to be derived from QGraphicsObject so that we can connect
        slots on it.
    """

    def __init__(self, commit_item, down_arrow=False):
        super(Arrow, self).__init__(parent=commit_item)
        self.commit_item = commit_item

        self.color = BLACK

        self.setAcceptDrops(True)
        self.setAcceptHoverEvents(True)

        self.is_down_arrow = down_arrow

        self.setup_display()

    def setup_display(self):
        self.path = QPainterPath()

        tot_x_offset = ARROW_BASE_X

        tot_y_offset = COMMIT_HEIGHT

        if self.is_down_arrow:
            x_y = (
                (0,                                     0),
                (0,                                     20),
                (- ARROW_TIP_WIDTH/2,                   19),
                (ARROW_BASE_WIDTH/2,                    ARROW_HEIGHT),
                (ARROW_BASE_WIDTH + ARROW_TIP_WIDTH/2,  19),
                (ARROW_BASE_WIDTH,                      20),
                (ARROW_BASE_WIDTH,                      0)
            )
        else:
            x_y = (
                (0,                                     0 + ARROW_HEIGHT),
                (0,                                     -20 + ARROW_HEIGHT),
                (- ARROW_TIP_WIDTH/2,                   -19 + ARROW_HEIGHT),
                (ARROW_BASE_WIDTH/2,                    0),
                (ARROW_BASE_WIDTH + ARROW_TIP_WIDTH/2,  -19 + ARROW_HEIGHT),
                (ARROW_BASE_WIDTH,                      -20 + ARROW_HEIGHT),
                (ARROW_BASE_WIDTH,                      0 + ARROW_HEIGHT)
            )
        absolute_x_y = []
        for x,y in x_y:
            absolute_x_y.append(QPointF(tot_x_offset + x, tot_y_offset + y))

        polygon = QPolygonF(absolute_x_y)
        self.path.addPolygon(polygon)

    def paint(self, painter, option, widget=None):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawPath(self.path)

    def boundingRect(self):
        return self.path.boundingRect()

    def shape(self):
        return self.path

    def dragEnterEvent(self, event):
        """
            This method is called when a dragged object comes in contact with
            the arrow.
            This method should light up the arrow to show that the item can be
            dropped.
        """
        pass

    def dragLeaveEvent(self, event):
        """
            This method should do the opposite that dragEnterEvent do, revert
            the lighting of the arrow.
        """
        pass

    def dropEvent(self, event):
        """
            This method is called when a dragged object is dropped onto the
            arrow.
            This method could either:
                - tell the main class that some commits have been inserted
                - move the next commit items
        """
        self.commit_item.emit(
            SIGNAL("commitItemInserted(QString*)"),
            QString(event.mimeData().text()))

class CommitItem(QGraphicsObject):
    """
        This class should contain:
            - last coordonates of the column.

        Instanciated objects should have:
            - a reference to a GitPython commit
            - a reference to the below CommitItem in the column
            - a reference to the arrow

        A special comitItem could be HEAD.
            A different color.
    """

    def __init__(self, commit, model=None, next_commit_item=None):
        """
            In the init method we should:
                - set the cursor as an open hand

            We need next_commit (the CommitItem above this one in the column) in
            order to get the column offset when refreshing the position.
            We need previous_commit (the CommitItem under this one in the
            column) in order to call refresh_position on it when refreshing
            this CommitItem position.
        """
        super(CommitItem, self).__init__()
        self.orig_color = self.color = BLUE

        self.commit = commit
        self._model = model
#        self.name = commit.hexsha[:7]
        self.name = commit.message[:18]
        self.arrow = None

        self.next_commit = next_commit_item
        self.previous_commit = None

        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.ItemIsMovable)

        self.setup_display()
        self.refresh_position()

    def get_commit(self):
        return self.commit

    def get_model(self):
        return self._model

    def setup_display(self):
        """
            The display should represent the commit short hash and some part of
            the commit message.
        """
        self.path = QPainterPath()

        rect = QRectF(0, 0, COMMIT_WIDTH, COMMIT_HEIGHT)
        self.path.addRoundedRect(rect, 10, 10)

        font = QFont()
        font.setFamily("Helvetica")
        font.setPointSize(FONT_SIZE)
        # TODO: change the way the text is displayed. We should be able to know
        # what will be the size of the displayed text. Maybe QGraphicsText ...
        self.path.addText(
            (COMMIT_WIDTH-len(self.name)*(FONT_SIZE-4))/2 +4,
            (COMMIT_HEIGHT + FONT_SIZE) / 2 ,
            font, QString(self.name))

    def paint(self, painter, option, widget=None):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawPath(self.path)

    def gray(self, bool_value):
        """
            This method repaints the item gray.
        """
        if bool_value:
            self.color = GRAY
        else:
            self.color = self.orig_color
        self.update()

    def boundingRect(self):
        return self.path.boundingRect()

    def shape(self):
        return self.path

    # Event methods
    def mousePressEvent(self, event):
        """
            This method is called when the user clicks on the CommitItem.
            This method could:
                - emit a SIGNAL to the main class in order for actions on this
                commit to be taken (like display commit information).
                We should also think about catching the selected signal directly
                from the main class.
                - set the cursor as a closed hand.
        """
        self.emit(SIGNAL("pressed"), self)
        self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """
            This method is called when a CommitItem is moved.
            This method should create a QDrag in order for a drag event to
            start.
        """
        drag = QDrag(event.widget())
        data = QMimeData()
        data.setText(self.name)

        drag.setMimeData(data)

        #data.setColorData(GREEN)
        pixmap = QPixmap(COMMIT_WIDTH, COMMIT_HEIGHT)
        pixmap.fill(WHITE)
        painter = QPainter(pixmap)
        painter.translate(0, 0)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawPath(self.path)
        painter.end()

        pixmap.setMask(pixmap.createHeuristicMask())
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(0, 0))
        drag.start()

    def hoverMoveEvent(self, event):
        """
            This method is called when the user hovers over the commitItem.
            This method emits a custom signal hoveringOverCommitItem(QString*)
            that is catched by the main class and triggers the gray method on
            every commit that isn't similar to this one. This behaviour as well
            as the trigger condition will be set in the main class.
        """
        self.setCursor(Qt.OpenHandCursor)

    # Position methods
    def refresh_position(self):
        """
            This method uses the next CommitItem position to determine its
            position. The method then triggers the refresh_position on the
            previous CommitItem.
        """
        if self.next_commit is not None:
            # There is a commit above this one in the column (this is not HEAD)
            y_offset = self.next_commit.y() + TOTAL_COMMIT_HEIGHT
        else:
            y_offset = TOTAL_COMMIT_HEIGHT # Could be 0, 10 or 20

        self.setPos(self.x(), y_offset)

        if self.previous_commit is not None:
            self.previous_commit.refresh_position()

    # Organization methods
    def set_previous_commit_item(self, previous_commit_item):
        """
            Sets the previous commit that will be under this one in the column.
        """
        self.previous_commit = previous_commit_item
        if self.arrow is None:
            self.arrow = Arrow(self)

    def get_previous_commit_item(self):
        return self.previous_commit

    def set_next_commit_item(self, next_commit_item):
        self.next_commit = next_commit_item

    def get_next_commit_item(self):
        return self.next_commit

class HeadCommitItem(CommitItem):
    """
        This item represents the HEAD of the branch. It looks like a commitItem
        but the arrow should be reversed.

    """

    def __init__(self):
#        super(HeadCommitItem, self).__init__(...)
        pass

