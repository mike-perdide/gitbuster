# util.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from os.path import exists, join

from PyQt4.QtCore import QDir, QObject, QSettings, QVariant, SIGNAL, QUrl,\
        QStringList, QString
from PyQt4.QtGui import QFileDialog


def _connect_button(button, function):
    " Simple method that connects buttons, using the clicked() signal "
    QObject.connect(button, SIGNAL("clicked()"), function)


def is_top_git_directory(filepath):
    git_path = join(filepath, ".git")
    return exists(git_path)


def select_git_directory():
    settings = QSettings("majerti", "gitbuster")
    settings.beginGroup("Last run")

    filepath = '/'
    last_directory = settings.value("directory", QVariant(QDir.homePath()))
    dirs_list = settings.value("recent directories",
                               QStringList()).toStringList()

    recent_dirs_urls = [QUrl.fromLocalFile(dir) for dir in dirs_list]
    home_url = QUrl.fromLocalFile(QDir.homePath())

    while not is_top_git_directory(unicode(filepath)):
        file_dialog = QFileDialog(None, "Open git repository",
                                  last_directory.toString())
        file_dialog.setFileMode(QFileDialog.Directory)
        file_dialog.setOptions(QFileDialog.ShowDirsOnly)
        if recent_dirs_urls:
            file_dialog.setSidebarUrls(
                [home_url,] +
                custom_entries_urls +
                recent_dirs_urls[-6:]
            )
        ret = file_dialog.exec_()

        custom_entries = QStringList()
        custom_entries_urls = []
        for url in file_dialog.sidebarUrls():
            if url not in recent_dirs_urls and url != home_url:
                custom_entries.append(QString(url.path()))
                custom_entries_urls.append(url)
        settings.setValue("custom entries", custom_entries)

        if ret:
            filepath = file_dialog.selectedFiles()[0]
        else:
            return ret

        if not filepath:
            return filepath

    if not dirs_list.contains(filepath):
        dirs_list.append(filepath)
        settings.setValue("recent directories", dirs_list)

    settings.setValue("directory", filepath)
    settings.endGroup()
    settings.sync()

    return unicode(filepath)


class SetNameAction:

    def __init__(self, old_name, new_name, model, button):
        self._old_name = old_name
        self._new_name = new_name
        self._model = model
        self._button = button

    def undo(self):
        self._button.setText(self._old_name)
        self._model.set_new_branch_name(self._old_name)

    def redo(self):
        self._button.setText(self._new_name)
        self._model.set_new_branch_name(self._new_name)
