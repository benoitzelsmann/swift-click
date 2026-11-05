"""Reusable named windows, default targets and read-only automatic discovery."""
import asyncio
import copy
import uuid
from PySide6.QtCore import Qt,QSize
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QStackedWidget,QButtonGroup
from desktop_ui import card,label,push,make_page
from ui_controls import SelectionList,confirm_dialog
from ui_icons import icon,badge,application_icon
from i18n import tr,language
from settings import role_ref,routine_steps,routine_references


class WindowsPage(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.rendered_language = None
        self.available = []
        self.ident = None
        self.editing = None
        self.detecting = False
        self.opening = False
        self.detected_once = False
        self.role = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        toolbar = QWidget()
        tools = QHBoxLayout(toolbar)
        tools.setContentsMargins(0,0,0,0)
        self.detect_button = push("Detect",lambda:owner.launch(self.detect()))
        self.detect_button.setIcon(icon("detect"))
        tools.addWidget(self.detect_button)
        tools.addWidget(push("Add window",self.new,True))
        page,body = make_page("Windows",action=toolbar)
        layout.addWidget(page)
        surface,box = card()
        box.setContentsMargins(18,16,18,16)
        self.stack = QStackedWidget()
        box.addWidget(self.stack,1)
        body.addWidget(surface,1)
        catalogue = QWidget()
        content = QVBoxLayout(catalogue)
        content.setContentsMargins(0,0,0,0)
        self.defaults = label("","muted")
        self.defaults.setProperty("i18nUserText",True)
        content.addWidget(self.defaults)
        self.saved = SelectionList()
        self.saved.setIconSize(QSize(34,34))
        self.saved.setAccessibleName("Saved windows")
        self.saved.setStyleSheet("QListWidget {background:white;border:0;padding:0;} QListWidget::item {padding:12px;margin-bottom:5px;background:#f6f8f8;}")
        self.saved.currentItemChanged.connect(self.selection)
        content.addWidget(self.saved,1)
        self.empty = label("Add an open window or run detection.","muted")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setMinimumHeight(60)
        content.addWidget(self.empty,1)
        controls = QHBoxLayout()
        self.edit_button = push("Edit",self.edit)
        self.open_button = push("Open",lambda:owner.launch(self.open_selected()))
        self.delete_button = push("Delete",self.remove)
        for button in (self.edit_button,self.open_button,self.delete_button):
            controls.addWidget(button)
        controls.addStretch()
        content.addLayout(controls)
        self.stack.addWidget(catalogue)
        editor = QWidget()
        edit = QVBoxLayout(editor)
        edit.setContentsMargins(0,0,0,0)
        edit.setSpacing(10)
        self.name = QLineEdit()
        self.name.setPlaceholderText("Window name")
        self.name.setAccessibleName("Window name")
        self.name.setMaxLength(60)
        self.name.textChanged.connect(self.update_save)
        edit.addWidget(self.name)
        role_line = QHBoxLayout()
        role_line.addWidget(label("Default for","muted"))
        group = QButtonGroup(self)
        self.roles = {}
        for role,title in ((None,"Neither"),("mywhoosh","MyWhoosh"),("video","Media")):
            button = push(title,lambda _=False,r=role:setattr(self,"role",r))
            button.setCheckable(True)
            button.setObjectName("choice")
            group.addButton(button)
            self.roles[role] = button
            role_line.addWidget(button)
        edit.addLayout(role_line)
        heading = QHBoxLayout()
        heading.addWidget(label("Open windows","muted"),1)
        heading.addWidget(push("Refresh",self.populate))
        edit.addLayout(heading)
        self.list = SelectionList()
        self.list.setIconSize(QSize(30,30))
        self.list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setAccessibleName("Open windows")
        self.list.currentRowChanged.connect(self.chosen)
        edit.addWidget(self.list,1)
        buttons = QHBoxLayout()
        buttons.addWidget(push("Cancel",self.finish))
        buttons.addStretch()
        self.select_button = push("Save window",self.select,True)
        buttons.addWidget(self.select_button)
        edit.addLayout(buttons)
        self.stack.addWidget(editor)
        self.status = label("","muted")
        self.status.setProperty("i18nUserText",True)
        box.addWidget(self.status)
        self.result = label("","muted")
        box.addWidget(self.result)

    def reload(self, selected=None):
        self.rendered_language = language()
        selected = selected or self.ident
        cfg = self.owner.controller.config
        self.saved.blockSignals(True)
        self.saved.clear()
        try:
            live = self.owner.controller.windows.native.list()
        except (RuntimeError,OSError):
            live = []
        for ident,target in cfg["windows"].items():
            try:
                self.owner.controller.windows.target(ident,cfg,live)
                state = tr("Open")
            except RuntimeError:
                state = tr("Not open")
            self.saved.addItem(target["name"]+"\n"+state+" · "+target["title"])
            item = self.saved.item(self.saved.count()-1)
            item.setIcon(application_icon(target["path"]))
            item.setData(Qt.ItemDataRole.UserRole,ident)
            if ident == selected:
                self.saved.setCurrentItem(item)
        self.saved.blockSignals(False)
        self.empty.setVisible(not self.saved.count())
        self.saved.setVisible(bool(self.saved.count()))
        names = []
        for role,title in (("mywhoosh","MyWhoosh"),("video","Media")):
            target = cfg["windows"].get(role_ref(cfg,role))
            names.append(tr(title)+" · "+(target["name"] if target else tr("Not defined")))
        self.defaults.setText("     /     ".join(names))
        self.selection(self.saved.currentItem())
        if not self.detected_once and not self.detecting:
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return
            self.owner.launch(self.detect())

    def selection(self, item, _previous=None):
        self.ident = item.data(Qt.ItemDataRole.UserRole) if item else None
        for button in (self.edit_button,self.open_button,self.delete_button):
            button.setEnabled(bool(self.ident) and not self.opening)

    def new(self):
        self.editing = None
        self.name.clear()
        self.role = None
        self.roles[None].setChecked(True)
        self.populate()
        self.stack.setCurrentIndex(1)

    def edit(self):
        if not self.ident:
            return
        self.editing = self.ident
        target = self.owner.controller.config["windows"][self.ident]
        self.name.setText(target["name"])
        self.role = next((r for r in ("mywhoosh","video") if role_ref(self.owner.controller.config,r) == self.ident),None)
        self.roles[self.role].setChecked(True)
        self.populate()
        self.stack.setCurrentIndex(1)
        self.update_save()

    def choose_role(self, role):
        """Also used when jumping here to prepare a default target."""
        ident = role_ref(self.owner.controller.config,role)
        if ident in self.owner.controller.config["windows"]:
            self.ident = ident
            self.edit()
        else:
            self.new()
            self.role = role
            self.roles[role].setChecked(True)
            self.name.setText("MyWhoosh" if role == "mywhoosh" else tr("Media"))

    def populate(self):
        known = {win.handle:win for win in self.available}
        self.available = [known.get(win.handle,win) for win in self.owner.controller.windows.native.list()]
        self.list.clear()
        for window in self.available:
            self.list.addItem(window.title)
            self.list.item(self.list.count()-1).setIcon(application_icon(window.path))
        self.update_save()

    def chosen(self, index):
        if index >= 0 and not self.name.text().strip():
            self.name.setText(self.available[index].title[:60])
        self.update_save()

    def update_save(self, *_):
        self.select_button.setEnabled(bool(self.name.text().strip()) and (self.list.currentRow() >= 0 or self.editing is not None))

    def select(self):
        cfg = copy.deepcopy(self.owner.controller.config)
        ident = self.editing or (self.role if self.role and self.role not in cfg["windows"] else str(uuid.uuid4()))
        index = self.list.currentRow()
        target = copy.deepcopy(cfg["windows"].get(ident,{}))
        window = self.available[index] if index >= 0 else None
        if window:
            other_role = "video" if self.role == "mywhoosh" else "mywhoosh"
            other = cfg["windows"].get(role_ref(cfg,other_role)) if self.role else None
            if other and other["path"].casefold() == window.path.casefold() and other["title"] == window.title:
                self.result.setText("Choose two different windows")
                return
            target = dict(window.identity(),name=self.name.text().strip())
            if window.app_id:
                target["app_id"] = window.app_id
        else:
            target["name"] = self.name.text().strip()
        cfg["windows"][ident] = target
        for role,ref in list(cfg["window_roles"].items()):
            if ref == ident:
                cfg["window_roles"][role] = None
        if self.role:
            cfg["window_roles"][self.role] = ident
        try:
            self.owner.controller.save(cfg)
            if window:
                self.owner.controller.windows.select(ident,window)
            self.ident = ident
            self.finish()
        except (RuntimeError,ValueError,OSError) as exc:
            self.result.setText(str(exc))

    def finish(self):
        self.stack.setCurrentIndex(0)
        self.reload(self.ident)

    async def detect(self):
        if self.detecting:
            return
        self.detecting = True
        self.detected_once = True
        self.detect_button.setEnabled(False)
        self.detect_button.setText("Detecting…")
        try:
            from window_discovery import discover
            detected = await discover(self.owner.controller.windows.native)
            self.available = detected["windows"]
            cfg = copy.deepcopy(self.owner.controller.config)
            selected = []
            for role,key,title in (("mywhoosh","mywhoosh","MyWhoosh"),("video","media","Media")):
                matches = detected[key]
                if role_ref(cfg,role) in cfg["windows"] or len(matches) != 1:
                    continue
                win = next(win for win in self.available if win.handle == matches[0])
                ident = next((ref for ref,target in cfg["windows"].items() if target["path"] == win.path and target["title"] == win.title),role)
                if ident not in cfg["windows"]:
                    cfg["windows"][ident] = dict(win.identity(),name=title)
                    if win.app_id:
                        cfg["windows"][ident]["app_id"] = win.app_id
                cfg["window_roles"][role] = ident
                selected.append((ident,win))
            if selected:
                self.owner.controller.save(cfg)
                for ident,win in selected:
                    self.owner.controller.windows.select(ident,win)
            self.status.setText(tr("Detected: {game} MyWhoosh, {media} media windows").format(game=len(detected["mywhoosh"]),media=len(detected["media"]))+
                                (" · "+tr(detected["warning"]) if detected["warning"] else ""))
            self.reload()
        except (RuntimeError,OSError,ValueError) as exc:
            self.result.setText(str(exc))
        finally:
            self.detecting = False
            self.detect_button.setEnabled(True)
            self.detect_button.setText("Detect")

    async def open_selected(self):
        if self.opening or not self.ident:
            return
        cfg = copy.deepcopy(self.owner.controller.config)
        cfg["routines"]["preview"] = {"name":"Open","return":False,"steps":[{"action":"open","window_id":self.ident}]}
        self.opening = True
        self.selection(self.saved.currentItem())
        self.open_button.setText("Opening…")
        try:
            completed = await self.owner.controller.windows.run({"action":"routine","routine_id":"preview"},cfg)
            self.result.setText("Action completed" if completed else "Cancelled")
        except (RuntimeError,OSError) as exc:
            self.result.setText(str(exc))
        finally:
            self.opening = False
            self.open_button.setText("Open")
            self.reload(self.ident)

    def remove(self):
        if not self.ident:
            return
        cfg = copy.deepcopy(self.owner.controller.config)
        affected = [r["name"] for r in cfg["routines"].values() if routine_references(r,cfg,window_id=self.ident)]
        text = tr("Delete this window?")
        if affected:
            text += "\n"+tr("These routines will need a new target:")+"\n"+"\n".join(affected)
        if not confirm_dialog(self,"Delete window",text,accept="Delete"):
            return
        for routine in cfg["routines"].values():
            for step in routine["steps"]:
                for field in ("window_id","other_window_id"):
                    if step.get(field) == self.ident:
                        step[field] = None
        del cfg["windows"][self.ident]
        cfg["window_roles"] = {r:ref if ref != self.ident else None for r,ref in cfg["window_roles"].items()}
        self.owner.controller.windows.session.pop(self.ident,None)
        try:
            self.owner.controller.save(cfg)
            self.ident = None
            self.reload()
        except (ValueError,OSError) as exc:
            self.result.setText(str(exc))
