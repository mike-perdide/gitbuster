from PyQt4.QtGui import QApplication, QGraphicsView, QGraphicsScene, QColor, QPainter
from robot import Robot
import sys

app = QApplication(sys.argv)

scene = QGraphicsScene(-200, -200, 400, 400)

robot = Robot()
robot.scale(1.2, 1.2)
robot.setPos(0, -20)
scene.addItem(robot)
view = QGraphicsView(scene)
view.setRenderHint(QPainter.Antialiasing)
view.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
view.setBackgroundBrush(QColor(230, 200, 167))
view.setWindowTitle("Drag and Drop Robot")
view.show()

app.exec_()

