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
    from PySide6.QtWidgets import QHBoxLayout, QButtonGroup
    appearance_row = QHBoxLayout()
    appearance_row.addWidget(label("Appearance", size=16), 1)
    w.appearance_group = QButtonGroup(w)
    w.appearance_buttons = {}
    for mode, title in (("light", "Light"), ("dark", "Dark"), ("system", "System")):
        button = push(title, lambda checked=False, value=mode: w.change_appearance(value))
        button.setMinimumWidth(110)
        button.setCheckable(True)
        button.setChecked(w.appearance == mode)
        button.setAccessibleName(title)
        w.appearance_group.addButton(button)
        w.appearance_buttons[mode] = button
        appearance_row.addWidget(button)
    content.addLayout(appearance_row)
    language_row = QHBoxLayout()
    language_row.addWidget(label("Language", size=16), 1)
    w.language_select = LanguagePicker()
    w.language_select.setAccessibleName("Language")
    w.language_select.setCurrentIndex(w.language_select.findData(language()))
    w.language_select.currentIndexChanged.connect(lambda _: w.change_language(w.language_select.currentData()))
    language_row.addWidget(w.language_select, 2)
    content.addLayout(language_row)
    from timing_view import TimingSettings
    w.timing_settings=TimingSettings(w)
    box.addWidget(w.timing_settings)
    from connection_help import Disclosure
    from ui_controls import NumericSpin, number_stepper
    from navigation_settings import save_navigation
    advanced = Disclosure("Advanced controls")
    advanced.body.addWidget(label("MyWhoosh directions", size=16))
    advanced.body.addWidget(label("Network works in the background. Keyboard needs MyWhoosh in front.", "muted"))
    from ui_controls import ChoiceGroup
    w.route_via = ChoiceGroup()
    w.route_via.setAccessibleName("MyWhoosh directions")
    from i18n import tr
    w.route_via.addItem(tr("Network (OpenBikeControl)"), "network")
    w.route_via.addItem(tr("Keyboard (A / D)"), "keyboard")
    w.route_via.setCurrentIndex(max(0, w.route_via.findData(w.controller.config.get("navigation", {}).get("route_via", "network"))))
    advanced.body.addWidget(w.route_via)
    advanced.body.addWidget(label("Route key duration", size=16))
    advanced.body.addWidget(label("How long a direction stays pressed.", "muted"))
    w.route_duration = NumericSpin()
    w.route_duration.setRange(100, 2000)
    w.route_duration.setSingleStep(50)
    w.route_duration.setSuffix(" ms")
    w.route_duration.setValue(w.controller.config.get("navigation", {}).get("press_ms", 500))
    controls, _, _ = number_stepper(w.route_duration, "Route key duration")
    advanced.body.addWidget(controls)
    advanced.body.addWidget(push("Save directions", lambda: save_navigation(w)))
    box.addWidget(advanced)
    backup_surface, backup_content = card()
    backup_content.addWidget(label("Settings backup", size=18))
    backup_content.addWidget(label("Everything, in one local file.", "muted"))
    from configuration_backup import choose_export, choose_import
    backup_row = QHBoxLayout()
    backup_row.addWidget(push("Export settings", lambda: choose_export(w)))
    backup_row.addWidget(push("Restore settings", lambda: choose_import(w)))
    backup_row.addStretch()
    backup_content.addLayout(backup_row)
    box.addWidget(backup_surface)
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
    content.addWidget(label("Protocol references: OpenBikeControl and BikeControl."))
    content.addWidget(label("Independent of Zwift and MyWhoosh. Names and logos belong to their owners.", "muted"))
    github = push("Open GitHub", lambda: open_link(info["repository"]))
    github.setMaximumWidth(300)
    content.addWidget(github)
    from app_support import check_for_updates, copy_support_report
    w.update_check_running = False
    w.update_url = ""
    update_surface, update_content = card()
    update_content.addWidget(label("Updates", size=18))
    update_content.addWidget(label("Checked only when you ask.", "muted"))
    update_actions = QHBoxLayout()
    w.update_button = push("Check for updates", lambda: w.launch(check_for_updates(w)))
    w.update_link = push("View release", lambda: open_link(w.update_url))
    w.update_link.hide()
    update_actions.addWidget(w.update_button)
    update_actions.addWidget(w.update_link)
    update_actions.addStretch()
    update_content.addLayout(update_actions)
    w.update_status = label("", "muted")
    update_content.addWidget(w.update_status)
    box.addWidget(update_surface)
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
    content.addWidget(label("Describe the problem and your app version.", "muted"))
    w.report_button = push("Report a problem", lambda: open_link(info["repository"] + "/issues/new/choose"))
    suggestion = push("Suggest an improvement", lambda: open_link(info["repository"] + "/issues/new?title=Feature%20request"))
    support_row = QHBoxLayout()
    support_row.setSpacing(10)
    for widget in (w.report_button, suggestion, push("Copy technical details", lambda: copy_support_report(w))):
        support_row.addWidget(widget)
    support_row.addStretch()
    content.addLayout(support_row)
    content.addWidget(label("Versions, connection states, item counts.", "muted"))
    w.support_status = label("", "muted")
    content.addWidget(w.support_status)
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
    w.pages.addWidget(scroll_page(page))
