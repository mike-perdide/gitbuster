# confirm_dialog.py
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gitbuster and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#

from PyQt4.QtCore import QString, Qt
from PyQt4.QtGui import QCheckBox, QDialog, QLabel
from gitbuster.confirm_dialog_ui import Ui_Dialog
from gitbuster.util import run_long_operation


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
            to_rewrite = run_long_operation("Calculating dependencies",
                                            model.get_to_rewrite_count,
                                            parent=self)
            is_name_modified = model.is_name_modified()

            display_string = ""
            if model.is_fake_model():
                display_string += "New branch."
            else:
                if is_name_modified:
                    display_string += "New name %s." % is_name_modified

                if mod_count:
                    display_string += "%d modified, %d to rewrite." % \
                                      (mod_count, to_rewrite)

            if display_string:
                count_label = QLabel(QString(display_string))
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
