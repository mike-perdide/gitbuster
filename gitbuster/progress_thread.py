# filter_main_class.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from PyQt4.QtCore import QThread, SIGNAL

import time


class ProgressThread(QThread):
    """
        Thread checking on the git command process, rewriting the
        git repository.
    """

    def __init__(self, progress_bar, models, log, force_committed_date):
        """
            Initializes the thread with the progress bar widget and the
            qGitModel used.

            :param progress_bar:
                Progress bar widdget used to display the progression of the
                git command process.
            :param model:
                The qGitModel used in the MainWindow's view.
            :param log:
                Do we log the writing of the model ?
            :param force_committed_date:
                Do we write the committed date/author according to the model
                data or do we let git update it.
        """
        QThread.__init__(self)

        self._progress_bar = progress_bar
        self._models = models
        self._log = log
        self._force_committed_date = force_committed_date
        self._success = {}

        total_to_rewrite = 0
        for model in self._models:
            total_to_rewrite += model.get_to_rewrite_count()

        # If we have more than 80 commits modified, show progress bar
        self._use_progress_bar = total_to_rewrite > 80

    def run(self):
        """
            Run method of the thread. Will check on the git command process
            progress regularly and updates the progress bar widget.
        """
        total_models = len(self._models)
        progress_bar = self._progress_bar

        if self._use_progress_bar:
            progress_bar.emit(SIGNAL("starting"))
            progress_bar.emit(SIGNAL("update(int)"), 0)

        finished_writing_models = 0
        for model in self._models:
            model.write(self._log, self._force_committed_date,
                        dont_populate=True)

            while not model.is_finished_writing():
                # While the model writing isn't finished, update the  progress
                # bar with the process progress, taking into account the models
                # that are already written.
                progress = model.progress()

                if self._use_progress_bar and progress:
                    global_progress = int(
                            (model.progress() + finished_writing_models) \
                            * 100 / total_models)
                    progress_bar.emit(SIGNAL("update(int)"), global_progress)
                time.sleep(0.5)

            finished_writing_models += 1

            self._success[model] = model.is_write_success()

        if self._use_progress_bar:
            progress_bar.emit(SIGNAL("update(int)"), 100)
            time.sleep(0.2)
            progress_bar.emit(SIGNAL("stopping"))

    def get_write_success(self):
        """
            Returns the successes dictionnary.
        """
        return self._success
