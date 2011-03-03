from PyQt4.QtGui import QGraphicsItem, QBrush
from PyQt4.QtCore import Qt, QParallelAnimationGroup, QPropertyAnimation, QEasingCurve, QRectF, QObject

class RoboPart(QGraphicsItem, QObject):
    
    def __init__(self, parent=None):
        QObject.__init__(self)
        QGraphicsItem.__init__(self)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasColor():
            event.accept()
            self.dragOver = True
            update()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.dragOver = False
        self.update()

    def dropEvent(self, event):
        self.dragOver = False
        update()

class RobotHead(RoboPart):

    def __init__(self, parent=None):
        RoboPart.__init__(self)
        self.color = 150

    def boundingRect(self):
        return QRectF(-15, -50, 30, 50)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self.color))
        painter.drawRoundedRect(-10, -30, 20, 30, 25, 25, Qt.RelativeSize)
        painter.drawEllipse(-7, -3 - 20, 7, 7)
        painter.drawEllipse(0, -3 - 20, 7, 7)
        painter.drawEllipse(-5, -1 - 20, 2, 2)
        painter.drawEllipse(2, -1 - 20, 2, 2)
        painter.drawArc(-6, -2 - 20, 12, 15, 190 * 16, 160 * 16)


class RobotTorso(RoboPart):

    def __init__(self, parent=None):
        RoboPart.__init__(self)
        self.color = 100

    def boundingRect(self):
        return QRectF(-30, -20, 60, 60)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self.color))
        painter.drawRoundedRect(-20, -20, 40, 60, 25, 25, Qt.RelativeSize);
        painter.drawEllipse(-25, -20, 20, 20);
        painter.drawEllipse(5, -20, 20, 20);
        painter.drawEllipse(-20, 22, 20, 20);
        painter.drawEllipse(0, 22, 20, 20);

class RobotLimb(RoboPart):
    def __init__(self, parent=None):
        RoboPart.__init__(self)
        self.color = 50

    def boundingRect(self):
        return QRectF(-5, -5, 40, 10)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self.color))
        painter.drawRoundedRect(boundingRect(), 50, 50, Qt.RelativeSize)
        painter.drawEllipse(-5, -5, 10, 10)

class Robot(RoboPart):

    def __init__(self, parent=None):
        RoboPart.__init__(self)

        self.setFlag(QGraphicsItem.ItemHasNoContents)

        self.torsoItem = RobotTorso(self)
        self.headItem = RobotHead(self.torsoItem)
        self.upperLeftArmItem = RobotLimb(self.torsoItem)
        self.lowerLeftArmItem = RobotLimb(self.upperLeftArmItem)
        self.upperRightArmItem = RobotLimb(self.torsoItem)
        self.lowerRightArmItem = RobotLimb(self.upperRightArmItem)
        self.upperRightLegItem = RobotLimb(self.torsoItem)
        self.lowerRightLegItem = RobotLimb(self.upperRightLegItem)
        self.upperLeftLegItem = RobotLimb(self.torsoItem)
        self.lowerLeftLegItem = RobotLimb(self.upperLeftLegItem)

        self.headItem.setPos(0, -18)
        self.upperLeftArmItem.setPos(-15, -10)
        self.lowerLeftArmItem.setPos(30, 0)
        self.upperRightArmItem.setPos(15, -10)
        self.lowerRightArmItem.setPos(30, 0)
        self.upperRightLegItem.setPos(10, 32)
        self.lowerRightLegItem.setPos(30, 0)
        self.upperLeftLegItem.setPos(-10, 32)
        self.lowerLeftLegItem.setPos(30, 0)

        self.animation = QParallelAnimationGroup(None)


        #self.headAnimation = QPropertyAnimation(self.headItem, "scale")
        #self.headAnimation.setStartValue(20)
        #self.headAnimation.setEndValue(-20)

        #self.headScaleAnimation = QPropertyAnimation(self.headItem, "scale")
        #self.headScaleAnimation.setEndValue(1.1)
        #self.animation.addAnimation(self.headAnimation)
        #self.animation.addAnimation(self.headScaleAnimation)

        #self.upperLeftArmAnimation = QPropertyAnimation(self.upperLeftArmItem, "rotation")
        #self.upperLeftArmAnimation.setStartValue(190)
        #self.upperLeftArmAnimation.setEndValue(180)
        #self.animation.addAnimation(self.upperLeftArmAnimation)

        #self.lowerLeftArmAnimation = QPropertyAnimation(self.lowerLeftArmItem, "rotation")
        #self.lowerLeftArmAnimation.setStartValue(50)
        #self.lowerLeftArmAnimation.setEndValue(10)
        #self.animation.addAnimation(self.lowerLeftArmAnimation)

        #self.upperRightArmAnimation = QPropertyAnimation(self.upperRightArmItem, "rotation")
        #self.upperRightArmAnimation.setStartValue(300)
        #self.upperRightArmAnimation.setEndValue(310)
        #self.animation.addAnimation(self.upperRightArmAnimation)

        #self.lowerRightArmAnimation = QPropertyAnimation(self.lowerRightArmItem, "rotation")
        #self.lowerRightArmAnimation.setStartValue(0)
        #self.lowerRightArmAnimation.setEndValue(-70)
        #self.animation.addAnimation(self.lowerRightArmAnimation)

        #self.upperLeftLegAnimation = QPropertyAnimation(self.upperLeftLegItem, "rotation")
        #self.upperLeftLegAnimation.setStartValue(150)
        #self.upperLeftLegAnimation.setEndValue(80)
        #self.animation.addAnimation(self.upperLeftLegAnimation)

        #self.lowerLeftLegAnimation = QPropertyAnimation(self.lowerLeftLegItem, "rotation")
        #self.lowerLeftLegAnimation.setStartValue(70)
        #self.lowerLeftLegAnimation.setEndValue(10)
        #self.animation.addAnimation(self.lowerLeftLegAnimation)

        #self.upperRightLegAnimation = QPropertyAnimation(self.upperRightLegItem, "rotation")
        #self.upperRightLegAnimation.setStartValue(40)
        #self.upperRightLegAnimation.setEndValue(120)
        #self.animation.addAnimation(self.upperRightLegAnimation)

        #self.lowerRightLegAnimation = QPropertyAnimation(self.lowerRightLegItem, "rotation")
        #self.lowerRightLegAnimation.setStartValue(10)
        #self.lowerRightLegAnimation.setEndValue(50)
        #self.animation.addAnimation(self.lowerRightLegAnimation)

        #self.torsoAnimation = QPropertyAnimation(self.torsoItem, "rotation")
        #self.torsoAnimation.setStartValue(5)
        #self.torsoAnimation.setEndValue(-20)
        #self.animation.addAnimation(self.torsoAnimation)

        for i in xrange(self.animation.animationCount()):
            anim = QPropertyAnimation(self.animation.animationAt(i))
            anim.setEasingCurve(QEasingCurve.SineCurve)
            anim.setDuration(2000)

        self.animation.setLoopCount(-1)
        self.animation.start()

    def boundingRect(self):
        return QRectF()

    def paint(self):
        pass
