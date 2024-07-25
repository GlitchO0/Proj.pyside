import sys
from dataclasses import dataclass
from contextlib import contextmanager

from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QRegularExpression,
    QSortFilterProxyModel,
    Qt,
    Signal, QDate, QDateTime, QTime, QByteArray,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QCursor,
    QFont,
    QKeySequence,
    QPixmap,
    QUndoCommand,
    QUndoStack, QVector2D,
)
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QDateEdit,
    QDateTimeEdit,
    QFileDialog,
    QFontDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QSpinBox,
    QStyledItemDelegate,
    QTimeEdit,
    QToolBar,
    QTreeView,
    QUndoView,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QDoubleSpinBox,
    QDockWidget,
    QComboBox,
    QPushButton,
    QHBoxLayout
, QKeySequenceEdit, QListWidget, QAbstractItemView, QListWidgetItem

)


@dataclass
class PropertyItem:
    name: str
    value: any
    type: str


class SetRowColorCommand(QUndoCommand):
    def __init__(self, model, color_type, old_color, new_color):
        super().__init__()
        self.model = model
        self.color_type = color_type
        self.old_color = old_color
        self.new_color = new_color
        self.setText(f"Change {color_type} row color from '{old_color.name()}' to '{new_color.name()}'")

    def redo(self):
        if self.color_type == 'even':
            self.model.setEvenRowColor(self.new_color)
        elif self.color_type == 'odd':
            self.model.setOddRowColor(self.new_color)

    def undo(self):
        if self.color_type == 'even':
            self.model.setEvenRowColor(self.old_color)
        elif self.color_type == 'odd':
            self.model.setOddRowColor(self.old_color)


class SetBackgroundColorCommand(QUndoCommand):
    def __init__(self, window, old_color, new_color):
        super().__init__()
        self.window = window
        self.old_color = old_color
        self.new_color = new_color
        self.setText(f"Change background color from '{old_color.name()}' to '{new_color.name()}'")

    def redo(self):
        self.window.applyBackgroundColor(self.new_color)

    def undo(self):
        self.window.applyBackgroundColor(self.old_color)


class ColorButton(QWidget):
    colorChanged = Signal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = QColor()
        self.button = QPushButton()
        self.button.clicked.connect(self.openColorDialog)
        layout = QHBoxLayout()
        layout.addWidget(self.button)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setAutoFillBackground(True)
        self.updateButtonColor()

    def openColorDialog(self):
        color = QColorDialog.getColor(self.color, self)
        if color.isValid():
            self.setColor(color)

    def setColor(self, color):
        self.color = color
        self.updateButtonColor()
        self.colorChanged.emit(color)

    def getColor(self):
        return self.color

    def updateButtonColor(self):
        self.button.setStyleSheet(f'background-color: {self.color.name()};')


class ColorDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = ColorButton(parent)
        editor.colorChanged.connect(self.commitAndCloseEditor)
        return editor

    def setEditorData(self, editor, index):
        color = QColor(index.model().data(index, Qt.EditRole))
        editor.setColor(color)

    def setModelData(self, editor, model, index):
        color = editor.getColor().name()
        if model.data(index, Qt.EditRole) != color:
            model.setData(index, color, Qt.EditRole)
            # Trigger the background color change for the rows
            model.dataChanged.emit(index, index, [Qt.BackgroundRole])

    def commitAndCloseEditor(self, color):
        editor = self.sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)


# StringDelegate
class StringDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QLineEdit(parent)

    def setEditorData(self, editor, index):
        editor.setText(index.model().data(index, Qt.EditRole))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), Qt.EditRole)


# StringListDelegate (list of strings)
class StringListDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        string_list = index.model().data(index, Qt.EditRole)
        if isinstance(string_list, list):
            editor.setText(', '.join(string_list))

    def setModelData(self, editor, model, index):
        text = editor.text()
        string_list = text.split(', ')
        model.setData(index, string_list, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


# BoolDelegate
class BoolDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QCheckBox(parent)

    def setEditorData(self, editor, index):
        editor.setChecked(index.model().data(index, Qt.EditRole))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.isChecked(), Qt.EditRole)


