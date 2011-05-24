# util.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-
from PyQt4.QtCore import SIGNAL, QObject
from PyQt4.QtGui import QFileDialog
from PyQt4.QtCore import QDir, QSettings, QVariant
from os.path import join, exists


def _connect_button(button, function):
    " Simple method that connects buttons, using the clicked() signal "
    QObject.connect(button, SIGNAL("clicked()"), function)


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
