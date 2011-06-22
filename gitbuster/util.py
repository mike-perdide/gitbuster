# util.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from os.path import exists, join
from pprint import pprint
import time

from PyQt4.QtCore import QDir, QObject, QSettings, QVariant, SIGNAL, QUrl,\
        QStringList, QString, Qt, QThread
from PyQt4.QtGui import QFileDialog, QFontMetrics, QDialog

from gitbuster.long_operation_box_ui import Ui_LongOperationBox


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
    custom_entries = settings.value("custom entries",
                                    QStringList()).toStringList()

    recent_dirs_urls = [QUrl.fromLocalFile(dir) for dir in dirs_list]
    home_url = QUrl.fromLocalFile(QDir.homePath())
    custom_entries_urls = [QUrl.fromLocalFile(dir) for dir in custom_entries]

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


def custom_resize_columns_to_contents(view):

    model = view.model()
    font = view.font()

    MAGIC_NUMBERS = {"hexsha": 1.4,
                     "authored_date" : 1.1,
                     "committed_date" : 1.1}

    for column, field in enumerate(model.get_columns()):
        # Use QFontMetrics to find out the proper size.
        if "name" in field:
            width_set = []
            for row in xrange(30):
                item = model.data(model.createIndex(row, column), Qt.DisplayRole)
                metrics = QFontMetrics(font)
                width = metrics.width(item.toString())
                width_set.append(width)
            width = max(width_set)
        else:
            item = model.data(model.createIndex(0, column), Qt.DisplayRole)
            metrics = QFontMetrics(font)
            width = metrics.width(item.toString())

        if field in MAGIC_NUMBERS:
            magic = MAGIC_NUMBERS[field]
        else:
            magic = 1.2

        view.setColumnWidth(column, int(width * magic))


class SetNameAction:

    def __init__(self, old_name, new_name, checkbox, button, original_name):
        self._old_name = old_name or original_name
        self._new_name = new_name
        self._checkbox = checkbox
        self._button = button
        self._original_name = original_name

    def undo(self):
        if self._old_name != self._original_name:
            self._button.setText(self._old_name + "  (new name)")
        else:
            self._button.setText(self._old_name)
        self._checkbox.setText(self._old_name)

    def redo(self):
        if self._new_name != self._original_name:
            self._button.setText(self._new_name + "  (new name)")
        else:
            self._button.setText(self._new_name)
        self._checkbox.setText(self._new_name)


class DummyRemoveAction:

    def __init__(self, row, view):
        self._row = row
        self._view = view

    def undo(self):
        self._view.showRow(self._row)

    def redo(self):
        self._view.hideRow(self._row)


class Timer:
    records = {}

    def __init__(self, record=None):
        if record is None:
            self.render_records()
        self._record = record
        self._start_time = time.time()

    def stop(self):
        if not self._record in self.records:
            self.records[self._record] = []
        self.records[self._record].append("%.4f" %
                                          (time.time() - self._start_time))

    def render_records(self):
        pprint(self.records)

class RunLongOperation(QThread):

    def __init__(self, operation, args, kwargs):
        QThread.__init__(self)
        self._operation = operation
        self._args = args
        self._kwargs = kwargs
        self._result = None

    def run(self):
        self._result = self._operation(*self._args, **self._kwargs)

    def result(self):
        return self._result

class ProgressOperation(QThread):

    def __init__(self, operation):
        QThread.__init__(self)
        self._operation = operation

    def run(self):
        while True:
            progress = self._operation()
            self.emit(SIGNAL("update"), progress)
            time.sleep(0.5)

class LongOperationBox(QDialog):

    def __init__(self, text, operation, args=[], kwargs={},
                 progress_method = None, parent=None):
        QDialog.__init__(self, parent)

        self._ui = Ui_LongOperationBox()
        self._ui.setupUi(self)
        self._ui.label.setText(text)

        self._operation = operation
        self._progress_method = progress_method

        self._thread = RunLongOperation(operation, args, kwargs)
        self.connect(self._thread, SIGNAL("finished()"), self.thread_finished)

        self._progress_thread = None
        if self._progress_method:
            self._progress_thread = ProgressOperation(self._progress_method)
            self.connect(self._progress_thread, SIGNAL("update"), self.update)
            self._ui.progressBar.setValue(0)

    def thread_finished(self):
        if self._progress_thread:
            self._progress_thread.terminate()
        self.accept()

    def update(self, value):
        if value:
            self._ui.progressBar.setValue(int(value * 100))

    def result(self):
        return self._thread.result()

    def exec_(self):
        self._thread.start()
        if self._progress_thread:
            self._progress_thread.start()
        QDialog.exec_(self)

def run_long_operation(text, operation, args=[], kwargs={},
                       progress_method=None, parent=None):
        long_box = LongOperationBox(text,
                                    operation, args=args, kwargs=kwargs,
                                    progress_method=progress_method,
                                    parent=parent)
        long_box.exec_()
        return long_box.result()
