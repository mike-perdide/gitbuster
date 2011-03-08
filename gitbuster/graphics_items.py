# graphics_item.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QGraphicsScene, QApplication, QWidget, QGraphicsItem, \
        QPainterPath, QBrush, QGraphicsView, QGraphicsSceneDragDropEvent, \
        QFont, QPainter, QColor, QGraphicsTextItem, QPolygonF, QGraphicsObject,\
        QDrag, QPixmap
from PyQt4.QtCore import QRectF, Qt, SIGNAL, QString, QPointF, QObject, \
        QEvent, QMimeData, QPoint

COMMIT_WIDTH = 150
COMMIT_HEIGHT = 40

ARROW_BASE_WIDTH = 6
ARROW_TIP_WIDTH = 10
ARROW_HEIGHT = 30
ARROW_BASE_X = (COMMIT_WIDTH - ARROW_BASE_WIDTH) / 2

TOTAL_COMMIT_HEIGHT = COMMIT_HEIGHT + ARROW_HEIGHT

FONT_SIZE = 18

GREEN = QColor(0, 150, 0)
BLUE = QColor(0, 0, 150)
BLACK = QColor(0, 0 ,0)
GRAY = QColor(150, 150, 150)
WHITE = QColor(255, 255, 255)


class Arrow(QGraphicsObject, QGraphicsItem):
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

class CommitItem(QGraphicsObject, QGraphicsItem):
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

    def __init__(self, name, branch_view):
        """
            In the init method we should:
                - set the cursor as an open hand
        """
        super(CommitItem, self).__init__()
        self.orig_color = self.color = BLUE

        self.name = name
        self.arrow = None
        self.previous_commit = None
        self.branch_view = branch_view

        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.ItemIsMovable)

        self.setup_display()
        self.move_at_the_column_end()

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
    def move_at_the_column_end(self):
        """
            This method should use the CommitItem parameter to find out its
            coordinates (and therefore be displayed at the end of the column.
            This should trigger the same method on the next commit.
            That way, if we need to insert a commit C between A and B like this:
                HEAD - B - C - A (initial commit)
            We just need to do:
                - set B as the new column end
                - set C as the below commit of B
                - set A as the below commit of C
                - call the move_at_the_column_end method on C
        """
        column_offset = self.branch_view.get_column_offset()
        self.setPos(0, column_offset)
        self.branch_view.set_column_offset(column_offset + TOTAL_COMMIT_HEIGHT)

        if self.previous_commit is not None:
            self.previous_commit.move_at_the_column_end()

    def set_as_the_new_column_end(self):
        """
            This method sets the class parameter "last item coordinates" with
            this item's coordinates.
        """
        self.branch_view.set_column_offset(self.y())

    # Organization methods
    def set_previous(self, previous_commit):
        """
            Sets the previous commit that will be under this one in the column.
        """
        self.previous_commit = previous_commit
        if self.arrow is None:
            self.arrow = Arrow(self)

    def get_previous(self):
        return self.previous_commit

class HeadCommitItem(CommitItem):
    """
        This item represents the HEAD of the branch. It looks like a commitItem
        but the arrow should be reversed.

    """

    def __init__(self):
#        super(HeadCommitItem, self).__init__(...)
        pass

