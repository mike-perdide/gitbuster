
from PyQt4.QtGui import QApplication, QCheckBox, QGridLayout, QKeySequence,\
     QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QShortcut, QTableView,\
     QWidget, QFont, QTableView
from PyQt4.QtCore import QObject, Qt, SIGNAL
connect = QObject.connect

from gitbuster.branch_view_ui import Ui_BranchView
from gitbuster.util import SetNameAction, DummyRemoveAction


class ButtonLineEdit(QWidget):
    """
    This widget provides a button that displays a changeable text,
    and the text can be edited in place thanks to a lineedit
    """

    def __init__(self, history_mgr, model, checkbox, parent=None):
        QWidget.__init__(self, parent)

        #data stored here for convenience
        self.history_mgr = history_mgr
        self.model = model
        self.new_name = model.get_old_branch_name()
        self.checkbox = checkbox

        #widgets. Maybe we should use designer here.
        name_label_font = QFont()
        name_label_font.setBold(True)
        self.current_name_label = QLabel(self)
        self.current_name_label.setMinimumHeight(23)
        self.current_name_label.setToolTip("Branch name. Click to change.")
        self.current_name_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.current_name_label.setFont(name_label_font)
        self.label = QLabel()
        self.editor = QLineEdit(self)
        self.valid_button = QPushButton("Ok")
        #layout
        self.box = QGridLayout(self)
        self.box.addWidget(self.current_name_label, 0, 0, 1, 3)
        self.box.addWidget(self.label, 1, 0, 1, 1)
        self.box.addWidget(self.editor, 1, 1, 1, 1)
        self.box.addWidget(self.valid_button, 1, 2, 1, 1)

        #initial state of the widget
        self._readmode()

        #initial load of data
        branch = self.model.get_current_branch() or self.model.get_remote_ref()
        self.current_name_label.setText(branch.name)

        #make it live
        QObject.connect(self.current_name_label,
                        SIGNAL("customContextMenuRequested(const QPoint&)"),
                        self.context_menu)
        QObject.connect(self.editor, SIGNAL("returnPressed()"), self.go_read)
        QObject.connect(self.valid_button, SIGNAL("clicked()"), self.go_read)

    def _iter_widgets(self):
        """
        yields widgets and their belonging to edit (True) or read (False) mode
        """
        yield self.valid_button, True
        yield self.editor, True
        yield self.label, True
        yield self.current_name_label, False

    def _editmode(self):
        for widget, is_edit in self._iter_widgets():
            widget.setVisible(is_edit)

    def go_edit(self):
        self._editmode()
        name = self.model.get_current_branch().name
        self.label.setText(u"<span>"
            "Change &#147;<i>%(name)s</i>&#148; into"
            "</span>" %
            {'name': name})
        self.editor.setText(self.new_name or name)

    def _readmode(self):
        for widget, is_edit in self._iter_widgets():
            widget.setVisible(not is_edit)

    def go_read(self):
        old_name = self.new_name
        new_name = unicode(self.editor.text()).strip()
        old_branch_name = self.model.get_old_branch_name()

        if self.new_name == new_name:
            # The name hasn't changed.
            self._readmode()
            return

        valid_name, error = self.model.is_valid_branch_name(new_name)

        if not valid_name:
            # The branch name isn't valid.
            QMessageBox.warning(self, "Naming error", error.args[0])
            return

        # The branch name is valid.
        self.new_name = new_name

        # Setting the new branch name on the model and creating history events
        self.model.start_history_event()
        self.model.set_new_branch_name(new_name)
        action = SetNameAction(old_name, new_name,
                               self.checkbox,
                               self.current_name_label,
                               old_branch_name)
        self.history_mgr.add_history_action(action)

        # Displaying the new branch name
        if new_name != old_branch_name:
            self.current_name_label.setText(new_name + "  (new name)")
        else:
            self.current_name_label.setText(new_name)
        self.checkbox.setText(new_name)

        self._readmode()

    def context_menu(self, q_point):
        """
            Creates a menu with the actions:
                - edit
                - delete (not implemented yet)
                - copy to new branch (not implemented yet)
        """
        menu = QMenu(self)
        edit_action = menu.addAction("edit")

        choosed_action = menu.exec_(self.sender().mapToGlobal(q_point))

        if choosed_action == edit_action:
            self.go_edit()

    def reset_displayed_name(self):
        """
            When the apply is finished, we may want to check that the model's
            branch name is not new anymore.
        """
        branch = self.model.get_current_branch() or self.model.get_remote_ref()
        self.current_name_label.setText(branch.name)


