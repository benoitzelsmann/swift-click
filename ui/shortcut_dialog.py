"""Dialog that records a Windows keyboard shortcut by pressing it."""
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel

from i18n import tr, apply_widgets
import sys
from keyboard_shortcuts import (MODIFIERS, MODIFIER_CODES, shortcut_label, ordered, modifier_labels,
                                native_key, held_modifiers)
from ui_controls import KeyboardButton


class ShortcutDialog(QDialog):
    """Press the keys together; Win can also be toggled because Windows keeps
    some Win shortcuts for itself before an application sees them."""

    def __init__(self, parent=None, binding=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Keyboard shortcut"))
        self.setMinimumWidth(460)
        binding = binding if isinstance(binding, dict) and binding.get("action") == "key_shortcut" else None
        self.modifiers = set(binding["modifiers"]) if binding else set()
        self.key = binding["key"] if binding else None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        title = QLabel("Record a keyboard shortcut")
        title.setStyleSheet("font-size:16px;font-weight:600")
        layout.addWidget(title)
        hint = QLabel("Press the keys together." if sys.platform == "darwin"
                      else "Press the keys together. Add Win with its button if Windows intercepts the shortcut.")
        hint.setWordWrap(True)
        hint.setObjectName("muted")
        layout.addWidget(hint)
        self.display = QLabel()
        self.display.setObjectName("shortcutDisplay")
        self.display.setProperty("i18nUserText", True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setMinimumHeight(56)
        self.display.setStyleSheet("font-size:20px;font-weight:600;border:1px solid palette(mid);border-radius:8px")
        layout.addWidget(self.display)
        chips = QHBoxLayout()
        chips.setSpacing(8)
        self.chips = {}
        for name in MODIFIERS:
            chip = KeyboardButton(modifier_labels()[name])
            chip.setObjectName("chip")
            chip.setCheckable(True)
            chip.setProperty("i18nUserText", True)
            chip.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            chip.clicked.connect(lambda checked, n=name: self.toggle(n, checked))
            self.chips[name] = chip
            chips.addWidget(chip)
        chips.addStretch()
        layout.addLayout(chips)
        buttons = QHBoxLayout()
        self.clear_button = KeyboardButton("Clear")
        self.clear_button.clicked.connect(self.clear)
        buttons.addWidget(self.clear_button)
        buttons.addStretch()
        cancel = KeyboardButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        self.save_button = KeyboardButton("Save")
        self.save_button.setObjectName("primary")
        self.save_button.clicked.connect(self.accept)
        buttons.addWidget(self.save_button)
        for button in (self.clear_button, cancel, self.save_button):
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addLayout(buttons)
        apply_widgets(self)
        self.render()

    def binding(self):
        return {"action": "key_shortcut", "modifiers": ordered(self.modifiers), "key": self.key}

    def render(self):
        empty = self.key is None and not self.modifiers
        self.display.setText(tr("Press a shortcut…") if empty else shortcut_label(self.binding()))
        for name, chip in self.chips.items():
            chip.setChecked(name in self.modifiers)
        self.save_button.setEnabled(not empty)

    def toggle(self, name, checked):
        (self.modifiers.add if checked else self.modifiers.discard)(name)
        self.render()

    def clear(self):
        self.modifiers, self.key = set(), None
        self.render()

    def record(self, vk, qt_modifiers):
        if not vk:
            return
        if vk in MODIFIER_CODES:
            # A modifier pressed alone starts a new shortcut.
            if self.key is not None:
                self.modifiers, self.key = set(), None
            self.modifiers.add(MODIFIER_CODES[vk])
        else:
            pressed = held_modifiers(qt_modifiers)
            # Keep a Win added by its button: Windows may hide it from the event.
            self.modifiers = pressed | (self.modifiers & {"win"})
            self.key = vk
        self.render()

    def event(self, event):
        # Every key, including Tab, Esc and Enter, is part of the shortcut.
        if event.type() == QEvent.Type.KeyPress:
            if not event.isAutoRepeat():
                self.record(native_key(event.nativeVirtualKey()), event.modifiers())
            return True
        if event.type() == QEvent.Type.ShortcutOverride:
            event.accept()
            return True
        return super().event(event)

    def keyPressEvent(self, event):
        event.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.grabKeyboard()

    def done(self, result):
        self.releaseKeyboard()
        super().done(result)


def ask_shortcut(parent, binding=None):
    dialog = ShortcutDialog(parent, binding)
    return dialog.binding() if dialog.exec() == QDialog.DialogCode.Accepted else None
