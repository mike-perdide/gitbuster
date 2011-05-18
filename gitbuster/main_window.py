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
            model.setMerge(False)
            model.enable_option("filters")
            model.populate()
            self._models[branch] = model

            QObject.connect(model, SIGNAL("newHistoryEvent"),
                            self.new_history_event)

        self.filter_main_class = FilterMainClass(self, directory, self._models)
        self.rebase_main_class = RebaseMainClass(self, directory, self._models)

        self._history = []
        self._last_history_event = -1

        self._ui.progressBar.hide()

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

        # Catching progress bar signals.
        self.connect(self._ui.progressBar, SIGNAL("starting"),
                                                    self.show_progress_bar)
        self.connect(self._ui.progressBar, SIGNAL("update(int)"),
                                                    self.update_progress_bar)
        self.connect(self._ui.progressBar, SIGNAL("stopping"),
                                                    self.hide_progress_bar)

        # Connecting actions
        self.connect(self._ui.actionChange_repository,
                     SIGNAL("triggered(bool)"),
                     self.change_directory)

        action_shortcuts = (
            (self._ui.actionUndo, QKeySequence.Undo, self.undo_history),
            (self._ui.actionRedo, QKeySequence.Redo, self.redo_history),
            (self._ui.actionQuit, QKeySequence.Quit, self.close))
        for action, shortcut, slot in action_shortcuts:
            action.setShortcut(shortcut)
            QObject.connect(action, SIGNAL("triggered()"), slot)

        QObject.connect(self._ui.actionApply, SIGNAL("triggered()"), self.apply)

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

            if ret:
                log_checked = msgBox.log_checked()
                script_checked = msgBox.script_checked()

                self.progress_thread = ProgressThread(self._ui.progressBar,
                                                      msgBox.checked_models(),
                                                      log_checked,
                                                      script_checked)
                self.progress_thread.start()

    def show_progress_bar(self):
        """
            Shows the progress bar representing the progress of the writing
            process.
        """
        self._ui.progressBar.show()
        self._ui.applyButton.setDisabled(True)
        self._ui.cancelButton.setDisabled(True)

    def update_progress_bar(self, value):
        """
            Updates the progress bar with a value.

            :param value:
                Progression of the write process, between 0 and 100
        """
        self._ui.progressBar.setValue(value)

    def hide_progress_bar(self):
        """
            Hide the progress bar representing the progress of the writing
            process.
        """
        self._ui.progressBar.hide()
        self._ui.applyButton.setEnabled(True)
        self._ui.cancelButton.setEnabled(True)