# IntDelegate
class IntDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QSpinBox(parent)
        editor.setRange(-2147483648, 2147483647)
        return editor

    def setEditorData(self, editor, index):
        editor.setValue(int(index.model().data(index, Qt.EditRole)))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.value(), Qt.EditRole)


# FloatDelegate
class FloatDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QDoubleSpinBox(parent)
        editor.setRange(-1.79769e+308, 1.79769e+308)
        return editor

    def setEditorData(self, editor, index):
        editor.setValue(float(index.model().data(index, Qt.EditRole)))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.value(), Qt.EditRole)


# DateDelegate
class DateDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QDateEdit(parent)

    def setEditorData(self, editor, index):
        editor.setDate(index.model().data(index, Qt.EditRole))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.date(), Qt.EditRole)


# DateTimeDelegate
class DateTimeDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QDateTimeEdit(parent)

    def setEditorData(self, editor, index):
        editor.setDateTime(index.model().data(index, Qt.EditRole))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.dateTime(), Qt.EditRole)


# TimeDelegate
class TimeDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QTimeEdit(parent)

    def setEditorData(self, editor, index):
        editor.setTime(index.model().data(index, Qt.EditRole))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.time(), Qt.EditRole)


# FileDelegate
class FileDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QFileDialog(parent)

    def setEditorData(self, editor, index):
        editor.selectFile(index.model().data(index, Qt.EditRole))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.selectedFiles()[0], Qt.EditRole)


# FontDelegate
class FontDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QFontDialog(parent)

    def setEditorData(self, editor, index):
        editor.setCurrentFont(QFont(index.model().data(index, Qt.EditRole)))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentFont().toString(), Qt.EditRole)


# IconDelegate
class IconDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QFileDialog(parent)

    def setEditorData(self, editor, index):
        editor.selectFile(index.model().data(index, Qt.EditRole))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.selectedFiles()[0], Qt.EditRole)


# CursorDelegate
class CursorDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cursor_map = {
            "ArrowCursor": Qt.ArrowCursor,
            "WaitCursor": Qt.WaitCursor,
            "IBeamCursor": Qt.IBeamCursor,
            "CrossCursor": Qt.CrossCursor,
            "SizeVerCursor": Qt.SizeVerCursor,
            "SizeHorCursor": Qt.SizeHorCursor,
            "SizeBDiagCursor": Qt.SizeBDiagCursor,
            "SizeFDiagCursor": Qt.SizeFDiagCursor,
            "SizeAllCursor": Qt.SizeAllCursor,
            "BlankCursor": Qt.BlankCursor
        }

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.cursor_map.keys())
        return editor

    def setEditorData(self, editor, index):
        cursor_name = index.data()
        editor.setCurrentText(cursor_name)

    def setModelData(self, editor, model, index):
        cursor_name = editor.currentText()
        model.setData(index, cursor_name)


# UrlDelegate
class UrlDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QLineEdit(parent)

    def setEditorData(self, editor, index):
        editor.setText(index.model().data(index, Qt.EditRole))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), Qt.EditRole)


# KeySequenceDelegate
class KeySequenceDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QKeySequenceEdit(parent)

    def setEditorData(self, editor, index):
        editor.setKeySequence(QKeySequence(index.model().data(index, Qt.EditRole)))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.keySequence().toString(), Qt.EditRole)


# PaletteDelegate
class PaletteDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return QColorDialog(parent)

    def setEditorData(self, editor, index):
        editor.setCurrentColor(QColor(index.model().data(index, Qt.EditRole)))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentColor().name(), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


