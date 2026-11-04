"""General preferences, credits and feedback links, independent of the engine."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QComboBox

from i18n import LANGUAGES, language


def metadata():
    return json.loads(Path(__file__).with_name("product.json").read_text(encoding="utf8"))


def contact_email():
    value = metadata().get("contact_email", "").strip()
    return value if re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+", value) else ""


def open_link(url):
    return QDesktopServices.openUrl(QUrl(url))


def build_about_pages(w):
    from desktop_ui import make_page, card, label, push, scroll_page
    info = metadata()
    page, box = make_page("General")
    surface, content = card()
    box.addWidget(surface)
    content.addWidget(label("Language", size=18))
    w.language_select = QComboBox()
    w.language_select.setAccessibleName("Language")
    for code, name in LANGUAGES.items():
        w.language_select.addItem(name, code)
    w.language_select.setCurrentIndex(w.language_select.findData(language()))
    w.language_select.currentIndexChanged.connect(lambda _: w.change_language(w.language_select.currentData()))
    content.addWidget(w.language_select)
    content.addWidget(label("Language changes apply immediately.", "muted"))
    box.addStretch()
    w.pages.addWidget(page)

    page, box = make_page("Credits")
    surface, content = card()
    box.addWidget(surface)
    version = Path(__file__).with_name("VERSION").read_text().strip()
    content.addWidget(label("Swift Click", size=20))
    content.addWidget(label(f"Version {version}", "muted"))
    content.addWidget(label(f"Created by {info['author']}"))
    content.addWidget(label("Built with Python, PySide6 / Qt, qasync, Bleak and python-zeroconf."))
    content.addWidget(label("OpenBikeControl and BikeControl provided protocol documentation and research references."))
    content.addWidget(label("Swift Click is independent of Zwift and MyWhoosh. Product names and logos belong to their respective owners.", "muted"))
    content.addWidget(label("Only the right-hand Click V2 (Y/A/B/Z/+) is supported.", "muted"))
    content.addWidget(push("Open GitHub", lambda: open_link(info["repository"])))
    notices = Path(sys.executable).parent / "notices" if getattr(sys, "frozen", False) else Path(__file__).parent / "dist/notices"
    licenses = push("Third-party licenses", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(notices))))
    licenses.setEnabled(notices.is_dir())
    content.addWidget(licenses)
    box.addStretch()
    w.pages.addWidget(scroll_page(page))

    page, box = make_page("Contact")
    surface, content = card()
    box.addWidget(surface)
    content.addWidget(label("Feedback and support", size=18))
    content.addWidget(label("Include the app version, Windows version and steps to reproduce. Remove personal information from screenshots and logs.", "muted"))
    w.report_button = push("Report a problem", lambda: open_link(info["repository"] + "/issues/new/choose"))
    content.addWidget(w.report_button)
    content.addWidget(push("Suggest an improvement", lambda: open_link(info["repository"] + "/issues/new?title=Feature%20request")))
    email = contact_email()
    w.contact_email_label = label(email or "Email contact is not available yet.", "muted")
    if email:
        w.contact_email_label.setProperty("i18nUserText", True)
    content.addWidget(w.contact_email_label)
    w.email_button = push("Send an email", lambda: open_link("mailto:" + quote(email, safe="@.+") + "?subject=Swift%20Click"))
    w.email_button.setEnabled(bool(email))
    content.addWidget(w.email_button)
    box.addStretch()
    w.pages.addWidget(page)
