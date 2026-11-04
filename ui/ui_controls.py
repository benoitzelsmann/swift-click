"""Shared controls with keyboard-only focus cues and an accessible switch."""

from PySide6.QtCore import Qt, QSize, QRectF, QVariantAnimation, QEasingCurve
from i18n import apply_widgets
from PySide6.QtGui import QColor, QPainter, QCursor
from PySide6.QtWidgets import (
    QPushButton, QCheckBox, QStyleOptionButton, QStylePainter, QStyle,
    QStyledItemDelegate, QStyleOptionViewItem, QListWidget, QAbstractItemView,
    QMessageBox, QFrame, QLabel, QVBoxLayout, QApplication,
)


class KeyboardButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAutoDefault(False)

    def paintEvent(self, event):
        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.state &= ~QStyle.StateFlag.State_HasFocus
        painter = QStylePainter(self)
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)


class SelectionDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        clean = QStyleOptionViewItem(option)
        clean.state &= ~QStyle.StateFlag.State_HasFocus
        super().paint(painter, clean, index)


class SelectionList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemDelegate(SelectionDelegate(self))
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)


def message_box(parent, title, text, *, question=False, warning=False, accept="Confirm"):
    box = QMessageBox(parent)
    box.setOption(QMessageBox.Option.DontUseNativeDialog, True)
    box.setWindowTitle("Swift Click")
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.setText(title)
    box.setInformativeText(text.replace("\u2014", ",").replace("\u2013", "-"))
    box.setIcon(QMessageBox.Icon.NoIcon if question else
                QMessageBox.Icon.Warning if warning else QMessageBox.Icon.Information)
    box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                           if question else QMessageBox.StandardButton.Ok)
    box.setDefaultButton(QMessageBox.StandardButton.No if question else QMessageBox.StandardButton.Ok)
    box.setStyleSheet("""
        QMessageBox { background:#ffffff; color:#18202b; }
        QMessageBox QLabel { background:transparent; color:#18202b; font-size:13px; }
        QMessageBox QLabel#qt_msgbox_label { font-size:17px; font-weight:600; }
        QMessageBox QLabel#qt_msgbox_informativelabel { color:#495462; min-width:390px; }
        QMessageBox QPushButton { background:#ffffff; color:#18202b; min-width:80px;
            border:1px solid #dfe3e9; border-radius:6px; padding:8px 14px; }
        QMessageBox QPushButton:default { background:#202632; color:#ffffff; border-color:#202632; }
    """)
    if question:
        box.button(QMessageBox.StandardButton.Yes).setText(accept)
        box.button(QMessageBox.StandardButton.No).setText("Cancel")
    apply_widgets(box)
    return box


def confirm_dialog(parent, title, text, *, accept="Confirm"):
    result = message_box(parent, title, text, question=True, accept=accept).exec()
    return result == QMessageBox.StandardButton.Yes


def show_message(parent, title, text, *, warning=False):
    message_box(parent, title, text, warning=warning).exec()


class CountdownOverlay(QFrame):
    def __init__(self, title):
        super().__init__(None, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setObjectName("countdown")
        self.setStyleSheet("QFrame#countdown { background:#202632; border-radius:10px; }"
                           "QLabel { color:white; background:transparent; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24,16,24,16)
        self.caption = QLabel(title)
        layout.addWidget(self.caption)
        self.number = QLabel("3")
        self.number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.number.setStyleSheet("font-size:32px;font-weight:600;color:white")
        layout.addWidget(self.number)
        self.resize(230,112)
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen:
            bounds = screen.availableGeometry()
            self.move(bounds.right() - self.width() - 24, bounds.top() + 24)

    def set_remaining(self, remaining):
        self.number.setText(str(remaining))
        self.setAccessibleName(f"{self.caption.text()}: {remaining}")
        apply_widgets(self)


class ToggleSwitch(QCheckBox):
    """Keep QCheckBox semantics, checked state and signals for assistive tools."""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(text)
        self.offset = float(self.isChecked())
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(140)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.valueChanged.connect(self.move_thumb)
        self.toggled.connect(self.animate)

    def sizeHint(self):
        return QSize(self.fontMetrics().horizontalAdvance(self.text()) + 64, 34)

    def minimumSizeHint(self):
        return self.sizeHint()

    def hitButton(self, point):
        return self.rect().contains(point)

    def move_thumb(self, value):
        self.offset = float(value)
        self.update()

    def animate(self, checked):
        self.animation.stop()
        target = float(checked)
        if not self.isVisible():
            self.move_thumb(target)
            return
        self.animation.setStartValue(self.offset)
        self.animation.setEndValue(target)
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        top = (self.height() - 24) / 2
        track = QRectF(3, top, 44, 24)
        if self.isEnabled():
            track_color = "#287e68" if self.isChecked() else "#d5dce3"
            text_color = "#18202b"
        else:
            track_color = "#a0b9b0" if self.isChecked() else "#e3e7ec"
            text_color = "#929ba7"
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(track_color))
        painter.drawRoundedRect(track, 12, 12)
        painter.setBrush(QColor("#ffffff" if self.isEnabled() else "#f5f7f9"))
        painter.drawEllipse(QRectF(track.left() + 2 + self.offset * 20, top + 2, 20, 20))
        painter.setPen(QColor(text_color))
        painter.setFont(self.font())
        painter.drawText(QRectF(59, 0, self.width() - 59, self.height()),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         self.text())
