"""Illustrated connection guides. Screenshots keep their original pixels on disk."""

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QSize, QSettings
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
    QSizePolicy, QDialog, QDialogButtonBox, QApplication,
)

from app_paths import config_dir
from i18n import apply_widgets
from ui_controls import KeyboardButton

ASSETS = Path(__file__).with_name("assets")


def text_label(text, name=None):
    widget = QLabel(text)
    widget.setWordWrap(True)
    if name:
        widget.setObjectName(name)
    return widget


@dataclass(frozen=True)
class Step:
    title: str
    body: str
    image: str
    caption: str
    compact: bool = False
    trim_gap: bool = False


MYWHOOSH_STEPS = (
    Step("Set up MyWhoosh",
         "Open <b>Connectivity</b> in MyWhoosh settings. Enable <b>Direct Connect</b> "
         "for the network connection and <b>Virtual Shifting</b> for gear changes. "
         "<b>Auto Connect</b> is optional and can simplify later sessions.",
         "help/mywhoosh-settings.png", "Compact view · labels and switches are shown closer together.", True),
    Step("Check that LAN is blue",
         "Return to the MyWhoosh pairing screen and check that <b>LAN is blue</b>. "
         "Click <b>Connect</b> above to start the Swift Click connection. "
         "If using two devices, connect both to the same local network.",
         "help/mywhoosh-lan.png", "Blue LAN means networking is enabled. The handlebar icon may still be white."),
    Step("Install the connection service",
         "Click the <b>handlebar icon on the far right</b>, which represents OpenBikeControl. "
         "If <b>Dircon Service Unavailable</b> appears, choose <b>YES</b> and complete the installation. "
         "Then <b>close and restart MyWhoosh</b> before connecting again. "
         "Allow Bonjour installation if requested for network discovery. "
         "If there is no prompt, continue to the next step.",
         "help/mywhoosh-service.png", "Choose YES, finish installation, then restart MyWhoosh."),
    Step("Accept the connection",
         "When <b>OpenBikeControl Instance Found</b> appears in MyWhoosh, "
         "click <b>YES</b> to allow the Swift Click connection.",
         "help/mywhoosh-confirm.png", "Compact view · choose YES in MyWhoosh to accept.", trim_gap=True),
    Step("Check the connection and test shifting",
         "The <b>handlebar turns blue</b> in MyWhoosh and Swift Click shows <b>Connected</b>. "
         "In <b>Settings → Buttons</b>, assign Gear up and Gear down to two gestures. "
         "Start a ride and check that the displayed gear changes.",
         "help/mywhoosh-connected.png", "Blue LAN and a blue handlebar mean MyWhoosh accepted the network connection."),
)

CONTROLLER_STEPS = (
    Step("Wake the right controller",
         "Enable Bluetooth on your PC and press a button on the <b>right Zwift Click V2</b>. "
         "Only the right controller with A/B/Y/Z/+ is supported. Close Zwift and any "
         "other app that may already be connected to it.",
         "click-right.png", "Pressing a button wakes the right Click V2. The left controller is not supported."),
    Step("Connect and check button input",
         "Click <b>Connect</b> above and wait for <b>Connected</b>. Press a button: "
         "the Button input indicator confirms reception even if no action is assigned yet.",
         "click-right.png", "The battery level appears when the controller reports it."),
    Step("Assign actions",
         "Open <b>Settings → Buttons</b> to enable Simple, Double, Long or Continuous hold and assign actions. "
         "To control MyWhoosh, connect it under <b>Connections → MyWhoosh</b> as well. "
         "Save click targets under <b>Actions → Mouse positions</b>. Create sequences under <b>Actions → Routines</b>.",
         "click-right.png", "Connection settings and button assignments have separate pages."),
)


class GuideImage(QWidget):
    """Fit a source screenshot; optionally omit only its empty middle strip."""

    def __init__(self, parent=None, *, expandable=True):
        super().__init__(parent)
        self.source = QPixmap()
        self.compact = False
        self.trim_gap = False
        self.expandable = expandable
        self.setMinimumHeight(96)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        if expandable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setToolTip("Click to enlarge image")

    def set_step(self, step):
        self.source = QPixmap(str(ASSETS / step.image))
        self.compact = step.compact
        self.trim_gap = step.trim_gap
        self.setAccessibleName(step.caption + (" · Enlarge" if self.expandable else ""))
        self.update()

    def source_regions(self):
        if self.trim_gap and self.source.height() >= 500:
            return [QRectF(0, 0, self.source.width(), 220),
                    QRectF(0, 460, self.source.width(), self.source.height() - 460)]
        if self.compact and self.source.width() >= 1800:
            # Keep all three labels on the left and all switches on the right.
            return [QRectF(0, 0, 650, self.source.height()),
                    QRectF(1530, 0, self.source.width() - 1530, self.source.height())]
        return [QRectF(self.source.rect())]

    def sizeHint(self):
        return QSize(600, 130)

    def paintEvent(self, event):
        if self.source.isNull():
            return
        regions = self.source_regions()
        width = max(r.width() for r in regions) if self.trim_gap else sum(r.width() for r in regions)
        height = sum(r.height() for r in regions) if self.trim_gap else self.source.height()
        scale = min(self.width() / width, self.height() / height)
        x, y = (self.width() - width * scale) / 2, (self.height() - height * scale) / 2
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        for region in regions:
            target = QRectF(x, y, region.width() * scale, region.height() * scale)
            painter.drawPixmap(target, self.source, region)
            if self.trim_gap:
                y += target.height()
            else:
                x += target.width()

    def enlarge(self):
        if not self.expandable or self.source.isNull():
            return
        dialog = QDialog(self.window())
        dialog.setWindowTitle("Guide image")
        dialog.resize(1040, 540)
        dialog.setMinimumSize(600, 350)
        layout = QVBoxLayout(dialog)
        image = GuideImage(expandable=False)
        image.source = self.source
        image.compact = self.compact
        image.trim_gap = self.trim_gap
        layout.addWidget(image, 1)
        layout.addWidget(text_label(self.accessibleName().removesuffix(" · Enlarge"), "muted"))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Close")
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        apply_widgets(dialog)
        dialog.exec()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.enlarge()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.enlarge()
        else:
            super().keyPressEvent(event)


