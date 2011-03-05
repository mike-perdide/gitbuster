
class Arrow(QGraphicsObject, QGraphicsItem):
    """
        This item need to be derived from QGraphicsObject so that we can connect
        slots on it.
    """

    def __init__(self, x_offset, y_offset, parent=None):
        super(Arrow, self).__init__(parent=parent)
        self._parent = parent

        self.color = BLACK

        self.setup_display()
        self.setAcceptDrops(True)
        self.setAcceptHoverEvents(True)

        self.x_offset = x_offset
        self.y_offset = y_offset

    def setup_display(self):
        self.path = QPainterPath()
        polygon = QPolygonF(
            [QPointF(self.x_offset + ARROW_BASE_X,
                     COMMIT_HEIGHT + self.y_offset),
             QPointF(self.x_offset + ARROW_BASE_X,
                     COMMIT_HEIGHT + self.y_offset + 20),
             QPointF(self.x_offset + ARROW_BASE_X - ARROW_TIP_WIDTH / 2,
                     COMMIT_HEIGHT + self.y_offset + 19),
             QPointF(self.x_offset + ARROW_BASE_X + ARROW_BASE_WIDTH / 2,
                     COMMIT_HEIGHT + self.y_offset + ARROW_HEIGHT),
             QPointF(self.x_offset + ARROW_BASE_X + ARROW_BASE_WIDTH
                     + ARROW_TIP_WIDTH / 2,
                     COMMIT_HEIGHT + self.y_offset + 19),
             QPointF(self.x_offset + ARROW_BASE_X + ARROW_BASE_WIDTH,
                     COMMIT_HEIGHT + self.y_offset + 20),
             QPointF(self.x_offset + ARROW_BASE_X + ARROW_BASE_WIDTH,
                     COMMIT_HEIGHT + self.y_offset), ]
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
        pass

class CommitItem(QGraphicsObject, QGraphicsItem):
    """
        This class should contain:
            - last coordonates of the column. Since we may have several columns,
            we may need a list of 2-lists
        This class may contain:
            - a reference to the HEAD of each branch

        Instanciated objects should have:
            - a reference to a GitPython commit
            - a reference to the below CommitItem in the column
            - a reference to the arrow

        A special comitItem could be HEAD.
            A different color.
    """

    def __init__(self):
        """
            In the init method we should:
                - set the cursor as an open hand
        """
        super(CommitItem, self).__init__()

    # Display methods
    def setup_display(self):
        pass

    def paint(self, painter, option, widget=None):
        pass

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
        pass

    def mouseMoveEvent(self, event):
        """
            This method is called when a CommitItem is moved.
            This method should create a QDrag in order for a drag event to
            start.
        """
        pass

    def hoverMoveEvent(self, event):
        """
            This method is called when the user hovers over the commitItem.
            This method emits a custom signal hoveringOverCommitItem(QString*)
            that is catched by the main class and triggers the gray method on
            every commit that isn't similar to this one. This behaviour as well
            as the trigger condition will be set in the main class.
        """
        pass

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
        pass

    def set_as_the_new_column_end(self):
        """
            This method sets the class parameter "last item coordinates" with
            this item's coordinates.
        """
        pass


