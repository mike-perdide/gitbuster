# main_window.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QMainWindow, QFileDialog, QShortcut, QKeySequence
from PyQt4.QtCore import QDir, QSettings, QVariant, SIGNAL, QObject
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
        self.current_branch = a_model.get_current_branch()
        for branch in a_model.get_branches():
            model = QEditableGitModel(directory=directory, models_dict=models)
            model.set_current_branch(branch)
            model.setMerge(True)
            model.enable_option("filters")
            model.populate()
            models[branch] = model

            QObject.connect(model, SIGNAL("newHistoryEvent"),
                            self.new_history_event)

        self.filter_main_class = FilterMainClass(self, directory, models)
        self.rebase_main_class = RebaseMainClass(self, directory, models)

        self._history = []
        self._last_history_event = -1

        # Connecting actions
        self.connect(self._ui.actionQuit, SIGNAL("triggered(bool)"),
                     self.close)

        self.connect(self._ui.actionChange_repository,
                     SIGNAL("triggered(bool)"),
                     self.change_directory)

        shortcut = QShortcut(QKeySequence(QKeySequence.Undo), self)
        QObject.connect(shortcut, SIGNAL("activated()"), self.undo_history)

        shortcut = QShortcut(QKeySequence(QKeySequence.Redo), self)
        QObject.connect(shortcut, SIGNAL("activated()"), self.redo_history)

    def new_history_event(self):
        """
            When a history event occurs, we store the tab index, the displayed
            models and the model that was modified.
        """
        while self._last_history_event < len(self._history) - 1:
            self._history.pop()

        self._last_history_event += 1

        model = self.sender()
        activated_index = self._ui.mainTabWidget.currentIndex()
        if activated_index == 0:
            opened_model_index = self._ui.currentBranchComboBox.currentIndex()
            self._history.append((activated_index, opened_model_index, model))
        else:
            checkboxes = []
            for checkbox in self.rebase_main_class._checkboxes:
                if checkbox.isChecked():
                    checkboxes.append(checkbox)
            self._history.append((activated_index, checkboxes, model))

    def undo_history(self):
        """
            Reverts the history one event back, application wide.
        """
        if self._last_history_event >= 0:
            model = self.reproduce_history_conditions()
            model.undo_history()

            if self._last_history_event > -1:
                self._last_history_event -= 1

    def redo_history(self):
        """
            Replays the history one event forward, application wide.
        """
        if self._last_history_event < len(self._history) - 1:
            model = self.reproduce_history_conditions()
            model.redo_history()

            self._last_history_event += 1

    def reproduce_history_conditions(self):
        """
            This method reproduces the settings of the application stored when
            the history event occured.

            :return:
                The model that was modified.
        """
        tab_index, index_or_checkboxes, model = \
                self._history[self._last_history_event]

        self._ui.mainTabWidget.setCurrentIndex(tab_index)
        if tab_index == 0:
            self._ui.currentBranchComboBox.setCurrentIndex(index_or_checkboxes)
        else:
            for checkbox in self.rebase_main_class._checkboxes:
                if checkbox in index_or_checkboxes:
                    checkbox.setChecked(True)
                else:
                    checkbox.setChecked(False)

        return model

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
