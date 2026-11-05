"""Opt-in release checks and minimal, private-by-default support information."""
import asyncio
import json
import platform
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPOSITORY = "https://github.com/benoitzelsmann/swift-click"
RELEASE_API = "https://api.github.com/repos/benoitzelsmann/swift-click/releases/latest"
MAX_RESPONSE = 128 * 1024


def version_numbers(version):
    match = re.fullmatch(r"v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version)
    if not match:
        raise ValueError("Invalid release version")
    return tuple(int(part) for part in match.groups())


def latest_release():
    request = Request(RELEASE_API, headers={"Accept": "application/vnd.github+json", "User-Agent": "SwiftClick-UpdateCheck"})
    try:
        with urlopen(request, timeout=8) as response:
            if response.geturl() != RELEASE_API:
                raise ValueError("Unexpected release endpoint")
            raw = response.read(MAX_RESPONSE + 1)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    if len(raw) > MAX_RESPONSE:
        raise ValueError("Release response too large")
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("draft") is not False or data.get("prerelease") is not False:
        raise ValueError("Invalid release response")
    tag = data.get("tag_name")
    if not isinstance(tag, str):
        raise ValueError("Invalid release version")
    version_numbers(tag)
    link = REPOSITORY + "/releases/tag/" + tag
    if data.get("html_url") != link:
        raise ValueError("Unexpected release destination")
    return tag.removeprefix("v"), link


async def check_for_updates(window):
    if window.closing or window.update_check_running:
        return
    window.update_check_running = True
    window.update_button.setEnabled(False)
    window.update_status.setText("Checking for updates…")
    window.update_link.hide()
    window.refresh()
    try:
        release = await asyncio.to_thread(latest_release)
        if window.closing:
            return
        if release and version_numbers(release[0]) > version_numbers(window.app_version):
            window.update_status.setText("Version {version} is available.".format(version=release[0]))
            window.update_url = release[1]
            window.update_link.show()
        else:
            window.update_status.setText("You have the latest available version.")
    except (OSError, URLError, ValueError, TypeError, RecursionError):
        if not window.closing:
            window.update_status.setText("Could not check for updates. Check your connection and try again.")
    finally:
        window.update_check_running = False
        if not window.closing:
            window.update_button.setEnabled(True)
            window.refresh()


def support_report(window):
    """Allowlist technical facts; avoid log text, paths, addresses and target names."""
    from PySide6 import __version__ as qt_version
    from i18n import language
    config = window.controller.config
    report = {
        "application": "Swift Click", "version": window.app_version,
        "system": platform.system(), "system_release": platform.release(),
        "architecture": platform.machine(), "qt": qt_version,
        "language": language(), "appearance": window.appearance,
        "controller_connected": bool(window.controller.connected),
        "network_ready": bool(window.is_ready),
        "saved_windows": len(config["windows"]), "saved_positions": len(config["positions"]),
        "saved_routines": len(config["routines"]),
        "settings_loaded": window.controller.config_error is None,
    }
    return json.dumps(report, ensure_ascii=False, indent=2)


def copy_support_report(window):
    from PySide6.QtWidgets import QApplication
    QApplication.clipboard().setText(support_report(window))
    window.support_status.setText("Technical details copied. Paste them into your issue report.")
    window.refresh()
