# confirm_dialog.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QDialog, QCheckBox, QApplication, QLabel
from PyQt4.QtCore import QString, Qt
from gitbuster.confirm_dialog_ui import Ui_Dialog

class ConfirmDialog(QDialog):

    def __init__(self, models):
        QDialog.__init__(self)

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)

        row = 1
        for branch, model in models.items():
            mod_count  = model.get_modified_count()
            to_rewrite = model.get_to_rewrite_count()

            if mod_count:
                count_label = QLabel(QString("%d modified, %d to rewrite." %
                                             (mod_count, to_rewrite)))
                count_label.setAlignment(Qt.AlignRight)

                checkbox = QCheckBox(self)
                checkbox.setText(QString(branch.name))
                self._ui.branchCountLayout.addWidget(checkbox, row, 0, 1, 2)
                self._ui.branchCountLayout.addWidget(count_label, row, 1, 1, 2)
    
                row += 1

        #if modified_count > 1:
        #    msg = "%d commits have been modified.\n"
        #else:
        #    msg = "%d commit has been modified.\n"

        #if to_rewrite_count > 1:
        #    msg += "%d commits of the git tree are about to be rewritten."
        #else:
        #    msg += "%d commit of the git tree is about to be rewritten."

#        self._ui.countLabel.setText(msg % (modified_count, to_rewrite_count))

