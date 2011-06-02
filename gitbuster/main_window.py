# main_window.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from PyQt4.QtCore import QObject, SIGNAL
from PyQt4.QtGui import QApplication, QKeySequence, QMainWindow, QMessageBox
from gitbuster.confirm_dialog import ConfirmDialog
from gitbuster.main_window_ui import Ui_MainWindow
from gitbuster.progress_thread import ProgressThread
from gitbuster.q_editable_git_model import QEditableGitModel
from gitbuster.q_git_model import QGitModel
from gitbuster.util import _connect_button, select_git_directory
from gitbuster.remote_branch_dialog import RemoteBranchDialog

from gitbuster.filter_main_class import FilterMainClass
from gitbuster.rebase_main_class import RebaseMainClass

from git import Repo
from subprocess import Popen, PIPE
import os


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

        self._modifications_shown = True
        self._directory = directory

        self.current_branch = None

        self._models = {}
        self.set_current_directory(directory)

        self.enable_modifications_buttons(False)

        self.filter_main_class = FilterMainClass(self, directory, self._models)
        self.rebase_main_class = RebaseMainClass(self, directory, self._models)

        self.reset_history()

        self._applying = False
        self._ui.progressBar.hide()

        self.connect_slots()

    def create_new_branch_from_model(self, new_name, from_model_row):
        """
        """
        model = QEditableGitModel(self._models, directory=self._directory,
                                  fake_branch_name=new_name,
                                  from_model_row=from_model_row,
                                  parent=self)
        self.add_new_model(model)

    def connect_slots(self):
        """
            Connect the slots to the objects.
        """
        gui = self._ui
        # Bottom bar connections
        _connect_button(gui.applyButton, self.apply)

        # Catching progress bar signals.
        self.connect(gui.progressBar, SIGNAL("starting"),
                                                    self.show_progress_bar)
        self.connect(gui.progressBar, SIGNAL("update(int)"),
                                                    self.update_progress_bar)
        self.connect(gui.progressBar, SIGNAL("stopping"),
                                                    self.hide_progress_bar)

        # Connecting actions
        self.connect(gui.actionChange_repository,
                     SIGNAL("triggered(bool)"),
                     self.change_directory)

        action_shortcuts = (
            (gui.actionUndo, QKeySequence.Undo, self.undo_history),
            (gui.actionRedo, QKeySequence.Redo, self.redo_history),
            (gui.actionQuit, QKeySequence.Quit, self.quit),
            (gui.actionShow_modifications, None, self.show_modifications),
            (gui.actionHide_modifications, None, self.hide_modifications),
            (gui.actionNew_branch, None, self.new_remote_branch),
            (gui.actionApply, None, self.apply))
        for action, shortcut, slot in action_shortcuts:
            if shortcut:
                action.setShortcut(shortcut)
            QObject.connect(action, SIGNAL("triggered()"), slot)

    def new_remote_branch(self):
        """
            Create a new branch.
            This can be a branch build with a directory repository or with an
            URL repository.
        """
        dialog = RemoteBranchDialog(self, self._directory)
        ret = dialog.exec_()

        if ret:
            new_remote = dialog.get_remote()
            new_model = QGitModel(self._directory, remote_ref=new_remote,
                                 parent=self)
            self.add_new_model(new_model)

    def add_new_model(self, model):
        """
            This adds the given model to the two tabs.
        """
        if not isinstance(model, QGitModel):
            model.setMerge(False)
        model.enable_option("filters")

        new_branch = model.get_current_branch() or model.get_remote_ref()
        self._models[new_branch] = model
        QObject.connect(model, SIGNAL("newHistoryEvent"),
                        self.new_history_event)

        self.filter_main_class.add_new_model(model)
        self.rebase_main_class.add_new_model(model)

    def reset_history(self):
        """
            Reset the history (for instance when the apply is finished
            successfully.
        """
        self._history = []
        self._last_history_event = -1

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

            self._history.append([activated_index, opened_model_index, model, []])

        else:
            checkboxes = []
            for checkbox in self.rebase_main_class._checkboxes:
                if checkbox.isChecked():
                    checkboxes.append(checkbox)

            self._history.append([activated_index, checkboxes, model, []])

        self.enable_modifications_buttons(True)

    def enable_modifications_buttons(self, enable):
        """
            Hide or show the two modifications buttons.
        """
        self._ui.actionShow_modifications.setEnabled(enable)
        self._ui.actionHide_modifications.setEnabled(enable)

    def undo_history(self):
        """
            Reverts the history one event back, application wide.
        """
        if self._applying:
            return

        if self._last_history_event >= 0:
            model, actions = self.reproduce_history_conditions()
            model.undo_history()

            for action in actions:
                action.undo()

            self._last_history_event -= 1

        if self._last_history_event == -1:
            self.enable_modifications_buttons(False)

    def redo_history(self):
        """
            Replays the history one event forward, application wide.
        """
        if self._applying:
            return

        if self._last_history_event < len(self._history) - 1:
            model, actions = self.reproduce_history_conditions()
            model.redo_history()

            for action in actions:
                action.redo()

            self._last_history_event += 1

        self.enable_modifications_buttons(True)

    def add_history_action(self, action):
        """
            Add special history actions (actions related to the GUI, not covered
            by the model history). For instance: setting the branch name in the
            name button.
        """
        self._history[self._last_history_event][3].append(action)

    def reproduce_history_conditions(self):
        """
            This method reproduces the settings of the application stored when
            the history event occured.

            :return:
                The model that was modified.
        """
        tab_index, index_or_checkboxes, model, actions = \
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

        return model, actions

    def set_current_directory(self, directory, reset_all=False):
        """
            Sets the current directory.

            :param directory:
                The git directory.
        """
        self._models = {}
        a_model = QGitModel(directory)
        self.current_branch = a_model.get_current_branch()

        for branch in a_model.get_branches():
            model = QEditableGitModel(self._models, directory=directory,
                                      parent=self)
            model.set_current_branch(branch)
            model.setMerge(False)
            model.enable_option("filters")
            model.populate()
            self._models[branch] = model

            QObject.connect(model, SIGNAL("newHistoryEvent"),
                            self.new_history_event)

        if reset_all:
            self.rebase_main_class.reset_interface(self._models)
            self.filter_main_class.reset_interface(self._models)

    def change_directory(self):
        """
            When the change directory action is triggered, pop up a dialog to
            select the new directory and set the directory of the model.
        """
        directory = select_git_directory()
        if directory:
            self.set_current_directory(directory, reset_all=True)

    def show_modifications(self):
        if not self._modifications_shown:
            self.toggle_modifications()

    def hide_modifications(self):
        if self._modifications_shown:
            self.toggle_modifications()

    def toggle_modifications(self):
        """
            When the toggleModifications button is pressed, change the displayed
            model.
        """
        self._modifications_shown = not self._modifications_shown

        self.filter_main_class.toggle_modifications(self._modifications_shown)
        self.rebase_main_class.toggle_modifications(self._modifications_shown)

    def apply(self):
        """
            Write the modifications to the git repository.
        """
        if self._applying:
            # Can't apply if we're already applying
            return


        modified_models = [model for model in self._models.values()
                           if isinstance(model, QEditableGitModel) and
                           (model.get_modified_count > 0 or
                            model.is_modified_name())]

        if modified_models:
            msgBox = ConfirmDialog(modified_models)
            ret = msgBox.exec_()

            if ret and msgBox.checked_models():
                log = msgBox.log_checked()
                force_committed_date = msgBox.force_checked()

                self.apply_models(msgBox.checked_models(), log,
                                  force_committed_date)

    def apply_models(self, models, log, force_committed_date):
        """
            Applies the given models.
        """
        if not self._applying:
            self.progress_thread = ProgressThread(self._ui.progressBar,
                                                  models, log,
                                                  force_committed_date)

            QObject.connect(self.progress_thread, SIGNAL("started()"),
                            self.apply_started)
            QObject.connect(self.progress_thread, SIGNAL("finished()"),
                            self.apply_finished)

            self.progress_thread.start()

    def apply_started(self):
        """
            This method is called when the progress thread is started.
        """
        self._applying = True
        self._ui.applyButton.setDisabled(True)

    def apply_finished(self):
        """
            This method is called when the progress thread is finished.
        """
        self._applying = False
        self._ui.applyButton.setEnabled(True)


        rebuild_fakes = []
        for model, success in self.progress_thread.get_write_success().items():
            if success and model.is_fake_model():
                # If the applied models were fake, rebuild them.
                model.populate()
                rebuild_fakes.append(model)
                QObject.connect(model, SIGNAL("newHistoryEvent"),
                                self.new_history_event)
            elif not success:
                model.reset()
                conflicting_index = model.get_conflicting_index()
                self.rebase_main_class.commit_clicked(conflicting_index)
            elif success:
                model.populate()

        if True in self.progress_thread.get_write_success().values():
            # Reset history
            self.reset_history()
            self.rebase_main_class.apply_finished(rebuild_fakes)

    def show_progress_bar(self):
        """
            Shows the progress bar representing the progress of the writing
            process.
        """
        self._ui.progressBar.show()

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

    def quit(self):
        """
            Display a message if gitbuster is in applying state and quit if the
            user still wants to.
        """
        ret = True
        if self._applying:
            msgBox = QMessageBox(self)
            msgBox.setText("Gitbuster is currently applying !")
            msgBox.setInformativeText("Do you still want to quit ?")
            msgBox.setStandardButtons(msgBox.Cancel | msgBox.Apply)
            msgBox.setDefaultButton(msgBox.Cancel)
            ret = (msgBox.exec_() == msgBox.Apply)

        if ret:
            self.close()

    def closeEvent(self, event):
        """
            Catching the close event to do some cleanup
        """
        def run_command(command):
            Popen(command, shell=True, stdout=PIPE, stderr=PIPE)

        a_repo = Repo(self._directory)
        os.chdir(self._directory)

        if a_repo.active_branch.name == 'gitbuster_rebase':
            if a_repo.is_dirty():
                run_command("git reset --hard")

            fallback_branch_name = [branch.name for branch in a_repo.branches
                                    if branch.name != 'gitbuster_rebase'][0]
            run_command("git checkout %s" % fallback_branch_name)
            run_command("git branch -D gitbuster_rebase")