class BranchView(QWidget):
    """
        This is a widget containing the tableView and the ButtonLineEdit with
        the branch name.
    """

    def __init__(self, parent, model, checkbox, all_models):
        QWidget.__init__(self, parent)

        self._ui = Ui_BranchView()
        self._ui.setupUi(self)

        self._model = model
        self._all_models = all_models
        self._parent = parent

        self._table_view = QTableView(parent)
        self._table_view.setModel(model)

        self._name_widget = ButtonLineEdit(parent.parent(), model, checkbox)
        self._ui.layout.addWidget(self._name_widget, 0, 0)
        self._ui.layout.addWidget(self._table_view, 1, 0)

        #name = ButtonLineEdit(self.parent, model, checkbox)
        #place = position * 7

        #self._ui.viewLayout.addWidget(name, 0, place)
        #self._ui.viewLayout.addWidget(branch_view, 1, place)

        self.connect_signals()

    def connect_signals(self):
        """
            Connect the right signals to the right slots.
        """
        shortcut = QShortcut(QKeySequence(QKeySequence.Delete), self._parent)
        QObject.connect(shortcut, SIGNAL("activated()"), self.remove_rows)

        connect(self._table_view,
                SIGNAL("customContextMenuRequested(const QPoint&)"),
                self.context_menu)

        signals = "activated(const QModelIndex&)", "clicked(const QModelIndex&)"
        for signal in signals:
            connect(self._table_view, SIGNAL(signal), self.commit_clicked)

    def commit_clicked(self, index):
        self.emit(SIGNAL("activated(const QModelIndex&)"), index)

    def context_menu(self, q_point):
        """
            Creates a menu with the actions:
                - copy
                - delete
                - paste after
                - paste before
        """
        menu = QMenu(self._parent)
        table_view = self._table_view

        indexes = table_view.selectedIndexes()
        selected_rows = set([index.row() for index in indexes])
        copy_data = self._parent.get_copy_data()

        copy_action = menu.addAction("Copy")
        delete_action = menu.addAction("Delete")
        paste_after_action = menu.addAction("Paste after")
        paste_after_action.setDisabled(copy_data == "")
        paste_before_action = menu.addAction("Paste before")
        paste_before_action.setDisabled(copy_data == "")
        create_branch_action = menu.addAction("Create branch from this commit")

        choosed_action = menu.exec_(table_view.viewport().mapToGlobal(q_point))

        if choosed_action == delete_action:
            self.remove_rows()

        elif choosed_action == copy_action:
            self._parent.set_copy_data(table_view.model().mimeData(indexes))

        elif choosed_action == paste_after_action:
            drop_after = max(selected_rows) + 1
            table_view.model().dropMimeData(copy_data, Qt.CopyAction,
                                            drop_after, 0, self.parent)

        elif choosed_action == paste_before_action:
            drop_before = min(selected_rows)
            table_view.model().dropMimeData(copy_data, Qt.CopyAction,
                                            drop_before, 0, self.parent)

        elif choosed_action == create_branch_action:
            self.emit(SIGNAL("newBranchFromCommit"), indexes)

    def remove_rows(self):
        """
            When <Del> is pressed, this method removes the selected rows of the
            table view.

            We delete the rows starting with the last one, in order to use the
            correct indexes.
        """
        table_view = self._table_view
        if table_view is None:
            return False

        selected_indexes = [index for index in table_view.selectedIndexes()
                            if index.isValid()]
        model = table_view.model()

        ordered_list = []
        deleted_dummies = []
        for index in selected_indexes:
            if index.row() not in ordered_list and \
               not model.is_deleted(index) and \
               not model.is_first_commit(index):
                # Don't delete deleted or first commits.
                ordered_list.insert(0, index.row())
            if model.is_inserted_commit(index):
                deleted_dummies.append(index.row())

        if ordered_list:
            model.start_history_event()
        for dummy_row in deleted_dummies:
            # Special behaviour for inserted commits: hide them
            self.parent.add_history_action(DummyRemoveAction(dummy_row,
                                                             table_view))
            table_view.hideRow(dummy_row)

        for row in ordered_list:
            model.removeRows(row)

    def model(self):
        """
            Return the QTableView model.
        """
        return self._model

    def set_model(self, model):
        """
            Sets the QTableView model and the label's name.
        """
        # XXX
        table_view = self._table_view
        show_fields = ("hexsha", "message")
        for column, field in enumerate(model.get_columns()):
            if not field in show_fields:
                table_view.hideColumn(column)
        table_view.resizeColumnsToContents()
        table_view.horizontalHeader().setStretchLastSection(True)
        table_view.setSelectionMode(table_view.ExtendedSelection)
        table_view.setDragDropMode(table_view.DragDrop)
        table_view.setSelectionBehavior(table_view.SelectRows)
        table_view.setEditTriggers(table_view.NoEditTriggers)
        table_view.setContextMenuPolicy(Qt.CustomContextMenu)

        table_view.setModel(model)

    def show_modifications(self):
        pass
        #if hasattr(model, 'get_orig_q_git_model'):

    def reset_displayed_name(self):
        self._name_widget.reset_displayed_name()
