"""Shared controls with keyboard-only focus cues and an accessible switch."""

from PySide6.QtCore import Qt, QSize, QRectF, QVariantAnimation, QEasingCurve
from i18n import apply_widgets
from ui_theme import color
from PySide6.QtGui import QColor, QPainter, QCursor, QPen
from PySide6.QtWidgets import (
    QPushButton, QCheckBox, QStyleOptionButton, QStylePainter, QStyle,
    QStyledItemDelegate, QStyleOptionViewItem, QListWidget, QAbstractItemView,
    QMessageBox, QFrame, QLabel, QVBoxLayout, QApplication,QHBoxLayout,QWidget,QSpinBox,QDoubleSpinBox,QAbstractSpinBox,QLineEdit,
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
        if self.hasFocus() and self.window().testAttribute(Qt.WidgetAttribute.WA_KeyboardFocusChange):
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(color("focus")),2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self.rect().adjusted(2,2,-3,-3),6,6)


class NumericEditMixin:
    def repair_editor(self):
        self.lineEdit().setGeometry(self.rect().adjusted(10,4,-10,-4))

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.repair_editor()

    def showEvent(self,event):
        super().showEvent(event)
        self.repair_editor()

    def focusInEvent(self,event):
        super().focusInEvent(event)
        self.repair_editor()
        if event.reason()==Qt.FocusReason.MouseFocusReason:
            self.lineEdit().deselect()

    def focusOutEvent(self,event):
        super().focusOutEvent(event)
        self.lineEdit().deselect()

    def stepBy(self,steps):
        super().stepBy(steps)
        self.lineEdit().deselect()


class NumericSpin(NumericEditMixin,QSpinBox): pass
class NumericDoubleSpin(NumericEditMixin,QDoubleSpinBox): pass


def number_stepper(field,title):
    field.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    field.setAlignment(Qt.AlignmentFlag.AlignCenter)
    field.setFixedWidth(120)
    field.lineEdit().setStyleSheet('background:transparent;border:0;padding:0;min-height:0;')
    controls=QWidget()
    line=QHBoxLayout(controls)
    line.setContentsMargins(0,0,0,0)
    line.setSpacing(6)
    down=KeyboardButton('−')
    up=KeyboardButton('+')
    down.clicked.connect(field.stepDown)
    up.clicked.connect(field.stepUp)
    for button,verb in ((down,'Decrease'),(up,'Increase')):
        button.setFixedSize(38,38)
        button.setStyleSheet('padding:0;font-size:18px')
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setAccessibleName(verb+' · '+title)
    line.addWidget(down)
    line.addWidget(field)
    line.addWidget(up)
    line.addStretch()
    return controls,down,up


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
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)


class CatalogList(SelectionList):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIconSize(QSize(30, 30))
        self.setObjectName("catalog")


class CatalogSearch(QWidget):
    """Filter a catalogue without letting a hidden selection remain actionable."""
    def __init__(self, catalogue, placeholder):
        super().__init__()
        self.catalogue = catalogue
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.field = QLineEdit()
        self.field.setPlaceholderText(placeholder)
        self.field.setAccessibleName(placeholder)
        self.field.setClearButtonEnabled(True)
        layout.addWidget(self.field)
        self.empty = QLabel("No matching results")
        self.empty.setObjectName("muted")
        self.empty.hide()
        layout.addWidget(self.empty)
        self.field.textChanged.connect(self.apply_filter)

    def apply_filter(self, *_):
        import unicodedata
        def normalized(value):
            return "".join(c for c in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(c))
        terms = normalized(self.field.text()).split()
        visible = 0
        for row in range(self.catalogue.count()):
            item = self.catalogue.item(row)
            matches = all(term in normalized(item.text()) for term in terms)
            item.setHidden(not matches)
            visible += matches
        current = self.catalogue.currentItem()
        if current is not None and current.isHidden():
            self.catalogue.setCurrentRow(-1)
        self.empty.setVisible(bool(terms) and visible == 0)


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
            track_color = color("focus") if self.isChecked() else color("strong_border")
            text_color = color("text")
        else:
            track_color = color("selection") if self.isChecked() else color("disabled_surface")
            text_color = color("disabled")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(track_color))
        painter.drawRoundedRect(track, 12, 12)
        painter.setBrush(QColor("#ffffff" if self.isEnabled() else "#f5f7f9"))
        painter.drawEllipse(QRectF(track.left() + 2 + self.offset * 20, top + 2, 20, 20))
        if self.hasFocus() and self.window().testAttribute(Qt.WidgetAttribute.WA_KeyboardFocusChange):
            painter.setPen(QPen(QColor(color("focus")), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(track.adjusted(-2, -2, 2, 2), 14, 14)
        painter.setPen(QColor(text_color))
        painter.setFont(self.font())
        painter.drawText(QRectF(59, 0, self.width() - 59, self.height()),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         self.text())
