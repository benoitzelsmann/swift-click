"""Guided window selection and routines; no scripting or arbitrary step editor."""
import copy
import threading
import uuid

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QButtonGroup
from desktop_ui import make_page, card, label, push
from ui_controls import SelectionList, ToggleSwitch, confirm_dialog
from i18n import tr


def user_label(text=""):
    widget = label(text,"muted")
    widget.setProperty("i18nUserText",True)
    return widget


class WindowsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.owner = window
        self.role = "mywhoosh"
        self.available = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        page,box = make_page("Windows",action=push("Refresh",self.reload))
        layout.addWidget(page)
        surface,content = card()
        content.setContentsMargins(20,18,20,18)
        box.addWidget(surface,1)
        roles = QHBoxLayout()
        self.role_buttons = {}
        group = QButtonGroup(self)
        for role,title in (("mywhoosh","MyWhoosh"),("video","Video")):
            button = push(title,lambda _=False,r=role:self.choose_role(r))
            button.setCheckable(True)
            group.addButton(button)
            roles.addWidget(button)
            self.role_buttons[role] = button
        content.addLayout(roles)
        self.summary = user_label()
        self.summary.setAccessibleName("Selected window")
        content.addWidget(self.summary)
        self.list = SelectionList()
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.list.setAccessibleName("Open windows")
        self.list.currentItemChanged.connect(lambda *_:self.select_button.setEnabled(self.list.currentRow() >= 0))
        content.addWidget(self.list,1)
        controls = QHBoxLayout()
        self.select_button = push("Use selected window",self.select,True)
        self.select_button.setEnabled(False)
        controls.addWidget(self.select_button)
        controls.addWidget(push("Switch windows",lambda:window.launch(self.test())))
        content.addLayout(controls)
        content.addWidget(label("Keep keyboard focus on the video player inside the selected browser window.","muted"))
        self.result = label("","muted")
        content.addWidget(self.result)
        self.role_buttons[self.role].setChecked(True)

    def choose_role(self, role):
        self.role = role
        self.role_buttons[role].setChecked(True)
        self.update_summary()

    def update_summary(self):
        identity = self.owner.controller.config["windows"].get(self.role)
        title = identity["title"] if identity else tr("No window selected")
        if identity:
            try:
                self.owner.controller.windows.target(self.role,self.owner.controller.config)
            except RuntimeError:
                title += " · " + tr("Select again")
        self.summary.setText(title)

    def reload(self):
        try:
            self.available = self.owner.controller.windows.native.list()
            self.list.clear()
            for win in self.available:
                self.list.addItem(win.title)
            self.select_button.setEnabled(False)
            self.update_summary()
        except (RuntimeError,OSError) as exc:
            self.result.setText(str(exc))

    def select(self):
        index = self.list.currentRow()
        if index < 0:
            return
        window = self.available[index]
        config = copy.deepcopy(self.owner.controller.config)
        config["windows"][self.role] = window.identity()
        try:
            self.owner.controller.save(config)
            self.owner.controller.windows.select(self.role,window)
            self.update_summary()
        except (RuntimeError,OSError,ValueError) as exc:
            self.result.setText(str(exc))

    async def test(self):
        await self.owner.controller.windows.run("switch_windows",copy.deepcopy(self.owner.controller.config))


class RoutinesPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.owner = window
        self.ident = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        page,box = make_page("Routines",action=push("New routine",self.new,True))
        layout.addWidget(page)
        surface,content = card()
        content.setContentsMargins(18,16,18,16)
        content.setSpacing(10)
        box.addWidget(surface,1)
        columns = QHBoxLayout()
        self.list = SelectionList()
        self.list.setMaximumWidth(190)
        self.list.setAccessibleName("Saved routines")
        self.list.currentItemChanged.connect(self.selection)
        columns.addWidget(self.list,1)
        self.form = QWidget()
        form = QVBoxLayout(self.form)
        form.setContentsMargins(12,0,0,0)
        form.setSpacing(9)
        self.name = QLineEdit()
        self.name.setMaxLength(60)
        self.name.setPlaceholderText("Routine name")
        self.name.setAccessibleName("Routine name")
        self.name.textChanged.connect(self.update_controls)
        form.addWidget(self.name)
        self.templates = {}
        group = QButtonGroup(self)
        template_row = QHBoxLayout()
        for action,title in (("show","Show window"),("video","Seek video"),("mouse_position","Click position")):
            button = push(title,lambda _=False,a=action:self.set_template(a))
            button.setCheckable(True)
            button.setObjectName("choice")
            group.addButton(button)
            template_row.addWidget(button)
            self.templates[action] = button
        form.addLayout(template_row)
        target_row = QHBoxLayout()
        self.targets = {}
        target_group = QButtonGroup(self)
        for role,title in (("mywhoosh","MyWhoosh"),("video","Video")):
            button = push(title,lambda _=False:self.update_controls())
            button.setCheckable(True)
            target_group.addButton(button)
            target_row.addWidget(button)
            self.targets[role] = button
        form.addLayout(target_row)
        self.video_options = QWidget()
        row = QHBoxLayout(self.video_options)
        row.setContentsMargins(0,0,0,0)
        self.seek = {}
        seeks = QButtonGroup(self)
        for action,title in (("seek_back","Seek backward"),("seek_forward","Seek forward")):
            button = push(title,lambda:self.update_controls())
            button.setCheckable(True)
            seeks.addButton(button)
            row.addWidget(button)
            self.seek[action] = button
        form.addWidget(self.video_options)
        self.points = SelectionList()
        self.points.setMaximumHeight(85)
        self.points.setAccessibleName("Saved mouse position")
        self.points.currentItemChanged.connect(lambda *_:self.update_controls())
        form.addWidget(self.points)
        self.return_previous = ToggleSwitch("Return to previous window")
        self.return_previous.toggled.connect(self.update_controls)
        form.addWidget(self.return_previous)
        self.hint = label("Target windows are selected on the Windows page.","muted")
        self.hint.setStyleSheet("font-size:12px")
        form.addWidget(self.hint)
        controls = QHBoxLayout()
        self.save = push("Save",self.persist,True)
        self.test = push("Test",lambda:window.launch(self.run()))
        self.delete = push("Delete",self.remove)
        for button in (self.save,self.test,self.delete):
            controls.addWidget(button)
        form.addLayout(controls)
        self.result = label("","muted")
        form.addWidget(self.result)
        form.addStretch()
        columns.addWidget(self.form,3)
        content.addLayout(columns,1)
        self.template = "show"
        self.new()

    def reload(self, selected=None):
        selected = selected or self.ident
        self.list.blockSignals(True)
        self.list.clear()
        for ident,routine in self.owner.controller.config["routines"].items():
            self.list.addItem(routine["name"])
            item = self.list.item(self.list.count()-1)
            item.setData(Qt.ItemDataRole.UserRole,ident)
            if ident == selected:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        # Reloading points keeps the selected stable identifier.
        current = self.points.currentItem()
        point_id = current.data(Qt.ItemDataRole.UserRole) if current else None
        self.points.blockSignals(True)
        self.points.clear()
        for ident,point in self.owner.controller.config["positions"].items():
            self.points.addItem(point["name"])
            item = self.points.item(self.points.count()-1)
            item.setData(Qt.ItemDataRole.UserRole,ident)
            if ident == point_id:
                self.points.setCurrentItem(item)
        self.points.blockSignals(False)
        self.update_controls()

    def new(self):
        self.ident = None
        self.list.setCurrentRow(-1)
        self.name.clear()
        self.targets["video"].setChecked(True)
        self.seek["seek_forward"].setChecked(True)
        self.return_previous.setChecked(True)
        self.set_template("show")

    def selection(self, item, _previous=None):
        if item is None:
            return
        self.ident = item.data(Qt.ItemDataRole.UserRole)
        routine = self.owner.controller.config["routines"][self.ident]
        self.name.setText(routine["name"])
        self.targets[routine["target"]].setChecked(True)
        self.return_previous.setChecked(routine["return"])
        if routine["action"].startswith("seek_"):
            self.seek[routine["action"]].setChecked(True)
        self.set_template("video" if routine["action"].startswith("seek_") else routine["action"])
        for row in range(self.points.count()):
            if self.points.item(row).data(Qt.ItemDataRole.UserRole) == routine["position_id"]:
                self.points.setCurrentRow(row)
        self.update_controls()

    def set_template(self, template):
        self.template = template
        self.templates[template].setChecked(True)
        if template == "video":
            self.targets["video"].setChecked(True)
        self.targets["mywhoosh"].setEnabled(template != "video")
        self.video_options.setVisible(template == "video")
        self.points.setVisible(template == "mouse_position")
        self.update_controls()

    def update_controls(self):
        if not hasattr(self,"save") or not hasattr(self,"template"):
            return
        valid = bool(self.name.text().strip()) and (self.template != "mouse_position" or self.points.currentItem() is not None)
        self.save.setEnabled(valid)
        self.test.setEnabled(bool(self.ident) and self.draft() == self.owner.controller.config["routines"].get(self.ident))
        self.delete.setEnabled(bool(self.ident))

    def draft(self):
        action = next((a for a,b in self.seek.items() if b.isChecked()),"seek_forward") if self.template == "video" else self.template
        target = next((r for r,b in self.targets.items() if b.isChecked()),"video")
        return {"name":self.name.text().strip(),"target":target,"action":action,
            "return":self.return_previous.isChecked(),"position_id":self.points.currentItem().data(Qt.ItemDataRole.UserRole) if action == "mouse_position" and self.points.currentItem() else None}

    def persist(self):
        config = copy.deepcopy(self.owner.controller.config)
        ident = self.ident or str(uuid.uuid4())
        config["routines"][ident] = self.draft()
        try:
            self.owner.controller.save(config)
            self.ident = ident
            self.reload(ident)
            self.owner.load_bindings()
            self.result.setText("Saved")
        except (ValueError,OSError) as exc:
            self.result.setText(str(exc))

    async def run(self):
        try:
            await self.owner.controller.windows.run({"action":"routine","routine_id":self.ident},copy.deepcopy(self.owner.controller.config),threading.Event())
            self.result.setText("Action completed")
        except (RuntimeError,OSError) as exc:
            self.result.setText(str(exc))

    def remove(self):
        if not self.ident:
            return
        config = copy.deepcopy(self.owner.controller.config)
        uses = [key.upper()+" · "+kind for key,mapping in config["buttons"].items() for kind,binding in mapping.items()
                if isinstance(binding,dict) and binding.get("routine_id") == self.ident]
        text = tr("Delete this routine? Its assignments will become None.") + ("\n"+", ".join(uses) if uses else "")
        if not confirm_dialog(self,"Delete routine",text,accept="Delete"):
            return
        del config["routines"][self.ident]
        for mapping in config["buttons"].values():
            for kind,binding in mapping.items():
                if isinstance(binding,dict) and binding.get("routine_id") == self.ident:
                    mapping[kind] = "none"
        try:
            self.owner.controller.save(config)
            self.new()
            self.reload()
            self.owner.load_bindings()
        except (ValueError,OSError) as exc:
            self.result.setText(str(exc))
