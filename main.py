import sys
from dataclasses import dataclass
from contextlib import contextmanager

from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QRegularExpression,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import QAction, QColor, QKeySequence, QUndoCommand, QUndoStack
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QDockWidget,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QStyledItemDelegate,
    QToolBar,
    QTreeView,
    QUndoView,
    QVBoxLayout,
    QWidget,
)


@dataclass
class PropertyItem:
    name: str
    value: any
    type: str


class ColorDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QColorDialog(parent)

    def setEditorData(self, editor, index):
        editor.setCurrentColor(QColor(index.model().data(index, Qt.EditRole)))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentColor().name(), Qt.EditRole)


class StringDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QLineEdit(parent)

    def setEditorData(self, editor, index):
        editor.setText(index.model().data(index, Qt.EditRole))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), Qt.EditRole)


class PropertyModel(QAbstractItemModel):
    afterDataChanged = Signal(object, object, object)

    def __init__(self, properties=None, parent=None):
        super().__init__(parent)
        self.properties = properties or []
        self.headers = ["Property", "Value"]
        self.is_undo_redo = False
        self.even_row_color = QColor("#000000")
        self.odd_row_color = QColor("#000000")

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self.properties)
        return 0

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        property_item = self._get_property_item(index)

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column() == 0:
                return property_item.name
            elif index.column() == 1:
                return property_item.value
        elif role == Qt.BackgroundRole:
            return self.even_row_color if index.row() % 2 == 0 else self.odd_row_color
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        return self.createIndex(row, column)

    def parent(self, index):
        return QModelIndex()

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and role == Qt.EditRole:
            property_item = self._get_property_item(index)

            if index.column() == 1:
                old_value = property_item.value
                if old_value != value:
                    property_item.value = value
                    self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
                    if not self.is_undo_redo:
                        self.afterDataChanged.emit(index, old_value, value)
                    return True
        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() == 1:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def _get_property_item(self, index):
        return self.properties[index.row()]

    def getPropertyType(self, index):
        if not index.isValid():
            return None

        property_item = self._get_property_item(index)
        return property_item.type

    @contextmanager
    def undo_redo_context(self):
        self.is_undo_redo = True
        try:
            yield
        finally:
            self.is_undo_redo = False

    def setEvenRowColor(self, color):
        self.even_row_color = QColor(color)
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1), [Qt.BackgroundRole])

    def setOddRowColor(self, color):
        self.odd_row_color = QColor(color)
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1), [Qt.BackgroundRole])


class PropertyChangeCommand(QUndoCommand):
    def __init__(self, model, index, old_value, new_value):
        super().__init__()
        self.model = model
        self.index = index
        self.old_value = old_value
        self.new_value = new_value
        self.setText(f"Change property from '{old_value}' to '{new_value}'")

    def redo(self):
        with self.model.undo_redo_context():
            self.model.setData(self.index, self.new_value, Qt.EditRole)

    def undo(self):
        with self.model.undo_redo_context():
            self.model.setData(self.index, self.old_value, Qt.EditRole)


