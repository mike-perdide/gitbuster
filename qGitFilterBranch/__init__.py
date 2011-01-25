# __init__.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of qGitFilterBranch and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
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

def main():
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

