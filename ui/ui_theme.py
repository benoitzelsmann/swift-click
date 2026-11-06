"""Calm semantic colors for every Qt surface; no extra dependencies.

Cool neutral surfaces carry the hierarchy; one blue accent marks actions and selection.
"""
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

PALETTES = {
    "light": dict(text="#15171a", muted="#5a6170", canvas="#f6f7f9", surface="#ffffff",
        subtle="#f0f2f5", hover="#e8ebf0", pressed="#dfe3ea", border="#e2e5ea",
        strong_border="#b4bac5", accent="#2563eb", accent_hover="#1d4fd8", on_accent="#ffffff",
        selection="#e7effd", focus="#2563eb", disabled="#8a909b", disabled_surface="#eef0f3",
        track="#eef0f3", thumb="#c3c8d1", success="#1f7a45", danger="#c0262d", nav="#eff1f4"),
    "dark": dict(text="#eef0f3", muted="#a3aab6", canvas="#111317", surface="#1a1d22",
        subtle="#22262c", hover="#2a2f36", pressed="#323840", border="#2c3138",
        strong_border="#5d6470", accent="#6ea8fe", accent_hover="#8bb9ff", on_accent="#0b1220",
        selection="#1d3354", focus="#6ea8fe", disabled="#7d838e", disabled_surface="#1f2227",
        track="#1a1d22", thumb="#474d57", success="#6fd39a", danger="#ff8a8a", nav="#1e2126"),
}
_current = "light"


def color(role):
    return PALETTES[_current][role]


def current_mode():
    return _current


def stylesheet(mode="light"):
    result = _STYLE
    # Longest names first avoids replacing @accent inside @accent_hover.
    for role in sorted(PALETTES[mode], key=len, reverse=True):
        result = result.replace("@" + role, PALETTES[mode][role])
    return result


def apply_theme(mode):
    global _current
    preference = mode if mode in (*PALETTES, "system") else "light"
    app = QApplication.instance()
    if preference == "system":
        mode = "dark" if app.styleHints().colorScheme() == Qt.ColorScheme.Dark else "light"
    else:
        mode = preference
    if mode == _current and app.styleSheet() == stylesheet(mode):
        return preference
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
    return preference


