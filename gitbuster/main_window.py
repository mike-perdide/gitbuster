# main_window.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QMainWindow, QShortcut, QKeySequence, \
                        QApplication
from PyQt4.QtCore import SIGNAL, QObject
from gitbuster.main_window_ui import Ui_MainWindow
from gitbuster.q_git_model import QGitModel
from gitbuster.q_editable_git_model import QEditableGitModel
from gitbuster.confirm_dialog import ConfirmDialog
from gitbuster.util import _connect_button, select_git_directory
from gitbuster.progress_thread import ProgressThread

from gitbuster.filter_main_class import FilterMainClass
from gitbuster.rebase_main_class import RebaseMainClass


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

        self._models = {}
        self._modifications_shown = True

        a_model = QGitModel(directory)
        self.current_branch = a_model.get_current_branch()

        for branch in a_model.get_branches():
            model = QEditableGitModel(self._models, directory=directory)
            model.set_current_branch(branch)
            model.setMerge(True)
            model.enable_option("filters")
            model.populate()
            self._models[branch] = model

            QObject.connect(model, SIGNAL("newHistoryEvent"),
                            self.new_history_event)

        self.filter_main_class = FilterMainClass(self, directory, self._models)
        self.rebase_main_class = RebaseMainClass(self, directory, self._models)

        self._history = []
        self._last_history_event = -1

        self.connect_slots()

    def connect_slots(self):
        """
            Connect the slots to the objects.
        """
        # Bottom bar connections
        _connect_button(self._ui.applyButton, self.apply)
        _connect_button(self._ui.cancelButton, self.close)
        _connect_button(self._ui.toggleModificationsButton,
                                               self.toggle_modifications)

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

    def toggle_modifications(self):
        """
            When the toggleModifications button is pressed, change the displayed
            model.
        """
        if self._modifications_shown:
            label = "&Show modifications"
        else:
            label = "&Hide modifications"

        self._modifications_shown = not self._modifications_shown
        self._ui.toggleModificationsButton.setText(
            QApplication.translate("MainWindow", label,
                                   None, QApplication.UnicodeUTF8))

        self.filter_main_class.toggle_modifications(self._modifications_shown)
        self.rebase_main_class.toggle_modifications(self._modifications_shown)

    def apply(self):
        """
            Write the modifications to the git repository.
        """
        if True in [model.get_modified_count() > 0
                    for model in self._models.values()]:
            msgBox = ConfirmDialog(self._models)
            ret = msgBox.exec_()

#            if ret:
#                ui = msgBox._ui
#                log_checked = ui.logCheckBox.checkState() == Qt.Checked
#                script_checked = ui.scriptCheckBox.checkState() == Qt.Checked
#
#                model.write(log_checked, script_checked)
#
#                # If we have more than 80 commits modified, show progress bar
#                if to_rewrite_count > 80:
#                    progress_bar = self.parent._ui.progressBar
#                    self.progress_thread = ProgressThread(progress_bar, model)
#                    self.progress_thread.start()
#                else:
#                    # Wait a few milliseconds and before repopulating the model
#                    while not model.is_finished_writing():
#                        time.sleep(0.2)
#                    model.populate()
