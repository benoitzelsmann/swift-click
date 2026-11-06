"""Shared controls with keyboard-only focus cues and an accessible switch."""

from PySide6.QtCore import Qt, QSize, QRect, QPoint, QRectF, QVariantAnimation, QEasingCurve, Signal
from i18n import apply_widgets
from ui_theme import color
from PySide6.QtGui import QColor, QPainter, QCursor, QPen
from PySide6.QtWidgets import (
    QPushButton, QCheckBox, QStyleOptionButton, QStylePainter, QStyle,
    QStyledItemDelegate, QStyleOptionViewItem, QListWidget, QAbstractItemView,
    QMessageBox, QFrame, QLabel, QVBoxLayout, QApplication,QHBoxLayout,QWidget,QSpinBox,QDoubleSpinBox,QAbstractSpinBox,QLineEdit,
    QLayout, QSizePolicy,
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


class GestureCheck(QCheckBox):
    """A compact, painted check box that follows the theme and keeps QCheckBox semantics."""

    def __init__(self, accessible_name, parent=None):
        super().__init__("", parent)
        self.setAccessibleName(accessible_name)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedSize(22, 22)

    def sizeHint(self):
        return QSize(22, 22)

    def hitButton(self, point):
        return self.rect().contains(point)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        box = QRectF(2.5, 2.5, 17, 17)
        if self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(color("accent")))
            painter.drawRoundedRect(box, 5, 5)
            pen = QPen(QColor(color("on_accent")), 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawPolyline([QPoint(7, 11), QPoint(10, 14), QPoint(15, 8)])
        else:
            painter.setPen(QPen(QColor(color("strong_border")), 1.5))
            painter.setBrush(QColor(color("surface")))
            painter.drawRoundedRect(box, 5, 5)
        if self.hasFocus() and self.window().testAttribute(Qt.WidgetAttribute.WA_KeyboardFocusChange):
            painter.setPen(QPen(QColor(color("focus")), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(0.5, 0.5, 21, 21), 7, 7)


class FlowLayout(QLayout):
    """Wrap items onto new lines, like words in a paragraph."""

    def __init__(self, parent=None, spacing=8):
        super().__init__(parent)
        self.items = []
        self.gap = spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self.items.append(item)

    def count(self):
        return len(self.items)

    def itemAt(self, index):
        return self.items[index] if 0 <= index < len(self.items) else None

    def takeAt(self, index):
        return self.items.pop(index) if 0 <= index < len(self.items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.arrange(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.arrange(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.items:
            size = size.expandedTo(item.minimumSize())
        return size

    def arrange(self, rect, measure):
        x, y, line = rect.x(), rect.y(), 0
        for item in self.items:
            if item.widget() is not None and item.widget().isHidden():
                continue
            hint = item.sizeHint()
            if x + hint.width() > rect.right() + 1 and line:
                x, y, line = rect.x(), y + line + self.gap, 0
            if not measure:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + self.gap
            line = max(line, hint.height())
        return y + line - rect.y()


class ChoiceGroup(QWidget):
    """Visible, one-tap choices with the QComboBox calls the views already use."""
    currentIndexChanged = Signal(int)

    def __init__(self, parent=None, translate=False):
        super().__init__(parent)
        self.translate = translate
        self.flow = FlowLayout(self)
        self.buttons = []
        self.values = []
        self.index = -1
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    def addItem(self, text, data=None):
        button = KeyboardButton(text)
        button.setObjectName("chip")
        button.setCheckable(True)
        button.setProperty("i18nUserText", not self.translate)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if self.translate:
            apply_widgets(button)
        position = len(self.buttons)
        button.clicked.connect(lambda _=False, i=position: self.choose(i))
        self.buttons.append(button)
        self.values.append(data)
        self.flow.addWidget(button)
        if self.index < 0:
            self.setCurrentIndex(0)
        self.updateGeometry()

    def clear(self):
        for button in self.buttons:
            self.flow.removeWidget(button)
            button.deleteLater()
        self.buttons, self.values = [], []
        if self.index != -1:
            self.index = -1
            self.currentIndexChanged.emit(-1)

    def choose(self, index):
        self.setCurrentIndex(index)
        self.buttons[index].setChecked(True)

    def count(self):
        return len(self.buttons)

    def currentIndex(self):
        return self.index

    def setCurrentIndex(self, index):
        index = index if 0 <= index < len(self.buttons) else -1
        for position, button in enumerate(self.buttons):
            button.setChecked(position == index)
        if index != self.index:
            self.index = index
            self.currentIndexChanged.emit(index)

    def currentData(self):
        return self.values[self.index] if self.index >= 0 else None

    def currentText(self):
        return self.buttons[self.index].text() if self.index >= 0 else ""

    def itemData(self, index):
        return self.values[index]

    def itemText(self, index):
        return self.buttons[index].text()

    def setItemText(self, index, text):
        self.buttons[index].setText(text)

    def findData(self, data):
        return self.values.index(data) if data in self.values else -1

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.flow.heightForWidth(width)

    def sizeHint(self):
        width = sum(b.sizeHint().width() + 8 for b in self.buttons)
        return QSize(min(width, 560), self.flow.heightForWidth(min(width, 560)) if self.buttons else 0)

    def minimumSizeHint(self):
        return QSize(0, 0)
