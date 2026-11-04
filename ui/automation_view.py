"""Guided window selection and routines; no scripting or arbitrary step editor."""
import copy
import threading
import uuid

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QButtonGroup, QStackedWidget
from desktop_ui import make_page, card, label, push
from ui_controls import SelectionList, ToggleSwitch, confirm_dialog
from i18n import tr, language
from ui_icons import icon, badge, application_icon


from window_view import WindowsPage


class RoutinesPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.owner = window
        self.ident = None
        self.rendered_language = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        page,box = make_page("Routines",action=push("New routine",self.new,True))
        layout.addWidget(page)
        surface,content = card()
        content.setContentsMargins(18,16,18,16)
        content.setSpacing(10)
        box.addWidget(surface,1)
        self.stack = QStackedWidget()
        content.addWidget(self.stack,1)
        overview = QWidget()
        overview_box = QVBoxLayout(overview)
        overview_box.setContentsMargins(0,0,0,0)
        self.stack.addWidget(overview)
        self.list = SelectionList()
        self.list.setIconSize(QSize(38,38))
        self.list.setStyleSheet("QListWidget {background:white;border:0;padding:0;} QListWidget::item {padding:14px;margin-bottom:7px;background:#f6f8f8;}")
        self.list.setAccessibleName("Saved routines")
        self.list.currentItemChanged.connect(self.selection)
        overview_box.addWidget(self.list,1)
        self.empty = QWidget()
        empty_box = QVBoxLayout(self.empty)
        empty_box.addStretch()
        empty_box.addWidget(badge("routine",56),alignment=Qt.AlignmentFlag.AlignCenter)
        empty_title = label("No saved routines","muted")
        empty_title.setMinimumSize(280,40)
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_box.addWidget(empty_title,alignment=Qt.AlignmentFlag.AlignCenter)
        empty_box.addStretch()
        overview_box.addWidget(self.empty,1)
        overview_controls = QHBoxLayout()
        self.edit_button = push("Edit",lambda:self.stack.setCurrentIndex(1))
        self.test = push("Test",lambda:window.launch(self.run()))
        self.delete = push("Delete",self.remove)
        for button in (self.edit_button,self.test,self.delete):
            overview_controls.addWidget(button)
        overview_controls.addStretch()
        overview_box.addLayout(overview_controls)
        self.form = QWidget()
        self.stack.addWidget(self.form)
        form = QVBoxLayout(self.form)
        form.setContentsMargins(8,0,8,0)
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
            button.setIcon(icon({"show":"window","video":"forward","mouse_position":"click"}[action]))
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
        self.points.setIconSize(QSize(22,22))
        self.points.setMaximumHeight(85)
        self.points.setAccessibleName("Saved mouse position")
        self.points.currentItemChanged.connect(lambda *_:self.update_controls())
        form.addWidget(self.points)
        self.no_points = label("No saved positions. Add one in Mouse positions.","muted")
        form.addWidget(self.no_points)
        self.return_previous = ToggleSwitch("Return to previous window")
        self.return_previous.toggled.connect(self.update_controls)
        form.addWidget(self.return_previous)
        self.hint = label("Target windows are selected on the Windows page.","muted")
        self.hint.setStyleSheet("font-size:12px")
        form.addWidget(self.hint)
        controls = QHBoxLayout()
        self.save = push("Save",self.persist,True)
        controls.addWidget(push("Cancel",self.finish))
        controls.addStretch()
        controls.addWidget(self.save)
        form.addLayout(controls)
        self.result = label("","muted")
        content.addWidget(self.result)
        form.addStretch()
        self.template = "show"
        self.new()
        self.stack.setCurrentIndex(0)

    def reload(self, selected=None):
        self.rendered_language = language()
        selected = selected or self.ident
        self.list.blockSignals(True)
        self.list.clear()
        for ident,routine in self.owner.controller.config["routines"].items():
            role = routine["target"]
            target = "MyWhoosh" if role == "mywhoosh" else "Video"
            action = {"show":"Show window","seek_back":"Seek backward","seek_forward":"Seek forward","mouse_position":"Click position"}[routine["action"]]
            summary = tr(target) + " · " + tr(action)
            if routine["return"]:
                summary += " · " + tr("Return")
            self.list.addItem(routine["name"] + "\n" + summary)
            item = self.list.item(self.list.count()-1)
            identity = self.owner.controller.config["windows"].get(role,{})
            item.setIcon(application_icon(identity["path"]) if identity else icon("routine"))
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
            item.setIcon(icon("position"))
            item.setData(Qt.ItemDataRole.UserRole,ident)
            if ident == point_id:
                self.points.setCurrentItem(item)
        self.points.blockSignals(False)
        for role,button in self.targets.items():
            identity = self.owner.controller.config["windows"].get(role)
            button.setIcon(application_icon(identity["path"]) if identity else icon("window"))
        self.list.setVisible(bool(self.list.count()))
        self.empty.setVisible(not self.list.count())
        if self.stack.currentIndex() == 0 and self.list.currentItem():
            self.selection(self.list.currentItem())
        self.update_controls()

    def finish(self):
        self.stack.setCurrentIndex(0)
        self.reload(self.ident)

    def new(self):
        self.ident = None
        self.list.setCurrentRow(-1)
        self.name.clear()
        self.targets["video"].setChecked(True)
        self.seek["seek_forward"].setChecked(True)
        self.return_previous.setChecked(True)
        self.set_template("show")
        self.stack.setCurrentIndex(1)

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
        self.points.setVisible(self.template == "mouse_position" and self.points.count() > 0)
        self.no_points.setVisible(self.template == "mouse_position" and self.points.count() == 0)
        self.save.setEnabled(valid)
        self.test.setEnabled(bool(self.ident) and self.draft() == self.owner.controller.config["routines"].get(self.ident))
        self.delete.setEnabled(bool(self.ident))
        self.edit_button.setEnabled(bool(self.ident))

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
            self.stack.setCurrentIndex(0)
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
            self.stack.setCurrentIndex(0)
            self.owner.load_bindings()
        except (ValueError,OSError) as exc:
            self.result.setText(str(exc))
