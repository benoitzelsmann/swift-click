"""Versioned local configuration backups and validated, reversible restoration."""
import copy
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from settings import validate, write_config
from app_paths import config_dir

MAX_BACKUP_BYTES = 16 * 1024 * 1024


def read_backup(path):
    with Path(path).open("rb") as file:
        raw = file.read(MAX_BACKUP_BYTES + 1)
    if len(raw) > MAX_BACKUP_BYTES:
        raise ValueError("The backup is too large.")
    try:
        data = json.loads(raw.decode("utf-8-sig"))
        if isinstance(data, dict) and data.get("format") == "swift-click-backup":
            if data.get("version") != 1:
                raise ValueError("Unsupported backup version.")
            data = data.get("configuration")
        return validate(data)
    except (UnicodeError, RecursionError) as exc:
        raise ValueError("This file is not a valid Swift Click backup.") from exc


def export_backup(path, configuration):
    payload = {"format": "swift-click-backup", "version": 1,
               "created_at": datetime.now(timezone.utc).isoformat(),
               "configuration": validate(configuration)}
    write_config(Path(path), payload)


def restore_backup(controller, configuration):
    """Validate first, preserve current data, then commit using the controller."""
    restored = validate(configuration)
    if controller.connected or (controller.task and not controller.task.done()) or controller.oad_pending or controller.windows.lock.locked():
        raise ValueError("Disconnect the controller before restoring a backup.")
    directory = config_dir() / "backups"
    directory.mkdir(exist_ok=True)
    backup = directory / ("before-restore-" + datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8] + ".json")
    export_backup(backup, copy.deepcopy(controller.config))
    controller.save(restored)
    controller.router.reset()
    return backup


def choose_export(window):
    from PySide6.QtWidgets import QFileDialog
    from ui_controls import show_message
    from i18n import tr
    filename, _ = QFileDialog.getSaveFileName(window, tr("Export settings"),
        "SwiftClick-settings.json", tr("JSON backup (*.json)"))
    if not filename:
        return
    try:
        export_backup(filename, window.controller.config)
        show_message(window, "Settings exported", "Keep this file private. It contains your controller address and saved window paths.")
    except (OSError, ValueError) as exc:
        window.show_error(str(exc))


def choose_import(window):
    from PySide6.QtWidgets import QFileDialog
    from ui_controls import confirm_dialog, show_message
    from i18n import tr
    if window.connecting_ble or window.controller.connected or (window.controller.task and not window.controller.task.done()) or window.controller.oad_pending:
        show_message(window, "Restore settings", "Disconnect the controller before restoring a backup.")
        return
    if window.routines_page.testing or window.mouse_page.testing or window.mouse_page.capturing or window.windows_page.opening:
        show_message(window, "Restore settings", "Wait for the current action to finish before restoring settings.")
        return
    filename, _ = QFileDialog.getOpenFileName(window, tr("Restore settings"), "", tr("JSON backup (*.json)"))
    if not filename:
        return
    try:
        configuration = read_backup(filename)
        if not confirm_dialog(window, "Restore settings", "Replace assignments, windows, positions and routines with this backup? A copy of your current settings will be saved first.", accept="Restore"):
            return
        recovery = restore_backup(window.controller, configuration)
        window.editor.end_edit()
        window.mouse_page.cancel()
        window.windows_page.finish()
        window.routines_page.finish()
        window.load_bindings()
        window.mouse_page.reload()
        window.windows_page.reload()
        window.routines_page.reload()
        window.timing_settings.load(configuration["timings"])
        window.route_duration.setValue(configuration["navigation"]["press_ms"])
        window.intensity_clicks.setValue(configuration["navigation"]["intensity_clicks"])
        window.route_via.setCurrentIndex(max(0, window.route_via.findData(configuration["navigation"]["route_via"])))
        window.refresh()
        show_message(window, "Settings restored", tr("Your previous settings were saved to:") + "\n" + str(recovery))
    except (OSError, ValueError) as exc:
        window.show_error(str(exc))
