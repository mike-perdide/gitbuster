# confirm_dialog.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QDialog
from gitbuster.confirm_dialog_ui import Ui_Dialog

class ConfirmDialog(QDialog):

    def __init__(self, modified_count=0, to_rewrite_count=0):
        QDialog.__init__(self)

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)

        if modified_count > 1:
            msg = "%d commits have been modified.\n"
        else:
            msg = "%d commit has been modified.\n"

        if to_rewrite_count > 1:
            msg += "%d commits of the git tree are about to be rewritten."
        else:
            msg += "%d commit of the git tree is about to be rewritten."

        self._ui.countLabel.setText(msg % (modified_count, to_rewrite_count))

