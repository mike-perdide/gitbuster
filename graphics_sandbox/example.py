import os
import sys
import tempfile

from PyQt4.QtCore import *
from PyQt4.QtGui import *

#QLineEdit   (to replace below)
class MyWebView(QTextBrowser):
    def dragEnterEvent(self, e):
        e.accept()
        print "Dragged"

    def dropEvent(self, e):
        print "Dropped"    # This is never printed when using QTextBrowser
        print e.mimeData().text()

    def dragMoveEvent(self, inEvent):
        inEvent.accept()

class MyWindow(QWidget):
    def __init__(self, *args):
        QWidget.__init__(self, *args)

        layout = QVBoxLayout(self)
        
        view1 = MyWebView()
        layout.addWidget(view1)
        view1.setAcceptDrops(True)

        view2 = QLineEdit()
        layout.addWidget(view2)
        view2.setAcceptDrops(True)

        QObject.connect(view2, SIGNAL("dragEnterEvent(QDragEnterEvent)"), self.dragReceived)
        QObject.connect(view2, SIGNAL("dropEvent(QDropEvent)"), self.dropReceived)

    def dragReceived(self, e):
        e.accept()
        print "Connect Dragged"

    def dropReceived(self, e):
        print "Connect Dropped"

def main():
    app = QApplication(sys.argv)

    w = MyWindow()
    
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