class GuidePanel(QFrame):
    def __init__(self, key, steps, *, title="Connection guide"):
        super().__init__()
        self.setObjectName("card")
        self.steps = steps
        self.heading = title
        self.index = 0
        self.key = f"guides/{key}/expanded-v2"
        self.preferences = QSettings(str(config_dir() / "interface.ini"), QSettings.Format.IniFormat)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)
        heading = QHBoxLayout()
        self.toggle = KeyboardButton()
        self.toggle.setObjectName("disclosureButton")
        self.toggle.setCheckable(True)
        self.toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        heading.addWidget(self.toggle, 1)
        layout.addLayout(heading)
        self.content = QWidget()
        body = QVBoxLayout(self.content)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(8)
        self.counter = text_label("", "eyebrow")
        self.title = text_label("")
        self.title.setStyleSheet("font-size:18px;font-weight:600")
        self.description = text_label("")
        self.description.setTextFormat(Qt.TextFormat.RichText)
        self.image = GuideImage()
        self.image.setMaximumHeight(140)
        self.caption = text_label("", "muted")
        self.caption.setStyleSheet("font-size:12px")
        for item in (self.counter, self.title, self.description, self.image, self.caption):
            body.addWidget(item)
        controls = QHBoxLayout()
        self.previous = KeyboardButton("Previous")
        self.previous.clicked.connect(lambda: self.go(self.index - 1))
        self.enlarge = KeyboardButton("Enlarge image")
        self.enlarge.setObjectName("quiet")
        self.enlarge.clicked.connect(self.image.enlarge)
        self.next = KeyboardButton()
        self.next.setObjectName("primary")
        self.next.clicked.connect(self.advance)
        controls.addWidget(self.previous)
        controls.addWidget(self.enlarge)
        controls.addStretch()
        controls.addWidget(self.next)
        body.addLayout(controls)
        layout.addWidget(self.content)
        self.toggle.toggled.connect(self.set_expanded)
        self.toggle.setChecked(self.preferences.value(self.key, False, type=bool))
        self.set_expanded(self.toggle.isChecked(), remember=False)
        self.go(0)

    def set_expanded(self, expanded, *, remember=True):
        focused = QApplication.focusWidget()
        if not expanded and focused is not None and self.content.isAncestorOf(focused):
            self.toggle.setFocus(Qt.FocusReason.OtherFocusReason)
        self.content.setVisible(expanded)
        self.toggle.setText(("⌄ " if expanded else "› ") + self.heading)
        self.toggle.setAccessibleName(self.heading)
        if remember:
            self.preferences.setValue(self.key, expanded)

    def go(self, index):
        self.index = max(0, min(index, len(self.steps) - 1))
        step = self.steps[self.index]
        self.counter.setText(f"Step {self.index + 1} of {len(self.steps)}")
        self.title.setText(step.title)
        self.description.setText(step.body)
        self.image.set_step(step)
        self.caption.setText(step.caption)
        self.previous.setEnabled(self.index > 0)
        self.next.setText("Close guide" if self.index == len(self.steps) - 1 else "Next")
        apply_widgets(self)

    def advance(self):
        if self.index < len(self.steps) - 1:
            self.go(self.index + 1)
        else:
            self.toggle.setChecked(False)


class Disclosure(QFrame):
    def __init__(self, title):
        super().__init__()
        self.title = title
        self.setObjectName("disclosure")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.toggle = KeyboardButton("› " + title)
        self.toggle.setAccessibleName(title)
        self.toggle.setObjectName("quiet")
        self.toggle.setCheckable(True)
        self.toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle.setStyleSheet("text-align:left")
        layout.addWidget(self.toggle)
        self.content = QWidget()
        self.body = QVBoxLayout(self.content)
        self.body.setContentsMargins(10, 0, 10, 8)
        self.body.setSpacing(8)
        layout.addWidget(self.content)
        self.content.hide()
        self.toggle.toggled.connect(self.set_expanded)
        self.toggle.toggled.connect(lambda expanded: self.toggle.setText(("⌄ " if expanded else "› ") + self.title))

    def set_expanded(self, expanded):
        focused = QApplication.focusWidget()
        if not expanded and focused is not None and self.content.isAncestorOf(focused):
            self.toggle.setFocus(Qt.FocusReason.OtherFocusReason)
        self.content.setVisible(expanded)
