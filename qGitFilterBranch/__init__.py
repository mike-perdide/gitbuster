# -*- coding: utf-8 -*-

from PyQt4.QtCore import QDir, QSettings
from PyQt4.QtGui import QApplication, QFileDialog
from qGitFilterBranch.main_window import MainWindow
from os import environ
from os.path import join, exists
import sys

def is_top_git_directory(filepath):
    git_path = join(filepath, ".git")
    return exists(git_path)

def run():
    app = QApplication(sys.argv)

    settings = QSettings("Noname company yet", "qGitFilterBranch")

    settings.beginGroup("Last run")

    filepath = '/'
    while not is_top_git_directory(filepath):
        filepath = unicode(QFileDialog.getExistingDirectory(
            None,
            "Open git repository",
            unicode(settings.value("directory", QDir.homePath()).toString()),
            QFileDialog.ShowDirsOnly
            ))
        if not filepath:
            sys.exit(1)

    settings.setValue("directory", filepath)
    settings.endGroup()
    settings.sync()

    a = MainWindow(directory=filepath, debug=True)
    a.show()
    sys.exit(app.exec_())

