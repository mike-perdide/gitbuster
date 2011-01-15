#!/usr/bin/python

# -*- coding: utf-8 -*-

from PyQt4.QtGui import QApplication, QFileDialog
from qGitFilterBranch.main_window import MainWindow
from os.path import join, exists
import sys

def is_top_git_directory(filepath):
    git_path = join(filepath, ".git")
    return exists(git_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    filepath = "/"
    while not is_top_git_directory(filepath):
        fileDialog = QFileDialog()
        filepath = str(fileDialog.getExistingDirectory())
        if not filepath:
            sys.exit(1)

    a = MainWindow(directory=filepath, debug=True)
    a.show()
    sys.exit(app.exec_())