# ByteArrayDelegate
class ByteArrayDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if isinstance(value, QByteArray):
            editor.setText(value.toHex().data().decode())

    def setModelData(self, editor, model, index):
        hex_string = editor.text()
        model.setData(index, QByteArray.fromHex(hex_string.encode()), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


# PixmapDelegate
class PixmapDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QWidget(parent)
        layout = QHBoxLayout(editor)
        editor.button = QPushButton("Select Image", editor)
        editor.label = QLabel(editor)
        editor.label.setFixedSize(50, 50)
        editor.label.setAlignment(Qt.AlignCenter)
        editor.label.setScaledContents(True)

        layout.addWidget(editor.button)
        layout.addWidget(editor.label)
        layout.setContentsMargins(0, 0, 0, 0)
        editor.setLayout(layout)
        editor.button.clicked.connect(self.select_image)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if isinstance(value, dict) and 'pixmap' in value and 'path' in value:
            pixmap = QPixmap(value['path'])
            editor.label.setPixmap(pixmap.scaled(editor.label.size(), Qt.KeepAspectRatio))
            editor.selected_pixmap = pixmap
            editor.file_path = value['path']
            editor.button.setText("Change Image")

    def setModelData(self, editor, model, index):
        if hasattr(editor, 'selected_pixmap') and hasattr(editor, 'file_path'):
            model.setData(index, {'pixmap': editor.selected_pixmap, 'path': editor.file_path}, Qt.EditRole)


    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def select_image(self):
        editor = self.sender().parent()
        file_path, _ = QFileDialog.getOpenFileName(editor, "Select Image")
        if file_path:
            pixmap = QPixmap(file_path)
            editor.selected_pixmap = pixmap
            editor.file_path = file_path
            editor.label.setPixmap(pixmap.scaled(editor.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            editor.button.setText("Change Image")


# Vec2Delegate
class Vec2Delegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QWidget(parent)
        layout = QHBoxLayout(editor)
        layout.setContentsMargins(0, 0, 0, 0)
        editor.xEdit = QSpinBox()
        editor.yEdit = QSpinBox()
        layout.addWidget(editor.xEdit)
        layout.addWidget(editor.yEdit)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        x, y = map(int, value.split(","))
        editor.xEdit.setValue(x)
        editor.yEdit.setValue(y)

    def setModelData(self, editor, model, index):
        value = f"{editor.xEdit.value()},{editor.yEdit.value()}"
        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


# Vec2fDelegate
class Vec2fDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QWidget(parent)
        layout = QHBoxLayout(editor)
        layout.setContentsMargins(0, 0, 0, 0)
        editor.xEdit = QDoubleSpinBox()
        editor.yEdit = QDoubleSpinBox()
        layout.addWidget(editor.xEdit)
        layout.addWidget(editor.yEdit)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        x, y = map(float, value.split(","))
        editor.xEdit.setValue(x)
        editor.yEdit.setValue(y)

    def setModelData(self, editor, model, index):
        value = f"{editor.xEdit.value()},{editor.yEdit.value()}"
        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


# Vec3Delegate
class Vec3Delegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QWidget(parent)
        layout = QHBoxLayout(editor)
        layout.setContentsMargins(0, 0, 0, 0)
        editor.xEdit = QDoubleSpinBox()
        editor.yEdit = QDoubleSpinBox()
        editor.zEdit = QDoubleSpinBox()
        layout.addWidget(editor.xEdit)
        layout.addWidget(editor.yEdit)
        layout.addWidget(editor.zEdit)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        x, y, z = map(int, value.split(","))
        editor.xEdit.setValue(x)
        editor.yEdit.setValue(y)
        editor.zEdit.setValue(z)

    def setModelData(self, editor, model, index):
        value = f"{editor.xEdit.value()},{editor.yEdit.value()},{editor.zEdit.value()}"
        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


# Vec3fDelegate
class Vec3fDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QWidget(parent)
        layout = QHBoxLayout(editor)
        layout.setContentsMargins(0, 0, 0, 0)
        editor.xEdit = QDoubleSpinBox()
        editor.yEdit = QDoubleSpinBox()
        editor.zEdit = QDoubleSpinBox()
        layout.addWidget(editor.xEdit)
        layout.addWidget(editor.yEdit)
        layout.addWidget(editor.zEdit)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        x, y, z = map(float, value.split(","))
        editor.xEdit.setValue(x)
        editor.yEdit.setValue(y)
        editor.zEdit.setValue(z)

    def setModelData(self, editor, model, index):
        value = f"{editor.xEdit.value()},{editor.yEdit.value()},{editor.zEdit.value()}"
        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


# Vec4Delegate
class Vec4Delegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QWidget(parent)
        layout = QHBoxLayout(editor)
        layout.setContentsMargins(0, 0, 0, 0)
        editor.xEdit = QDoubleSpinBox()
        editor.yEdit = QDoubleSpinBox()
        editor.zEdit = QDoubleSpinBox()
        editor.wEdit = QDoubleSpinBox()
        layout.addWidget(editor.xEdit)
        layout.addWidget(editor.yEdit)
        layout.addWidget(editor.zEdit)
        layout.addWidget(editor.wEdit)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        x, y, z, w = map(int, value.split(","))
        editor.xEdit.setValue(x)
        editor.yEdit.setValue(y)
        editor.zEdit.setValue(z)
        editor.wEdit.setValue(w)

    def setModelData(self, editor, model, index):
        value = f"{editor.xEdit.value()},{editor.yEdit.value()},{editor.zEdit.value()},{editor.wEdit.value()}"
        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


# Vec4fDelegate
class Vec4fDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QWidget(parent)
        layout = QHBoxLayout(editor)
        layout.setContentsMargins(0, 0, 0, 0)
        editor.xEdit = QDoubleSpinBox()
        editor.yEdit = QDoubleSpinBox()
        editor.zEdit = QDoubleSpinBox()
        editor.wEdit = QDoubleSpinBox()
        layout.addWidget(editor.xEdit)
        layout.addWidget(editor.yEdit)
        layout.addWidget(editor.zEdit)
        layout.addWidget(editor.wEdit)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        x, y, z, w = map(float, value.split(","))
        editor.xEdit.setValue(x)
        editor.yEdit.setValue(y)
        editor.zEdit.setValue(z)
        editor.wEdit.setValue(w)

    def setModelData(self, editor, model, index):
        value = f"{editor.xEdit.value()},{editor.yEdit.value()},{editor.zEdit.value()},{editor.wEdit.value()}"
        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


# PropertyModel
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
                if isinstance(property_item.value, dict) and 'path' in property_item.value:
                    return property_item.value['path']
                return property_item.value
        elif role == Qt.DecorationRole and index.column() == 1:
            if isinstance(property_item.value, dict) and 'pixmap' in property_item.value:
                return property_item.value['pixmap'].scaled(50, 50, Qt.KeepAspectRatio)

        elif role == Qt.BackgroundRole:
            if index.column() == 1 and property_item.type == 'color':
                return QColor(property_item.value)
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
                    self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole, Qt.DecorationRole,Qt.BackgroundRole])
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
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1),
                              [Qt.BackgroundRole])

    def setOddRowColor(self, color):
        self.odd_row_color = QColor(color)
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1),
                              [Qt.BackgroundRole])


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
    delegateChanged = Signal(int, str)

    def __init__(self, properties=None, parent=None):
        super().__init__(parent)
        self.delegates = {
            "string": StringDelegate(),
            "color": ColorDelegate(),
            "bool": BoolDelegate(),
            "int": IntDelegate(),
            "float": FloatDelegate(),
            "date": DateDelegate(),
            "datetime": DateTimeDelegate(),
            "time": TimeDelegate(),
            "file": FileDelegate(),
            "font": FontDelegate(),
            "icon": IconDelegate(),
            "cursor": CursorDelegate(),
            "url": UrlDelegate(),
            "keysequence": KeySequenceDelegate(),
            "palette": PaletteDelegate(),
            "ByteArray": ByteArrayDelegate(),
            "Pixmap": PixmapDelegate(),
            "Stringlist": StringListDelegate(),
            "vec2": Vec2Delegate(),
            "vec2f": Vec2fDelegate(),
            "vec3": Vec3Delegate(),
            "vec3f": Vec3fDelegate(),
            "vec4": Vec4Delegate(),
            "vec4f": Vec4fDelegate()
        }

        self._model = PropertyModel(properties)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self._model)
        self.setModel(self.proxy_model)

        # Connect dataChanged signal
        self._model.dataChanged.connect(self.on_data_changed)

    def on_data_changed(self, top_left, bottom_right, roles):
        for row in range(top_left.row(), bottom_right.row() + 1):
            index = self._model.index(row, 1)
            property_name = self._model.data(self._model.index(row, 0))
            if property_name == "Cursor":
                cursor_name = self._model.data(index)
                self.delegateChanged.emit(row, cursor_name)
            # Refresh the affected rows
            self.viewport().update()

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
                PropertyItem("Color", "#000000", "color"),
                PropertyItem("Name3", "Process 3", "string"),
                PropertyItem("Bool", True, "bool"),
                PropertyItem("Int", 5, "int"),
                PropertyItem("Float", 10.5, "float"),
                PropertyItem("Date", QDate.currentDate(), "date"),
                PropertyItem("DateTime", QDateTime.currentDateTime(), "datetime"),
                PropertyItem("Time", QTime.currentTime(), "time"),
                PropertyItem("File", "/path/to/file.txt", "file"),
                PropertyItem("Font", "Arial,12,-1,5,50,0,0,0,0,0", "font"),
                PropertyItem("IconPath", "icon.png", "icon"),
                PropertyItem("Cursor", "ArrowCursor", "cursor"),
                PropertyItem("Url", "https://www.example.com", "url"),
                PropertyItem("KeySequence", "Ctrl+C", "keysequence"),
                PropertyItem("Palette", "#000000", "palette"),
                PropertyItem("StringList", "Type Yr list", "Stringlist"),
                PropertyItem("ByteArray", QByteArray(b'Example'), "ByteArray"),
                PropertyItem("Pixmap", "Select", "Pixmap"),
                PropertyItem("Vec2D", "1 , 2", "vec2"),
                PropertyItem("Vec2Df", "1.0,2.0", "vec2f"),
                PropertyItem("Vec3D", "1 ,2 ,3", "vec3"),
                PropertyItem("Vec3Df", "1.0,2.0,3.0", "vec3f"),
                PropertyItem("Vec4D", "1 ,2 ,3 ,4", "vec4"),
                PropertyItem("Vec4Df", "1.0,2.0,3.0,4.0", "vec4f"),
            ]
        )
        self.model = self.editor_widget.get_model()
        self.editor_widget.delegateChanged.connect(self.applyCursorChange)
        self.model.afterDataChanged.connect(self.afterDataChanged)

        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createUndoView()

        self.setWindowTitle("Undo Framework")
        self.setMinimumSize(874, 515)
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

    def applyCursorChange(self, row, cursor_name):
        cursor_shape = CursorDelegate().cursor_map.get(cursor_name, Qt.ArrowCursor)
        self.setCursor(QCursor(cursor_shape))

    def createUndoView(self):
        undoDockWidget = QDockWidget("Command List", self)
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
            old_color = self.model.even_row_color
            command = SetRowColorCommand(self.model, 'even', old_color, color)
            self.undoStack.push(command)

    def setOddRowColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            old_color = self.model.odd_row_color
            command = SetRowColorCommand(self.model, 'odd', old_color, color)
            self.undoStack.push(command)

    def setBackgroundColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            old_color = self.palette().window().color()
            command = SetBackgroundColorCommand(self, old_color, color)
            self.undoStack.push(command)

    def applyBackgroundColor(self, color):
        palette = self.palette()
        palette.setColor(self.backgroundRole(), color)
        self.setPalette(palette)

    def about(self):
        QMessageBox.about(self, "About Undo Framework", "This demonstrates the use of the QUndoStack class.")
=

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
