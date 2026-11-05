"""Apple HIG-inspired semantic colors for every Qt surface; no extra dependencies."""
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

PALETTES = {
    "light": dict(text="#1d1d1f", muted="#606068", canvas="#f5f5f7", surface="#ffffff",
        subtle="#f2f2f5", hover="#eaeaef", pressed="#e5e5eb", border="#dedee4",
        strong_border="#a3a3ad", accent="#0066cc", accent_hover="#0054a8", on_accent="#ffffff",
        selection="#e6f0fc", focus="#0066cc", disabled="#83838d", disabled_surface="#eeeef2",
        track="#eeeef2", thumb="#b2b2bc", success="#237a46", danger="#b93830"),
    "dark": dict(text="#f5f5f7", muted="#b3b3bd", canvas="#1c1c1e", surface="#2c2c2e",
        subtle="#343437", hover="#414145", pressed="#48484e", border="#45454b",
        strong_border="#73737d", accent="#0a66c2", accent_hover="#0870cf", on_accent="#ffffff",
        selection="#243f5c", focus="#69b0ff", disabled="#8b8b95", disabled_surface="#343437",
        track="#303034", thumb="#64646e", success="#72d395", danger="#ff8a80"),
}
_current = "light"


def color(role):
    return PALETTES[_current][role]


def stylesheet(mode="light"):
    result = _STYLE
    # Longest names first avoids replacing @accent inside @accent_hover.
    for role in sorted(PALETTES[mode], key=len, reverse=True):
        result = result.replace("@" + role, PALETTES[mode][role])
    return result


def apply_theme(mode):
    global _current
    mode = mode if mode in PALETTES else "light"
    app = QApplication.instance()
    if mode == _current and app.styleSheet() == stylesheet(mode):
        return mode
    _current = mode
    palette = QPalette()
    roles = {"Window":"canvas", "WindowText":"text", "Base":"surface", "AlternateBase":"subtle",
             "Text":"text", "Button":"surface", "ButtonText":"text", "Highlight":"selection",
             "HighlightedText":"text", "ToolTipBase":"surface", "ToolTipText":"text", "PlaceholderText":"muted",
             "Link":"focus", "Light":"surface", "Mid":"border", "Dark":"strong_border"}
    for role, token in roles.items():
        palette.setColor(getattr(QPalette.ColorRole, role), QColor(color(token)))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(color("disabled")))
    app.setPalette(palette)
    app.setStyleSheet(stylesheet(mode))
    for widget in app.allWidgets():
        widget.update()
    return mode


