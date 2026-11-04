"""Accessible language buttons with flags painted at the display's native DPI."""
from PySide6.QtCore import Qt, Signal, QRectF, QLineF
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen
from PySide6.QtWidgets import QWidget, QHBoxLayout, QButtonGroup

from ui_controls import KeyboardButton
from i18n import LANGUAGES


class FlagButton(KeyboardButton):
    def __init__(self, code, name):
        super().__init__(name)
        self.code = code
        self.setCheckable(True)
        self.setObjectName("languageChoice")
        self.setAccessibleName(name)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(66)
        self.setStyleSheet("""
            QPushButton#languageChoice { text-align:left; padding:12px 16px 12px 76px;
                border-radius:12px; background:#f7f9fc; border:1px solid #dfe5ec; }
            QPushButton#languageChoice:hover { background:#edf3f7; border-color:#9aaabd; }
            QPushButton#languageChoice:checked { background:#e7f3ed; border:2px solid #287e68; }
            QPushButton#languageChoice:focus { border-color:#287e68; }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(18, (self.height() - 28) / 2, 42, 28)
        clip = QPainterPath()
        clip.addRoundedRect(rect, 3, 3)
        painter.save()
        painter.setClipPath(clip)
        if self.code == "fr":
            for index, color in enumerate(("#0055a4", "#ffffff", "#ef4135")):
                painter.fillRect(QRectF(rect.x() + index*14, rect.y(), 14, rect.height()), QColor(color))
        else:
            painter.fillRect(rect, QColor("#012169"))
            for color, width in (("#ffffff", 7), ("#c8102e", 3)):
                painter.setPen(QPen(QColor(color), width))
                painter.drawLine(rect.topLeft(), rect.bottomRight())
                painter.drawLine(rect.bottomLeft(), rect.topRight())
            for color, width in (("#ffffff", 10), ("#c8102e", 6)):
                painter.setPen(QPen(QColor(color), width))
                painter.drawLine(QLineF(rect.center().x(), rect.top(), rect.center().x(), rect.bottom()))
                painter.drawLine(QLineF(rect.left(), rect.center().y(), rect.right(), rect.center().y()))
        painter.restore()
        painter.setPen(QPen(QColor("#cbd4df"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 3, 3)


class LanguagePicker(QWidget):
    currentIndexChanged = Signal(int)

    def __init__(self):
        super().__init__()
        self.codes = tuple(LANGUAGES)
        self._index = -1
        self.buttons = {}
        self.group = QButtonGroup(self)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        for index, (code, name) in enumerate(LANGUAGES.items()):
            button = FlagButton(code, name)
            self.buttons[code] = button
            self.group.addButton(button, index)
            layout.addWidget(button, 1)
        self.group.idClicked.connect(self.setCurrentIndex)
        self.setCurrentIndex(0)

    def findData(self, code):
        return self.codes.index(code) if code in self.codes else -1

    def currentData(self):
        return self.codes[self._index]

    def currentIndex(self):
        return self._index

    def setCurrentIndex(self, index):
        if not 0 <= index < len(self.codes) or index == self._index:
            return
        self._index = index
        self.group.button(index).setChecked(True)
        self.currentIndexChanged.emit(index)
