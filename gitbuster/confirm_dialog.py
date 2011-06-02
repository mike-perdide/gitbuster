# confirm_dialog.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from PyQt4.QtCore import QString, Qt
from PyQt4.QtGui import QCheckBox, QDialog, QLabel
from gitbuster.confirm_dialog_ui import Ui_Dialog


class ConfirmDialog(QDialog):

    def __init__(self, models):
        QDialog.__init__(self)

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)

        self._model_checkboxes = []

        row = 1
        for model in models:
            branch_name = model.get_new_branch_name() or \
                          model.get_current_branch().name
            mod_count = model.get_modified_count()
            to_rewrite = model.get_to_rewrite_count()
            is_name_modified = model.is_name_modified()

            if mod_count or is_name_modified:
                count_label = QLabel(QString("%s%d modified, %d to rewrite." %
                                             ("New name, " * is_name_modified,
                                              mod_count, to_rewrite)))
                count_label.setAlignment(Qt.AlignRight)

                checkbox = QCheckBox(self)
                checkbox.setText(QString(branch_name))
                self._ui.branchCountLayout.addWidget(checkbox, row, 0, 1, 2)
                self._ui.branchCountLayout.addWidget(count_label, row, 1, 1, 2)

                self._model_checkboxes.append((checkbox, model))

                row += 1

    def log_checked(self):
        """
            Returns the state of the "Log operations" checkbox.
        """
        return self._ui.logCheckBox.isChecked()

    def force_checked(self):
        """
            Returns the state of the "Force committed date/author" checkbox.
        """
        return self._ui.forceCheckBox.isChecked()

    def checked_models(self):
        """
            Returns the models chosen by the user.
        """
        models = []
        for checkbox, model in self._model_checkboxes:
            if checkbox.isChecked():
                models.append(model)

        return models