_STYLE = """
QWidget { color:@text; font-family:'Segoe UI'; font-size:14px; }
QMainWindow, QWidget#shell, QWidget#page { background:@canvas; }
QFrame#header { background:@surface; border-bottom:1px solid @border; }
QPushButton#assignment { background:@subtle; border:1px solid @border; border-radius:6px; padding:4px 7px; font-weight:500; }
QPushButton#assignment:hover { border-color:@focus; color:@text; }
QPushButton#choice { background:@subtle; border:1px solid transparent; border-radius:6px; padding:8px 10px; }
QPushButton#choice:checked { background:@selection; border-color:@focus; color:@text; }
QPushButton#choice:hover { border-color:@focus; }
QPushButton#category { background:@subtle; border:1px solid @border; border-radius:7px; text-align:left; padding:12px 16px; }
QPushButton#category:hover { background:@hover; border-color:@strong_border; }
QLabel#brand { font-size:18px; font-weight:700; }
QLabel#title { font-size:22px; font-weight:500; }
QLabel#muted { color:@muted; }
QFrame#card { background:@surface; border:1px solid @border; border-radius:12px; }
QFrame#binding { background:@surface; border:1px solid @border; border-radius:6px; }
QFrame#binding[selected="true"] { background:@selection; border-color:@focus; }
QPushButton { background:@surface; border:1px solid @border; border-radius:10px; padding:8px 16px; font-weight:500; }
QPushButton:hover { background:@hover; border-color:@strong_border; }
QPushButton:pressed { background:@pressed; }
QPushButton#primary { background:@accent; color:@on_accent; border:1px solid @accent; }
QPushButton#primary:hover { background:@accent_hover; }
QPushButton#primary:disabled, QPushButton:disabled { color:@disabled; background:@disabled_surface; border-color:@border; }
QPushButton#nav { border:1px solid transparent; border-radius:8px; background:transparent; color:@muted; padding:7px 12px; }
QPushButton#nav:checked { color:@text; background:@pressed; border-color:@border; }
QFrame#subnav { background:@surface; border-bottom:1px solid @border; }
QPushButton#subnavButton { border:1px solid transparent; background:transparent; color:@muted; padding:5px 13px; }
QPushButton#subnavButton:checked { color:@text; background:@surface; border-color:@border; }
QPushButton#disclosureButton { border:1px solid @border; background:@subtle; text-align:left; padding:6px 12px; }
QPushButton#disclosureButton:hover { border-color:@focus; }
QPushButton#disclosureButton:checked { background:@selection; border-color:@focus; color:@text; }
QFrame#separator { background:@border; border:0; }
QLabel#eyebrow { color:@accent; font-size:12px; font-weight:500; }
QScrollArea { border:0; background:@canvas; }
QScrollBar:vertical { background:@track; width:8px; margin:0; }
QScrollBar::handle:vertical { background:@thumb; border-radius:4px; min-height:30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QPushButton:checked { background:@selection; color:@text; }
QPushButton#quiet { border:1px solid transparent; background:transparent; color:@muted; padding:3px 5px; }
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit { background:@subtle; border:1px solid @border; border-radius:7px; padding:6px 10px; min-height:24px; }
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover { border-color:@strong_border; }
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus { border-color:@accent; }
QComboBox::drop-down { border:0; width:18px; }
QComboBox QAbstractItemView { background:@surface; selection-background-color:@selection; color:@text; border:1px solid @border; }
QTextEdit { background:@surface; border:1px solid @border; border-radius:6px; padding:8px; color:@muted; font-size:12px; }
QListWidget, QWidget#emptyPositions { border:1px solid transparent; background:@subtle; border-radius:10px; padding:6px; }
QListWidget::item { padding:12px; margin-bottom:5px; border-radius:10px; }
QListWidget::item:selected { background:@selection; color:@text; }
QStatusBar { background:@canvas; color:@muted; }

QDialog, QMessageBox, QMenu { background:@surface; color:@text; }
QToolTip { background:@surface; color:@text; border:1px solid @border; padding:6px; }
QLabel { background:transparent; }
QLabel#title { font-size:24px; font-weight:600; }
QLabel#brand { font-size:17px; font-weight:600; }
QLabel#eyebrow { color:@muted; }
QPushButton:focus, QComboBox:focus, QLineEdit:focus { border-color:@accent; }
QPushButton#nav:hover, QPushButton#subnavButton:hover, QPushButton#quiet:hover { background:@hover; }
QPushButton#languageChoice { text-align:left; padding:12px 16px 12px 76px; border-radius:10px; background:@subtle; }
QPushButton#languageChoice:checked { background:@selection; border:1px solid @accent; }
QListWidget#catalog { background:transparent; border:0; padding:0; }
QListWidget#catalog::item { background:@subtle; border:1px solid transparent; border-radius:8px; padding:10px; margin-bottom:6px; }
QListWidget#catalog::item:hover { border-color:@strong_border; }
QListWidget#catalog::item:selected { background:@selection; border-color:@accent; color:@text; }
QLineEdit#routineName { font-size:18px; font-weight:600; padding:8px 12px; }
QLabel#preview { background:@subtle; border:1px solid @border; border-radius:8px; padding:4px; }
QLabel#iconBadge { background:@subtle; border-radius:10px; }
QMessageBox QLabel { font-size:13px; }
QMessageBox QLabel#qt_msgbox_label { font-size:17px; font-weight:600; }
QMessageBox QLabel#qt_msgbox_informativelabel { color:@muted; min-width:390px; }
QMessageBox QPushButton { min-width:80px; }
QMessageBox QPushButton:default { background:@accent; color:@on_accent; border-color:@accent; }
QMenu { border:1px solid @border; padding:6px; }
QMenu::item { padding:7px 24px; border-radius:5px; }
QMenu::item:selected { background:@selection; }
QMenu::separator { height:1px; background:@border; margin:5px; }
QProgressBar { background:@subtle; border:0; border-radius:4px; text-align:center; }
QProgressBar::chunk { background:@accent; border-radius:4px; }
QScrollBar:horizontal { background:@track; height:8px; }
QScrollBar::handle:horizontal { background:@thumb; border-radius:4px; min-width:30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0; }
"""
