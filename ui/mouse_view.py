"""Named screen positions, edited inside the page without a capture overlay."""
import asyncio
import base64
import copy
import math
import threading
import uuid

from PySide6.QtCore import Qt, QByteArray, QBuffer, QIODevice, QPointF
from PySide6.QtGui import QColor, QImageReader, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QStackedWidget

import mouse_controls
from desktop_ui import card, label, push, make_page, show_page, PAGE_BUTTONS
from ui_controls import CatalogList, CountdownOverlay, confirm_dialog
from i18n import tr
from settings import routine_references
from ui_icons import application_icon, application_name, icon


def capture_preview(point, physical):
    """Grab a small screen-local crop in Qt coordinates, using the saved physical pixel."""
    origin = (physical[0] - point["x"], physical[1] - point["y"])
    screen = next((s for s in QApplication.screens()
                   if (s.geometry().x(), s.geometry().y()) == origin), None)
    if not screen:
        return None
    size = screen.geometry().size()
    width, height = min(192, size.width()), min(108, size.height())
    scale = screen.devicePixelRatio()
    x, y = point["x"] / scale, point["y"] / scale
    left = max(0, min(math.floor(x - width / 2), size.width() - width))
    top = max(0, min(math.floor(y - height / 2), size.height() - height))
    shot = screen.grabWindow(0, left, top, width, height)
    if shot.isNull():
        return None
    image = shot.toImage().scaled(width, height, Qt.AspectRatioMode.IgnoreAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
    image.setDevicePixelRatio(1)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    center = QPointF(x - left, y - top)
    painter.setPen(QPen(QColor("#16271f"), 4))
    painter.drawEllipse(center, 6, 6)
    painter.setPen(QPen(QColor("#a7f3c7"), 2))
    painter.drawEllipse(center, 6, 6)
    painter.end()
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    return bytes(data.toBase64()).decode("ascii") if image.save(buffer, "JPEG", 85) else None


class MousePage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.capturing = False
        self.testing = False
        self.editing = None
        self.draft = None
        self.captured_window = None
        self.binding_field = None
        self.countdown_overlay = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.add = push("Add a position",self.new,True)
        page, body = make_page("Mouse positions",action=self.add)
        layout.addWidget(page)
        surface, box = card()
        box.setContentsMargins(16,12,16,12)
        box.setSpacing(8)
        body.addWidget(surface,1)
        self.stack = QStackedWidget()
        box.addWidget(self.stack,1)
        catalogue = QWidget()
        rows = QVBoxLayout(catalogue)
        rows.setContentsMargins(0,0,0,0)
        self.list = CatalogList()
        self.list.setAccessibleName("Saved mouse positions")
        self.list.currentRowChanged.connect(self.selection)
        self.list.itemDoubleClicked.connect(lambda _: self.edit_selected())
        from ui_controls import CatalogSearch
        self.search = CatalogSearch(self.list, "Search positions")
        rows.addWidget(self.search)
        rows.addWidget(self.list,1)
        self.empty = label("No saved positions", "muted")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rows.addWidget(self.empty,1)
        actions = QHBoxLayout()
        self.edit_button = push("Edit", self.edit_selected)
        self.test = push("Test", lambda: window.launch(self.test_point()))
        self.delete = push("Delete", self.remove)
        for button in (self.edit_button, self.test, self.delete):
            actions.addWidget(button)
        actions.addStretch()
        rows.addLayout(actions)
        self.stack.addWidget(catalogue)
        self.edit = QWidget()
        editor = QVBoxLayout(self.edit)
        editor.setContentsMargins(0,0,0,0)
        editor.setSpacing(10)
        self.editor_title = label("Position",size=18)
        self.editor_title.setProperty("i18nUserText", True)
        editor.addWidget(self.editor_title)
        self.name = QLineEdit()
        self.name.setMaxLength(60)
        self.name.setMinimumHeight(34)
        self.name.setPlaceholderText("Position name")
        self.name.setAccessibleName("Position name")
        editor.addWidget(self.name)
        self.details = label("","muted")
        self.details.setProperty("i18nUserText",True)
        editor.addWidget(self.details)
        self.window_info = label("", "muted")
        self.window_info.setTextFormat(Qt.TextFormat.PlainText)
        self.window_info.setProperty("i18nUserText",True)
        editor.addWidget(self.window_info)
        self.draft_preview = self.preview_label()
        editor.addWidget(self.draft_preview,alignment=Qt.AlignmentFlag.AlignLeft)
        editor.addStretch()
        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.capture = push("Capture position",lambda: window.launch(self.capture_point()),True)
        self.capture.setProperty("i18nUserText", True)
        self.capture.setToolTip("Point at the target within 3 s. Nothing is clicked.")
        self.save_name = push("Save",self.commit_name,True)
        self.cancel_button = push("Cancel",self.cancel)
        controls.addWidget(self.cancel_button)
        controls.addStretch()
        controls.addWidget(self.capture)
        controls.addWidget(self.save_name)
        editor.addLayout(controls)
        self.note = label("","muted")
        self.note.hide()
        box.addWidget(self.note)
        self.stack.addWidget(self.edit)
        self.name.textChanged.connect(self.update_save_enabled)
        self.reload()

    def points(self):
        return self.window.controller.config["positions"]

    def preview_label(self):
        widget = label("")
        widget.setAccessibleName("Captured mouse position preview")
        widget.setObjectName("preview")
        widget.hide()
        return widget

    def show_preview(self, widget, point):
        widget.clear()
        preview = point.get("preview")
        if preview:
            buffer = QBuffer()
            buffer.setData(QByteArray.fromBase64(preview.encode("ascii")))
            buffer.open(QIODevice.OpenModeFlag.ReadOnly)
            reader = QImageReader(buffer, b"JPEG")
            size = reader.size()
            if 0 < size.width() <= 192 and 0 < size.height() <= 108:
                widget.setPixmap(QPixmap.fromImage(reader.read()))
        widget.setVisible(widget.pixmap() is not None and not widget.pixmap().isNull())

    def current_id(self):
        item = self.list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def location_text(self, point):
        screen = point["screen"]["device"].split("DISPLAY")[-1]
        display = tr("Display {number}").format(number=screen)
        state = "" if mouse_controls.is_valid(point) else " · " + tr("Position needs updating")
        return f"{display} · {point['x']}, {point['y']} px{state}"

    def refresh_language(self):
        self.reload()
        if self.stack.currentWidget() is self.edit:
            self.show_capture()
            self.editor_title.setText(tr("Position" if self.editing else "New position"))

    def reload(self, selected=None):
        selected = selected or self.current_id()
        self.list.blockSignals(True)
        self.list.clear()
        for ident,point in self.points().items():
            detail = self.location_text(point)
            self.list.addItem(point["name"] + "\n" + detail)
            item = self.list.item(self.list.count()-1)
            item.setData(Qt.ItemDataRole.UserRole,ident)
            if point.get("window"):
                item.setIcon(application_icon(point["window"]["path"]))
            else:
                item.setIcon(icon("position"))
            if ident == selected:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        if self.list.count() and self.list.currentRow() < 0:
            self.list.setCurrentRow(0)
        self.search.apply_filter()
        self.list.setVisible(bool(self.list.count()))
        self.empty.setVisible(not self.list.count())
        self.selection()

    def selection(self, *_):
        ident = self.current_id()
        busy = self.capturing or self.testing
        self.add.setEnabled(not busy)
        self.list.setEnabled(not busy)
        self.name.setEnabled(not busy)
        self.cancel_button.setEnabled(not busy)
        for button in (self.edit_button,self.test,self.delete):
            button.setVisible(bool(self.points()))
            button.setEnabled(bool(ident) and not busy)
        self.test.setEnabled(bool(ident) and not busy and mouse_controls.is_valid(self.points()[ident]))
        self.update_save_enabled()

    def new(self, _checked=False, *, binding_field=None):
        if self.capturing or self.testing:
            return
        self.editing = None
        self.draft = None
        self.binding_field = binding_field
        self.name.clear()
        self.open_editor()

    def open_editor(self):
        self.stack.setCurrentWidget(self.edit)
        self.editor_title.setText(tr("Position" if self.editing else "New position"))
        self.show_capture()
        self.update_save_enabled()
        self.set_note("")
        self.name.setFocus()

    def show_capture(self):
        point = self.draft or self.points().get(self.editing, {})
        self.details.setText(self.location_text(point) if point else "")
        self.details.setVisible(bool(point))
        target = self.window.controller.config["windows"].get(point.get("window_id"), {})
        path = point.get("window", {}).get("path")
        caption = target.get("name") or (tr(application_name(path)) if path else "")
        self.window_info.setText(caption)
        self.window_info.setVisible(bool(caption))
        self.show_preview(self.draft_preview, point)

    def set_note(self, message):
        self.note.setText(message)
        self.note.setVisible(bool(message))

    def update_save_enabled(self, *_):
        current = self.points().get(self.editing, {})
        busy = self.capturing or self.testing
        self.capture.setText(tr("Capture again" if self.draft is not None else "Capture in 3 seconds"))
        capture_style = "" if self.draft is not None or self.editing else "primary"
        if self.capture.objectName() != capture_style:
            self.capture.setObjectName(capture_style)
            self.capture.style().unpolish(self.capture)
            self.capture.style().polish(self.capture)
        changed = self.draft is not None or (self.editing is not None and self.name.text().strip() != current.get("name"))
        self.save_name.setEnabled(not busy and bool(self.name.text().strip()) and changed)
        self.capture.setEnabled(not busy and bool(self.name.text().strip()))

    def edit_selected(self):
        if self.capturing or self.testing or not self.current_id():
            return
        self.editing = self.current_id()
        self.draft = None
        self.name.setText(self.points()[self.editing]["name"])
        self.open_editor()

    def finish(self):
        self.editing = None
        self.draft = None
        self.binding_field = None
        self.stack.setCurrentIndex(0)
        self.set_note("")
        self.selection()

    def cancel(self):
        origin = self.binding_field
        self.finish()
        if origin is not None:
            show_page(self.window,PAGE_BUTTONS)
            self.window.editor.edit_action(origin)

    def clean_name(self):
        name = self.name.text().strip()
        if not name:
            raise ValueError("Enter a name for the position.")
        if any(p["name"].casefold() == name.casefold() for key,p in self.points().items() if key != self.editing):
            raise ValueError("This name is already in use.")
        return name

    def persist(self, config, ident=None):
        self.window.controller.save(config)
        self.window.load_bindings()
        self.reload(ident)

    def commit_name(self):
        if self.stack.currentWidget() is not self.edit or self.capturing or self.testing:
            return
        try:
            name = self.clean_name()
            config = copy.deepcopy(self.window.controller.config)
            ident = self.editing
            captured_window = self.captured_window if self.draft is not None else None
            if self.draft is not None:
                ident = ident or str(uuid.uuid4())
                config["positions"][ident] = copy.deepcopy(self.draft)
                config["positions"][ident]["name"] = name
                if captured_window:
                    window_id = self.link_window(config, captured_window)
                    config["positions"][ident]["window_id"] = window_id
            elif ident:
                config["positions"][ident]["name"] = name
            else:
                return
            origin = self.binding_field
            self.persist(config,ident)
            if captured_window:
                self.window.controller.windows.select(window_id, captured_window)
            self.finish()
            if origin is not None:
                show_page(self.window,PAGE_BUTTONS)
                self.window.editor.edit_action(origin)
                self.window.editor.select_position(ident)
        except (OSError,ValueError) as error:
            self.set_note(str(error))

    async def capture_point(self):
        if self.capturing or self.testing:
            return
        try:
            name = self.clean_name()
        except ValueError as error:
            self.set_note(str(error))
            return
        self.capturing = True
        self.selection()
        self.window.controller.router.reset()
        self.window.controller.input_suspended = True
        self.window.hide()
        try:
            await self.countdown("Capturing position")
            await asyncio.sleep(.08)  # Let Windows remove the countdown from the captured frame.
            self.draft = await asyncio.to_thread(mouse_controls.capture,name)
            self.capture_context()
            self.show_capture()
            self.set_note("Position captured. Save to confirm.")
        except (OSError,RuntimeError,ValueError) as error:
            self.set_note(str(error))
        finally:
            self.window.controller.router.reset()
            self.window.controller.input_suspended = False
            self.capturing = False
            if not self.window.closing:
                self.window.show()
                self.window.raise_()
                self.window.activateWindow()
            self.selection()

    def capture_context(self):
        self.captured_window = None
        try:
            physical = mouse_controls.resolve(self.draft)
        except (OSError, RuntimeError):
            return
        try:
            self.captured_window = self.window.controller.windows.native.window_at(physical)
        except (OSError, RuntimeError):
            pass
        if self.captured_window:
            self.draft["window"] = self.captured_window.identity()
        preview = capture_preview(self.draft, physical)
        if preview:
            self.draft["preview"] = preview

    def link_window(self, config, window):
        service = self.window.controller.windows
        try:
            live = service.native.list()
        except (RuntimeError, OSError):
            live = []
        tabs, whole = [], []
        for ident, target in config["windows"].items():
            if target["path"].casefold() != window.path.casefold():
                continue
            try:
                if service.target(ident, config, live).handle != window.handle:
                    continue
            except RuntimeError:
                continue
            match = target.get("tab_match")
            if not match:
                whole.append(ident)
            elif match.casefold() in window.title.casefold():
                tabs.append(ident)
        if len(tabs) == 1:
            return tabs[0]
        if whole:
            return whole[0]
        ident = str(uuid.uuid4())
        name = application_name(window.path)
        config["windows"][ident] = dict(window.identity(), name=name)
        return ident

    async def countdown(self, title):
        overlay = CountdownOverlay(title)
        self.countdown_overlay = overlay
        try:
            overlay.show()
            for remaining in (3,2,1):
                overlay.set_remaining(remaining)
                await asyncio.sleep(1)
        finally:
            overlay.close()
            overlay.deleteLater()
            self.countdown_overlay = None

    async def test_point(self):
        if self.testing or self.capturing:
            return
        ident = self.current_id()
        if not ident:
            return
        point = copy.deepcopy(self.points()[ident])
        stop = threading.Event()
        self.testing = True
        self.selection()
        self.window.hide()
        try:
            await self.countdown("Testing position")
            await asyncio.to_thread(mouse_controls.click,point,stop)
            self.set_note("Click sent.")
        except (RuntimeError,OSError) as error:
            self.set_note(str(error))
        finally:
            stop.set()
            self.testing = False
            if not self.window.closing:
                self.window.show()
                self.window.raise_()
                self.window.activateWindow()
            self.selection()

    def remove(self):
        ident = self.current_id()
        if not ident:
            return
        uses = []
        for key,mapping in self.window.controller.config["buttons"].items():
            for gesture,binding in mapping.items():
                if isinstance(binding,dict) and binding.get("position_id") == ident:
                    uses.append(f"{'+' if key == 'plus' else key.upper()} · " +
                                {"short":"Simple","double":"Double","long":"Long","hold":"Continuous hold"}[gesture])
        routines = [routine["name"] for routine in self.window.controller.config["routines"].values()
                    if routine_references(routine,self.window.controller.config,position_id=ident)]
        uses.extend(routines)
        text = f"Delete “{self.points()[ident]['name']}”?"
        if routines:
            text += "\n" + tr("Routines using this position will need a new target.")
        if uses:
            text += "\nThese assignments will be set to None.\n" + "\n".join(uses)
        if not confirm_dialog(self,"Delete position",text,accept="Delete"):
            return
        config = copy.deepcopy(self.window.controller.config)
        del config["positions"][ident]
        for routine in config["routines"].values():
            for step in routine["steps"]:
                if step.get("position_id") == ident:
                    step["position_id"] = None
        for mapping in config["buttons"].values():
            for kind,binding in mapping.items():
                if isinstance(binding,dict) and binding.get("position_id") == ident:
                    mapping[kind] = "none"
        try:
            self.persist(config)
            self.cancel()
        except (OSError,ValueError) as error:
            self.set_note(str(error))
