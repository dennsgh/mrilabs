from PyQt6.QtWidgets import QListWidget, QSizePolicy
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtGui import QFontMetrics


class Sidebar(QListWidget):

    pageSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.itemClicked.connect(self._on_item_clicked)

    def _on_item_clicked(self, item):
        self.pageSelected.emit(item.text())

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        max_width = max(
            fm.horizontalAdvance(self.item(index).text()) for index in range(self.count()))

        # Add some padding to the width
        width = max_width + 20  # Adjust padding as needed
        # Set the minimum width to be considered
        minimum_width = 200
        width = max(width, minimum_width)
        return QSize(width, self.sizeHintForRow(0) * self.count())

    def addItems(self, items):
        super().addItems(items)
        self.updateGeometry()  # Ensure the sidebar resizes to fit the new items

    def updateGeometry(self):
        # Recalculate the maximum width each time items are added or the widget is updated
        super().updateGeometry()
        self.setMaximumWidth(self.sizeHint().width())