# Python
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# 3rd Party
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6 import QtCore, QtGui

# Discussion of no signals / slots for drop events

# https://forum.qt.io/topic/564/signals-and-slots-for-drag-and-drop-behavior
# https://www.qtcentre.org/threads/24984-Connecting-slot-for-drop-event-in-QGraphicsView

# Guiding example: https://stackoverflow.com/questions/25603134/pyside-drag-and-drop-files-into-qlistwidget

@dataclass
class CheckedPath():
    path: Path
    isChecked: bool = False

class QListWidgetDragAndDrop(QListWidget):
    """ A customized QListWidget which provides drag-and-drop support, and empty placeholder text.

    If the QListWidget is empty, the self._placeholder_text will be displayed in the center of the widget.
    """

    signal_file_dropped = QtCore.Signal(list)

    def __init__(self, parent=None, accepted_audio_filename_extensions:Optional[List[str]] = None):
        super(QListWidgetDragAndDrop, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setIconSize(QtCore.QSize(72, 72))

        self._placeholder_text = ""

        self.accepted_audio_filename_extensions = accepted_audio_filename_extensions


    def _accepted_audio_extension(self, filename: str):
        if self.accepted_audio_filename_extensions is None:
            return False

        for extension in self.accepted_audio_filename_extensions:
            if filename.endswith(extension):
                return True
        
        return False



    def add_paths(self, checked_paths: List[CheckedPath]):
        """ Adds every Path in the given list to the QListWidget, as a QListWidgetItem. """
        for one_path in checked_paths:

            item = QListWidgetItem(str(one_path.path))
    
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable )

            if one_path.isChecked:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)

            self.addItem(item)


    def add_paths_checked(self, paths: List[Path]):
        """ Adds every Path in the given list to the QListWidget, as a QListWidgetItem. """
        for one_path in paths:

            item = QListWidgetItem(str(one_path))
    
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable )
            item.setCheckState(QtCore.Qt.Checked)

            self.addItem(item)


    def remove_selected_items(self):
        selected_items = self.selectedItems()

        for item in selected_items:
            self.takeItem(self.row(item))
    

    def get_checked_paths(self):
        """ Returns all items. """
        all_items = []

        model = self.model()
        for index in range(model.rowCount()):

            tt = model.index(index)
            item = model.itemData(tt)

            # At the time of writing, it's not exactly clear how to "properly" index into the derived QListWidget's
            # Model. These hard-coded index numbers (0 and 10) are suboptimal.
            item_name = item[0]
            item_checked = (item[10] == QtCore.Qt.Checked.value)

            # Skip any items that aren't checked.
            if not item_checked:
                continue

            all_items.append(Path(item_name))

        return all_items
    

    def get_paths(self) -> List[CheckedPath]:
        """ Returns all items. """
        all_items = []

        model = self.model()
        for index in range(model.rowCount()):

            tt = model.index(index)
            item = model.itemData(tt)

            # At the time of writing, it's not exactly clear how to "properly" index into the derived QListWidget's
            # Model. These hard-coded index numbers (0 and 10) are suboptimal.
            item_name = item[0]
            item_checked = (item[10] == QtCore.Qt.Checked.value)

            all_items.append(CheckedPath(Path(item_name), item_checked))

        return all_items


    # Dragging and dropping files on to a QListWidget were inspired by this example:
    # https://stackoverflow.com/questions/25603134/pyside-drag-and-drop-files-into-qlistwidget

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """ Triggers when files are dropped on to the widget. """
        mime_data = event.mimeData()

        if mime_data.hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            links = []
            accepted_paths = []
            for url in mime_data.urls():
                links.append(str(url.toLocalFile()))
                path = Path(url.toLocalFile())

                if path.is_dir():
                    accepted_paths.append(path)

                if self._accepted_audio_extension(path.name):
                    accepted_paths.append(path)

            self.signal_file_dropped.emit(links)
            self.add_paths_checked(accepted_paths)
        else:
            event.ignore()

    
    # Code to paint a placeholder text in the center of the QListWidget when empty, was inspired by this example:
    # https://stackoverflow.com/questions/60076333/how-to-set-the-placeholder-text-in-the-center-when-the-qlistwidget-is-empty

    @property
    def placeholder_text(self):
        return self._placeholder_text

    @placeholder_text.setter
    def placeholder_text(self, text):
        self._placeholder_text = text
        #self.update() # update() takes no parameters...?

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0:
            painter = QtGui.QPainter(self.viewport())
            painter.save()
            col = self.palette().placeholderText().color()
            painter.setPen(col)
            fm = self.fontMetrics()
            elided_text = fm.elidedText(
                self.placeholder_text, QtCore.Qt.ElideRight, self.viewport().width()
            )
            painter.drawText(self.viewport().rect(), QtCore.Qt.AlignCenter, elided_text)
            painter.restore()
