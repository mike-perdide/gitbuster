# conflicts_dialog.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt

from PyQt4.QtGui import QDialog
from PyQt4.QtCore import QString, QObject, SIGNAL
from gitbuster.remote_branch_dialog_ui import Ui_Form
from gitbuster.util import select_git_directory

from git import Repo

connect = QObject.connect

class RemoteBranchDialog(QDialog):

    def __init__(self, parent, directory):
        """
            Initializes the dialog.
            
            :param model:
                The directory of the repository.
        """
        QDialog.__init__(self)

        self._ui = Ui_Form()
        self._ui.setupUi(self)

        self._directory = directory
        self._existing_remotes = self.get_existing_remotes()
        self._created_remotes = []
        self._remote = None
        self._remote_ref = None

        type_items = "New web remote", "New directory remote"
        for type in type_items:
            self._ui.remoteComboBox.insertItem(0, QString(type))

        # Populate the remoteComboBox with the existing remotes
        for remote in self._existing_remotes:
            self._ui.remoteComboBox.insertItem(0, QString(remote))

        self._ui.remoteComboBox.insertItem(0, QString(""))
        self._ui.remoteComboBox.setCurrentIndex(0)

        self.connect_signals()
        self.remote_type_mode()

    def connect_signals(self):
        """
            Connecting widgets to slots.
        """
        connect(self._ui.remoteComboBox, SIGNAL("activated(const QString&)"),
                self.location_mode)

        connect(self._ui.locationDialogButton, SIGNAL("clicked()"),
                self.location_toolbox_clicked)

        connect(self._ui.locationLineEdit, SIGNAL("returnPressed()"),
                self.fetch_clicked)

        connect(self._ui.fetchButton, SIGNAL("clicked()"), self.fetch_clicked)

        connect(self._ui.branchComboBox, SIGNAL("activated(const QString&)"),
                self.branch_chosen)

        connect(self._ui.cancelButton, SIGNAL("clicked()"), self.close)
        connect(self._ui.addButton, SIGNAL("clicked()"), self.accept)

    def get_existing_remotes(self):
        """
            This returns the existing remotes in the repository.

            :returns:
                If we have already fetch remotes, re-use them.
                This is a dictionnary like:
                    existing_remotes[remote_name] = remote_url
        """
        a_repo = Repo(self._directory)
        existing_remotes = {}
        remote_output = " ".join(a_repo.git.remote("-v").split("\t"))
        remotes = [remote.split(" ") for remote in remote_output.split("\n")
                   if remote]
        for remote_name, url, mode in remotes:
            existing_remotes[url] = remote_name

        return existing_remotes

    def widget_display_mode(self):
        yield self._ui.locationLabel, "location"
        yield self._ui.locationLineEdit, "location"
        yield self._ui.locationDialogButton, "location-directory"
        yield self._ui.fetchButton, "fetch"
        yield self._ui.branchLabel, "branch"
        yield self._ui.branchComboBox, "branch"
        yield self._ui.addButton, "add"

    def remote_type_mode(self):
        """
            In this mode, the user selects either an existing remote or the
            type of the new remote (directory or web).
        """
        for widget, mode in self.widget_display_mode():
            widget.hide()

    def location_mode(self, remote_type_or_name):
        """
            In this mode, the user enters the location of the remote repository.
        """
        # Hide the branch widgets if necessary
        for widget, mode in self.widget_display_mode():
            widget.hide()

        remote = unicode(remote_type_or_name)
        if not remote:
            return

        if remote in self._existing_remotes:
            self._ui.locationLineEdit.setText(QString(remote))
            self.fetch_clicked()
            return

        if "directory" in remote:
            for widget, mode in self.widget_display_mode():
                if "location" in mode:
                    widget.show()

        elif "web" in remote:
            for widget, mode in self.widget_display_mode():
                if mode == "location":
                    widget.show()

        self._ui.locationLineEdit.clear()

    def location_toolbox_clicked(self):
        """
            Pop the QFileDialog.
        """
        self.remote_directory = select_git_directory()
        if self.remote_directory:
            self._ui.locationLineEdit.setText(QString(self.remote_directory))
            self.fetch_mode()

    def fetch_mode(self):
        for widget, mode in self.widget_display_mode():
            if mode == "fetch":
                widget.show()

    def fetch_clicked(self):
        """
            When the Fetch button is clicked, we fetch the remote references.
        """
        a_repo = Repo(self._directory)
        remote_url = unicode(self._ui.locationLineEdit.text())
        if remote_url in self._existing_remotes:
            self._remote = a_repo.remotes[self._existing_remotes[remote_url]]
        else:
            id = 0
            available_name = "remote" + str(id)
            while available_name in self._existing_remotes.values():
                id += 1
                available_name = "remote" + str(id)
            self._remote = a_repo.create_remote(available_name, remote_url)
            self._remote.fetch()
            self._created_remotes.append(self._remote)

        # When fetching a second time, we will only have the branches
        fetch_refs = self._remote.fetch()
        self._ui.branchComboBox.clear()
        for fetch_info in fetch_refs:
            self._ui.branchComboBox.insertItem(0, fetch_info.name)
        self._ui.branchComboBox.insertItem(0, QString(""))
        self._ui.branchComboBox.setCurrentIndex(0)

        self.branch_mode()

    def branch_mode(self):
        """
            This displays the widgets associated with the branch mode.
        """
        for widget, mode in self.widget_display_mode():
            if mode == "branch":
                widget.show()
            elif mode == "fetch":
                widget.hide()

    def branch_chosen(self, branch_name):
        """
            This is the method that is called when the branch is chosen on the
            branchComboBox.
        """
        selected_branch = unicode(branch_name)
        if branch_name:
            for widget, mode in self.widget_display_mode():
                if mode == "add":
                    widget.show()
        
        self._remote_ref = [branch_ref for branch_ref in self._remote.fetch()
                            if branch_ref.name == selected_branch][0]

    def cleanup(self):
        """
            Removes the created repository that won't be used.
        """
        for remote in self._created_remotes:
            if remote == self._remote:
                continue
            # This wasn't the we need to remove this remote.
            a_repo = Repo(self._directory)
            a_repo.git.remote("rm " + self._remote)

    def close(self):
        """
            When cancel is clicked, we should cleanup the repository i.e.
            remove the remote we may have created.
        """
        self.cleanup()
        QDialog.close(self)

    def reject(self):
        """
            When the dialog is closed, we should cleanup the repository i.e.
            remove the remote we may have created.
        """
        self.cleanup()
        QDialog.reject(self)

    def get_remote(self):
        """
            One the dialog is closed, this can be used to get the chosen
            remote.
        """
        return self._remote_ref
