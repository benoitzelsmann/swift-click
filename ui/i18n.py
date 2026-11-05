"""English source strings with live French presentation; user content stays intact."""
import json
import re
from pathlib import Path
from string import Formatter

LANGUAGES = {"en": "English", "fr": "Français"}
_language = "en"
_french = json.loads((Path(__file__).with_name("locales") / "fr.json").read_text(encoding="utf8"))
_patterns = []
# A specific sentence must win over a generic prefix such as "Version {version}".
for source, target in sorted(_french.items(),
        key=lambda item: len(re.sub(r"\{[^{}]*\}", "", item[0])), reverse=True):
    if "{" in source:
        parts = list(Formatter().parse(source))
        expression = "".join(re.escape(literal) + (r"(.+?)" if field else "")
                             for literal, field, _, _ in parts)
        fields = [field for _, field, _, _ in parts if field]
        _patterns.append((re.compile(expression, re.DOTALL), fields, target))


def set_language(code):
    global _language
    if code not in LANGUAGES:
        raise ValueError("Unsupported language")
    _language = code


def language():
    return _language


def tr(text):
    if _language == "en" or not text:
        return text
    if text in _french:
        return _french[text]
    for pattern, fields, target in _patterns:
        match = pattern.fullmatch(text)
        if match:
            return target.format(**dict(zip(fields, match.groups())))
    for separator in ("\n", " · ", " — ", ": ", " / "):
        if separator in text:
            return separator.join(tr(part) for part in text.split(separator))
    if text[:2] in ("› ", "⌄ "):
        return text[:2] + tr(text[2:])
    return text


def apply_widgets(root):
    """Track canonical source properties so changing language never chains translations."""
    from PySide6.QtWidgets import QWidget, QLabel, QAbstractButton, QLineEdit, QMessageBox
    for widget in [root, *root.findChildren(QWidget)]:
        properties = ["toolTip", "accessibleName", "windowTitle"]
        if widget.property("i18nUserTooltip"):
            properties.remove("toolTip")
        if widget.property("i18nUserAccessible"):
            properties.remove("accessibleName")
        if isinstance(widget, QMessageBox):
            properties.extend(["informativeText", "detailedText"])
        if isinstance(widget, (QLabel, QAbstractButton)) and not widget.property("i18nUserText"):
            properties.append("text")
        if isinstance(widget, QLineEdit):
            properties.append("placeholderText")
        for name in properties:
            current = widget.property(name)
            if not isinstance(current, str) or not current:
                continue
            original = widget.property("i18nSource_" + name)
            previous = widget.property("i18nRendered_" + name)
            if original is None or current != previous:
                original = current
                if widget.property("i18nSource_" + name) != original:
                    widget.setProperty("i18nSource_" + name, original)
            translated = tr(original)
            if current != translated:
                widget.setProperty(name, translated)
            if previous != translated:
                widget.setProperty("i18nRendered_" + name, translated)
