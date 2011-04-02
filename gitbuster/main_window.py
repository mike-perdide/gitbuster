# main_window.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QMainWindow, QFileDialog
from PyQt4.QtCore import QDir, QSettings, QVariant, SIGNAL
from gitbuster.main_window_ui import Ui_MainWindow
from gitbuster.q_git_model import QGitModel
from gitbuster.q_editable_git_model import QEditableGitModel

from os.path import join, exists

from gitbuster.filter_main_class import FilterMainClass
from gitbuster.rebase_main_class import RebaseMainClass

def is_top_git_directory(filepath):
    git_path = join(filepath, ".git")
    return exists(git_path)

def select_git_directory():
    settings = QSettings("Noname company yet", "gitbuster")

    settings.beginGroup("Last run")

    filepath = '/'
    while not is_top_git_directory(filepath):
        filepath = unicode(QFileDialog.getExistingDirectory(
            None,
            "Open git repository",
            unicode(settings.value("directory", QVariant(QDir.homePath()).toString())),
            QFileDialog.ShowDirsOnly
            ))
        if not filepath:
            return filepath

    settings.setValue("directory", filepath)
    settings.endGroup()
    settings.sync()

    return filepath


class MainWindow(QMainWindow):
    """
        Main Window of gitbuster.
    """

    def __init__(self, directory=".", debug=False):
        """
            Initialisation method, setting the directory.

            :param directory:
                Root directory of the git repository.
        """
        QMainWindow.__init__(self)

        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        models = {}
        a_model = QGitModel(directory)
        for branch in a_model.get_branches():
            model = QEditableGitModel(directory)
            model.set_current_branch(branch)
            model.setMerge(True)
            model.enable_option("filters")
            model.populate()
            models[branch] = model

        self.filter_main_class = FilterMainClass(self, directory, models)
        self.rebase_main_class = RebaseMainClass(self, directory, models)

        # Connecting actions
        self.connect(self._ui.actionQuit, SIGNAL("triggered(bool)"),
                     self.close)

        self.connect(self._ui.actionChange_repository,
                     SIGNAL("triggered(bool)"),
                     self.change_directory)

    def set_current_directory(self, directory):
        """
            Sets the current directory.

            :param directory:
                The git directory.
        """
        self.FilterMainClass.set_current_directory(directory)
        self.FilterMainClass.set_current_directory(directory)

    def change_directory(self):
        """
            When the change directory action is triggered, pop up a dialog to
            select the new directory and set the directory of the model.
        """
        directory = select_git_directory()
        if directory:
            self.set_current_directory(directory)