class PropertyEditor(QTreeView):
    def __init__(self, properties=None, parent=None):
        super().__init__(parent)
        self.delegates = {
            "string": StringDelegate(),
            "color": ColorDelegate(),
        }

        self._model = PropertyModel(properties)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self._model)
        self.setModel(self.proxy_model)

    def get_model(self):
        return self._model

    def setModel(self, proxy_model):
        super().setModel(proxy_model)

        source_model = proxy_model.sourceModel()

        for row in range(proxy_model.rowCount()):
            proxy_index = proxy_model.index(row, 1)
            source_index = proxy_model.mapToSource(proxy_index)
            property_type = source_model.getPropertyType(source_index)
            delegate = self.delegates.get(property_type, StringDelegate())
            self.setItemDelegateForRow(row, delegate)
            print(
                f"Set delegate '{delegate.__class__.__name__}' for row {row} (Property: '{source_model.data(source_model.index(source_index.row(), 0))}')"
            )

    def setFilter(self, filter_pattern):
        print("Setting filter:", filter_pattern)

        filter_regex = QRegularExpression(filter_pattern)
        self.proxy_model.setFilterRegularExpression(filter_regex)
        self.setModel(self.proxy_model)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.undoStack = QUndoStack(self)

        self.editor_widget = PropertyEditor(
            properties=[
                PropertyItem("Name1", "Process 1", "string"),
                PropertyItem("Name2", "Process 2", "string"),
                PropertyItem("Color", "#ff0000", "color"),
                PropertyItem("Name3", "Process 3", "string"),
            ]
        )
        self.model = self.editor_widget.get_model()
        self.model.afterDataChanged.connect(self.afterDataChanged)

        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createUndoView()

        self.setWindowTitle("Undo Framework")

        filter_widget = QLineEdit()
        filter_widget.setPlaceholderText("Filter properties...")
        filter_widget.textChanged.connect(self.setFilter)

        filter_layout = QVBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"), alignment=Qt.AlignTop)
        filter_layout.addWidget(filter_widget, alignment=Qt.AlignTop)
        filter_layout.setSpacing(0)
        filter_layout.setContentsMargins(0, 0, 0, 0)

        property_editor_layout = QVBoxLayout()
        property_editor_layout.addLayout(filter_layout)
        property_editor_layout.addWidget(self.editor_widget)
        w = QWidget()
        w.setLayout(property_editor_layout)

        self.setCentralWidget(w)
        self.adjustSize()

    def setFilter(self, filter_text):
        self.editor_widget.setFilter(filter_text)

    def afterDataChanged(self, index, old_value, new_value):
        command = PropertyChangeCommand(self.model, index, old_value, new_value)
        self.undoStack.push(command)

    def createUndoView(self):
        undoDockWidget = QDockWidget("Command List")
        undoDockWidget.setWidget(QUndoView(self.undoStack))
        self.addDockWidget(Qt.RightDockWidgetArea, undoDockWidget)

    def createActions(self):
        self.undoAction = self.undoStack.createUndoAction(self, "&Undo")
        self.undoAction.setShortcuts(QKeySequence.Undo)

        self.redoAction = self.undoStack.createRedoAction(self, "&Redo")
        self.redoAction.setShortcuts(QKeySequence.Redo)

        self.exitAction = QAction("Exit", self)
        self.exitAction.setShortcuts(QKeySequence.Quit)
        self.exitAction.triggered.connect(self.close)

        self.aboutAction = QAction("About", self)
        self.aboutAction.triggered.connect(self.about)

        self.setEvenRowColorAction = QAction("Set Even Row Color", self)
        self.setEvenRowColorAction.triggered.connect(self.setEvenRowColor)

        self.setOddRowColorAction = QAction("Set Odd Row Color", self)
        self.setOddRowColorAction.triggered.connect(self.setOddRowColor)

        self.setBackgroundColorAction = QAction("Set Background Color", self)
        self.setBackgroundColorAction.triggered.connect(self.setBackgroundColor)

    def createMenus(self):
        menuBar = QMenuBar(self)
        fileMenu = menuBar.addMenu("&File")
        fileMenu.addAction(self.exitAction)

        editMenu = menuBar.addMenu("&Edit")
        editMenu.addAction(self.undoAction)
        editMenu.addAction(self.redoAction)

        viewMenu = menuBar.addMenu("&View")
        viewMenu.addAction(self.setEvenRowColorAction)
        viewMenu.addAction(self.setOddRowColorAction)
        viewMenu.addAction(self.setBackgroundColorAction)

        helpMenu = menuBar.addMenu("&Help")
        helpMenu.addAction(self.aboutAction)

        self.setMenuBar(menuBar)

    def createToolBars(self):
        editToolBar = QToolBar("Edit", self)
        editToolBar.addAction(self.undoAction)
        editToolBar.addAction(self.redoAction)
        self.addToolBar(editToolBar)

    def setEvenRowColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.model.setEvenRowColor(color)

    def setOddRowColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.model.setOddRowColor(color)

    def setBackgroundColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.setStyleSheet(f"QMainWindow {{ background-color: {color.name()}; }}")

    def about(self):
        QMessageBox.about(self, "About Undo Framework", "This example demonstrates the use of the QUndoStack class.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