_STYLE = """
QWidget { color:@text; font-family:'Segoe UI'; font-size:14px; }
QMainWindow, QWidget#shell, QWidget#page { background:@canvas; }
QLabel { background:transparent; }
QToolTip { background:@surface; color:@text; border:1px solid @border; padding:6px 10px; }

QFrame#header { background:@surface; border-bottom:1px solid @border; }
QLabel#brand { font-size:17px; font-weight:700; }
QLabel#version { color:@muted; font-size:11px; font-weight:600; background:@subtle; border-radius:8px; padding:2px 8px; }
QFrame#navGroup { background:@nav; border:1px solid @border; border-radius:12px; }
QPushButton#nav, QPushButton#settingsNav { border:1px solid transparent; border-radius:9px; background:transparent; color:@muted; padding:6px 14px; font-weight:500; min-height:18px; }
QPushButton#nav:hover, QPushButton#settingsNav:hover { color:@text; background:@hover; }
QPushButton#nav:checked, QPushButton#settingsNav:checked { color:@text; background:@surface; border-color:@border; }
QPushButton#nav:focus, QPushButton#settingsNav:focus { border-color:@accent; }
QFrame#subnav { background:@surface; border-bottom:1px solid @border; }
QPushButton#subnavButton { border:0; border-bottom:2px solid transparent; border-radius:0; background:transparent; color:@muted; padding:9px 2px 7px 2px; margin-right:20px; font-weight:500; min-height:18px; }
QPushButton#subnavButton:hover { color:@text; background:transparent; }
QPushButton#subnavButton:checked { color:@text; border-bottom:2px solid @accent; background:transparent; }

QLabel#title { font-size:26px; font-weight:700; }
QLabel#eyebrow { color:@muted; font-size:12px; font-weight:600; }
QLabel#muted { color:@muted; }

QFrame#card { background:@surface; border:1px solid @border; border-radius:16px; }
QFrame#binding { background:@surface; border:1px solid @border; border-radius:12px; }
QFrame#binding[selected="true"] { background:@selection; border-color:@accent; }
QFrame#separator { background:@border; border:0; }
QFrame#recoveryNotice { background:@selection; border-bottom:1px solid @accent; }
QLabel#preview { background:@subtle; border:1px solid @border; border-radius:10px; padding:4px; }
QLabel#iconBadge { background:@selection; border-radius:12px; }

QPushButton { background:@surface; border:1px solid @border; border-radius:10px; padding:8px 16px; font-weight:500; min-height:20px; }
QPushButton:hover { background:@hover; border-color:@strong_border; }
QPushButton:pressed { background:@pressed; }
QPushButton:checked { background:@selection; color:@text; border-color:@accent; }
QPushButton:focus { border-color:@accent; }
QPushButton:disabled { color:@disabled; background:@disabled_surface; border-color:@border; }
QPushButton#primary { background:@accent; color:@on_accent; border:1px solid @accent; font-weight:600; }
QPushButton#primary:hover { background:@accent_hover; border-color:@accent_hover; }
QPushButton#primary:disabled { color:@disabled; background:@disabled_surface; border-color:@border; }
QPushButton#danger { color:@danger; }
QPushButton#danger:hover { border-color:@danger; background:@surface; }
QPushButton#danger:disabled { color:@disabled; background:@disabled_surface; border-color:@border; }
QPushButton#quiet { border:1px solid transparent; background:transparent; color:@muted; padding:4px 8px; }
QPushButton#quiet:hover { background:@hover; color:@text; }
QPushButton#assignment { background:@subtle; border:1px solid transparent; border-radius:9px; padding:5px 9px; font-weight:500; min-height:16px; }
QPushButton#assignment:hover { border-color:@accent; background:@surface; }
QPushButton#choice, QPushButton#chip { background:@subtle; border:1px solid transparent; border-radius:10px; padding:8px 14px; }
QPushButton#choice:hover, QPushButton#chip:hover { border-color:@strong_border; background:@subtle; }
QPushButton#choice:checked, QPushButton#chip:checked { background:@selection; border-color:@accent; color:@text; }
QPushButton#chip:disabled { background:@disabled_surface; color:@disabled; }
QPushButton#option { background:@subtle; border:1px solid transparent; border-radius:10px; text-align:left; padding:8px 12px; }
QPushButton#option:hover { border-color:@strong_border; background:@hover; }
QPushButton#option:checked { background:@selection; border-color:@accent; color:@text; font-weight:600; }
QLabel#pill { color:@text; font-size:12px; background:@subtle; border-radius:11px; padding:4px 10px; }
QPushButton#category { background:@subtle; border:1px solid transparent; border-radius:12px; text-align:left; padding:13px 16px; }
QPushButton#category:hover { background:@hover; border-color:@strong_border; }
QPushButton#disclosureButton { border:1px solid transparent; background:@subtle; border-radius:10px; text-align:left; padding:9px 14px; font-weight:600; }
QPushButton#disclosureButton:hover { background:@hover; border-color:transparent; }
QPushButton#disclosureButton:checked { background:@subtle; border-color:transparent; color:@text; }
QPushButton#languageChoice { text-align:left; padding:12px 16px 12px 76px; border-radius:12px; background:@subtle; border:1px solid transparent; }
QPushButton#languageChoice:hover { border-color:@strong_border; }
QPushButton#languageChoice:checked { background:@selection; border:1px solid @accent; }

QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox { background:@surface; border:1px solid @border; border-radius:10px; padding:7px 12px; min-height:22px; selection-background-color:@selection; selection-color:@text; }
QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover, QComboBox:hover { border-color:@strong_border; }
QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus, QComboBox:focus { border-color:@accent; }
QLineEdit:disabled { color:@disabled; background:@disabled_surface; }
QLineEdit#routineName { font-size:18px; font-weight:600; padding:9px 14px; }
QComboBox::drop-down { border:0; width:22px; }
QComboBox QAbstractItemView { background:@surface; selection-background-color:@selection; color:@text; border:1px solid @border; padding:4px; }
QTextEdit { background:@subtle; border:1px solid transparent; border-radius:10px; padding:10px; color:@muted; font-size:12px; }

QListWidget, QWidget#emptyPositions { border:1px solid transparent; background:@subtle; border-radius:12px; padding:6px; }
QListWidget::item { padding:12px; margin-bottom:6px; border-radius:10px; }
QListWidget::item:selected { background:@selection; color:@text; }
QListWidget#catalog { background:transparent; border:0; padding:0; }
QListWidget#catalog::item { background:@subtle; border:1px solid transparent; border-radius:12px; padding:11px; margin-bottom:6px; }
QListWidget#catalog::item:hover { border-color:@strong_border; }
QListWidget#catalog::item:selected { background:@selection; border-color:@accent; color:@text; }

QScrollArea { border:0; background:@canvas; }
QScrollBar:vertical { background:transparent; width:10px; margin:2px; }
QScrollBar::handle:vertical { background:@thumb; border-radius:3px; min-height:36px; margin:0 2px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background:transparent; }
QScrollBar:horizontal { background:transparent; height:10px; margin:2px; }
QScrollBar::handle:horizontal { background:@thumb; border-radius:3px; min-width:36px; margin:2px 0; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background:transparent; }

QDialog, QMessageBox, QMenu { background:@surface; color:@text; }
QMessageBox QLabel { font-size:13px; }
QMessageBox QLabel#qt_msgbox_label { font-size:17px; font-weight:600; }
QMessageBox QLabel#qt_msgbox_informativelabel { color:@muted; min-width:390px; }
QMessageBox QPushButton { min-width:88px; }
QMessageBox QPushButton:default { background:@accent; color:@on_accent; border-color:@accent; font-weight:600; }
QMenu { border:1px solid @border; padding:6px; }
QMenu::item { padding:8px 26px 8px 14px; border-radius:8px; }
QMenu::item:selected { background:@selection; }
QMenu::separator { height:1px; background:@border; margin:5px 8px; }
QProgressBar { background:@subtle; border:0; border-radius:4px; text-align:center; }
QProgressBar::chunk { background:@accent; border-radius:4px; }
QStatusBar { background:@canvas; color:@muted; }
"""
