"""Named screen positions, edited inside the page without a capture overlay."""
import asyncio
import copy
import uuid
import threading

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QStackedWidget

import mouse_controls
from desktop_ui import card, label, push, make_page, show_page, PAGE_BUTTONS
from ui_controls import SelectionList, CountdownOverlay, confirm_dialog
from i18n import tr
from settings import routine_references
from ui_icons import icon
from PySide6.QtCore import QSize


class MousePage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.capturing = False
        self.testing = False
        self.editing = None
        self.mode = None
        self.draft = None
        self.binding_field = None
        self.countdown_overlay = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.add = push("Add a position",self.new,True)
        page, body = make_page("Mouse positions",action=self.add)
        body.setSpacing(16)
        layout.addWidget(page)
        body.addWidget(label("Save a screen point without clicking. Use it directly on a button, or in a routine that activates its window first.","muted"))
        self.columns_surface = QWidget()
        columns = QHBoxLayout(self.columns_surface)
        columns.setContentsMargins(0,0,0,0)
        columns.setSpacing(16)
        self.columns_surface.setMaximumHeight(340)
        body.addWidget(self.columns_surface)
        body.addStretch()
        sidebar, sidebar_box = card()
        sidebar.setMinimumWidth(180)
        sidebar.setMaximumWidth(240)
        sidebar_box.setContentsMargins(12,12,12,12)
        columns.addWidget(sidebar,1)
        self.list = SelectionList()
        self.list.setIconSize(QSize(26,26))
        self.list.setObjectName("positions")
        self.list.currentRowChanged.connect(self.selection)
        self.position_pages = QStackedWidget()
        self.empty = QWidget()
        empty_box = QVBoxLayout(self.empty)
        empty_box.setContentsMargins(24,20,24,20)
        empty_box.addStretch()
        empty_title = label("No saved positions", "muted")
        empty_title.setMinimumHeight(50)
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_box.addWidget(empty_title)
        empty_box.addStretch()
        self.position_pages.addWidget(self.empty)
        self.position_pages.addWidget(self.list)
        sidebar_box.addWidget(self.position_pages,1)
        self.detail_surface, box = card()
        self.detail_surface.setMinimumWidth(360)
        box.setContentsMargins(20,20,20,20)
        columns.addWidget(self.detail_surface,2)
        self.detail_pages = QStackedWidget()
        box.addWidget(self.detail_pages,1)
        self.no_selection = label("Add a position", "muted")
        self.no_selection.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_pages.addWidget(self.no_selection)
        self.summary = QWidget()
        summary_box = QVBoxLayout(self.summary)
        summary_box.setContentsMargins(0,0,0,0)
        summary_box.setSpacing(12)
        self.summary_title = label("",size=18)
        self.summary_title.setProperty("i18nUserText", True)
        summary_box.addWidget(self.summary_title)
        self.summary_details = label("","muted")
        from ui_icons import badge
        summary_box.insertWidget(0,badge("position"))
        summary_box.addWidget(self.summary_details)
        self.rename = push("Rename",self.begin_rename)
        summary_box.addWidget(self.rename,alignment=Qt.AlignmentFlag.AlignLeft)
        summary_box.addSpacing(8)
        self.detail_pages.addWidget(self.summary)
        self.edit = QWidget()
        editor = QVBoxLayout(self.edit)
        editor.setContentsMargins(0,0,0,0)
        editor.setSpacing(10)
        self.editor_title = label("Position",size=18)
        editor.addWidget(self.editor_title)
        editor.addSpacing(8)
        editor.addWidget(label("Name", "muted"))
        self.name = QLineEdit()
        self.name.setMaxLength(60)
        self.name.setMinimumHeight(34)
        self.name.setPlaceholderText("Position name")
        self.name.setAccessibleName("Position name")
        editor.addWidget(self.name)
        self.details = label("","muted")
        editor.addWidget(self.details)
        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.capture = push("Capture position",lambda: window.launch(self.capture_point()),True)
        self.capture.setToolTip("Swift Click hides for 3 seconds. Move the pointer to the target; no click is sent.")
        self.save_name = push("Save",self.commit_name,True)
        self.cancel_button = push("Cancel",self.cancel)
        controls.addWidget(self.capture)
        controls.addWidget(self.save_name)
        controls.addStretch()
        controls.addWidget(self.cancel_button)
        editor.addLayout(controls)
        editor.addStretch()
        self.actions = QWidget()
        row = QHBoxLayout(self.actions)
        row.setContentsMargins(0,0,0,0)
        self.reposition = push("Reposition",self.begin_reposition)
        self.reposition.setToolTip("Capture the point again after moving the window or changing display resolution or scaling.")
        self.test = push("Test",lambda: window.launch(self.test_point()))
        self.delete = push("Delete",self.remove)
        for button in (self.reposition,self.test,self.delete):
            row.addWidget(button)
        summary_box.addWidget(self.actions)
        self.note = label("","muted")
        box.addWidget(self.note)
        self.detail_pages.addWidget(self.edit)
        self.name.textChanged.connect(self.update_save_enabled)
        self.reload()

    def points(self):
        return self.window.controller.config["positions"]

    def current_id(self):
        item = self.list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def reload(self, selected=None):
        selected = selected or self.current_id()
        self.list.blockSignals(True)
        self.list.clear()
        for ident,point in self.points().items():
            self.list.addItem(point["name"])
            item = self.list.item(self.list.count()-1)
            item.setIcon(icon("position"))
            item.setData(Qt.ItemDataRole.UserRole,ident)
            if ident == selected:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        if self.list.count() and self.list.currentRow() < 0:
            self.list.setCurrentRow(0)
        self.position_pages.setCurrentWidget(self.list if self.list.count() else self.empty)
        self.selection(force=True)

    def selection(self, *_, force=False):
        ident = self.current_id()
        busy = self.capturing or self.testing
        self.add.setEnabled(not busy)
        self.list.setEnabled(not busy)
        self.name.setEnabled(not busy)
        self.cancel_button.setEnabled(not busy)
        for button in (self.rename,self.reposition,self.test,self.delete):
            button.setEnabled(bool(ident) and not self.capturing and not self.testing)
        if busy:
            self.save_name.setEnabled(False)
            self.capture.setEnabled(False)
            return
        if not force and self.mode in ("new", "capture", "rename") and not _:
            self.update_save_enabled()
            return
        self.mode = None
        self.editing = None
        self.draft = None
        self.binding_field = None
        if not ident:
            self.detail_pages.setCurrentWidget(self.no_selection)
            self.mode = None
            self.editing = None
            return
        point = self.points()[ident]
        valid = mouse_controls.is_valid(point)
        self.test.setEnabled(valid and not self.capturing and not self.testing)
        screen = point["screen"]
        state = "" if valid else " · Position needs updating"
        screen_name = "Display " + screen["device"].split("DISPLAY")[-1]
        self.details.setText(f"{screen_name} · {point['x']}, {point['y']} px{state}")
        self.summary_title.setText(point["name"])
        self.summary_details.setText(self.details.text())
        self.detail_pages.setCurrentWidget(self.summary)

    def new(self, _checked=False, *, binding_field=None):
        if self.capturing or self.testing:
            return
        self.editing = None
        self.draft = None
        self.binding_field = binding_field
        self.name.clear()
        self.open_editor(rename=False)

    def open_editor(self, rename=False, *, focus=True):
        self.mode = "rename" if rename else "capture" if self.editing else "new"
        self.detail_pages.setCurrentWidget(self.edit)
        self.editor_title.setText("New position" if self.mode == "new" else "Position")
        self.details.setVisible(bool(self.editing))
        self.update_save_enabled()
        if focus:
            self.note.clear()
            self.name.setFocus()

    def update_save_enabled(self, *_):
        current = self.points().get(self.editing, {})
        busy = self.capturing or self.testing
        self.save_name.setVisible(self.mode == "rename" or self.draft is not None)
        self.capture.setVisible(self.mode in ("new", "capture"))
        self.capture.setText("Capture again" if self.draft is not None else "Capture position")
        capture_style = "" if self.draft is not None else "primary"
        if self.capture.objectName() != capture_style:
            self.capture.setObjectName(capture_style)
            self.capture.style().unpolish(self.capture)
            self.capture.style().polish(self.capture)
        changed = self.draft is not None or (self.mode == "rename" and self.name.text().strip() != current.get("name"))
        self.save_name.setEnabled(not busy and bool(self.name.text().strip()) and changed)
        self.capture.setEnabled(not busy and bool(self.name.text().strip()))

    def begin_rename(self):
        self.editing = self.current_id()
        if not self.editing:
            return
        self.draft = None
        self.name.setText(self.points()[self.editing]["name"])
        self.open_editor(rename=True)

    def begin_reposition(self):
        self.editing = self.current_id()
        if not self.editing:
            return
        self.draft = None
        self.name.setText(self.points()[self.editing]["name"])
        self.open_editor()

    def cancel(self):
        origin = self.binding_field
        self.mode = None
        self.editing = None
        self.draft = None
        self.binding_field = None
        self.note.clear()
        self.selection(force=True)
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
        if self.mode is None or self.capturing or self.testing:
            return
        try:
            name = self.clean_name()
            config = copy.deepcopy(self.window.controller.config)
            ident = self.editing
            if self.draft is not None:
                ident = ident or str(uuid.uuid4())
                config["positions"][ident] = copy.deepcopy(self.draft)
                config["positions"][ident]["name"] = name
            elif self.mode == "rename" and ident:
                config["positions"][ident]["name"] = name
            else:
                return
            origin = self.binding_field
            self.persist(config,ident)
            self.note.setText("Position saved.")
            if origin is not None:
                show_page(self.window,PAGE_BUTTONS)
                self.window.editor.edit_action(origin)
                self.window.editor.select_position(ident)
        except (OSError,ValueError) as error:
            self.note.setText(str(error))

    async def capture_point(self):
        if self.capturing or self.testing:
            return
        try:
            name = self.clean_name()
        except ValueError as error:
            self.note.setText(str(error))
            return
        self.capturing = True
        self.selection()
        self.window.controller.router.reset()
        self.window.controller.input_suspended = True
        self.window.hide()
        try:
            await self.countdown("Capturing position")
            self.draft = await asyncio.to_thread(mouse_controls.capture,name)
            screen = self.draft["screen"]["device"].split("DISPLAY")[-1]
            self.details.setText(f"Display {screen} · {self.draft['x']}, {self.draft['y']} px")
            self.details.show()
            self.note.setText("Position captured. Save to confirm.")
        except (OSError,RuntimeError,ValueError) as error:
            self.note.setText(str(error))
        finally:
            self.window.controller.router.reset()
            self.window.controller.input_suspended = False
            self.capturing = False
            if not self.window.closing:
                self.window.show()
                self.window.raise_()
                self.window.activateWindow()
            self.selection()

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
            self.note.setText("Click sent.")
        except (RuntimeError,OSError) as error:
            self.note.setText(str(error))
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
            self.note.setText(str(error))
