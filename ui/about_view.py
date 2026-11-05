"""General preferences, credits and feedback links, independent of the engine."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from language_picker import LanguagePicker

from i18n import language


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
    w.language_select = LanguagePicker()
    w.language_select.setAccessibleName("Language")
    w.language_select.setCurrentIndex(w.language_select.findData(language()))
    w.language_select.currentIndexChanged.connect(lambda _: w.change_language(w.language_select.currentData()))
    content.addWidget(w.language_select)
    from timing_view import TimingSettings
    w.timing_settings=TimingSettings(w)
    box.addWidget(w.timing_settings)
    box.addStretch()
    w.pages.addWidget(scroll_page(page))

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
    github = push("Open GitHub", lambda: open_link(info["repository"]))
    github.setMaximumWidth(300)
    content.addWidget(github)
    notices = Path(sys.executable).parent / "notices" if getattr(sys, "frozen", False) else Path(__file__).parent / "dist/notices"
    licenses = push("Third-party licenses", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(notices))))
    licenses.setEnabled(notices.is_dir())
    licenses.setMaximumWidth(300)
    content.addWidget(licenses)
    box.addStretch()
    w.pages.addWidget(scroll_page(page))

    page, box = make_page("Contact")
    surface, content = card()
    box.addWidget(surface)
    content.addWidget(label("Feedback and support", size=18))
    content.addWidget(label("Describe the problem and include your app version. Remove personal details from attachments.", "muted"))
    w.report_button = push("Report a problem", lambda: open_link(info["repository"] + "/issues/new/choose"))
    content.addWidget(w.report_button)
    w.report_button.setMaximumWidth(300)
    suggestion = push("Suggest an improvement", lambda: open_link(info["repository"] + "/issues/new?title=Feature%20request"))
    suggestion.setMaximumWidth(300)
    content.addWidget(suggestion)
    email = contact_email()
    w.contact_email_label = label(email or "Email contact is not available yet.", "muted")
    if email:
        w.contact_email_label.setProperty("i18nUserText", True)
    content.addWidget(w.contact_email_label)
    w.contact_email_label.setVisible(bool(email))
    w.email_button = push("Send an email", lambda: open_link("mailto:" + quote(email, safe="@.+") + "?subject=Swift%20Click"))
    w.email_button.setEnabled(bool(email))
    w.email_button.setVisible(bool(email))
    w.email_button.setMaximumWidth(300)
    content.addWidget(w.email_button)
    box.addStretch()
    w.pages.addWidget(page)
