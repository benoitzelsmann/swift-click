"""Reusable named windows, default targets and read-only automatic discovery."""
import asyncio
import copy
import re
import time
import uuid
from collections import Counter
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QStackedWidget,QButtonGroup
from desktop_ui import card,label,push,make_page
from ui_controls import CatalogList,confirm_dialog
from ui_icons import icon,application_icon,application_name
from i18n import tr,language
from settings import role_ref,routine_steps,routine_references
from browser_tabs import list_tabs, matching_tabs, supported


def tab_site(title):
    return next((site for site in ("YouTube", "Netflix", "Deezer", "Spotify", "Twitch")
                 if site.casefold() in title.casefold()), "")


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
        self.tab_cache = {}
        self.tab_requests = set()
        self.tab_slots = asyncio.Semaphore(3)
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
        box.setContentsMargins(16,12,16,12)
        self.stack = QStackedWidget()
        box.addWidget(self.stack,1)
        body.addWidget(surface,1)
        catalogue = QWidget()
        content = QVBoxLayout(catalogue)
        content.setContentsMargins(0,0,0,0)
        self.saved = CatalogList()
        self.saved.setAccessibleName("Saved windows")
        self.saved.currentItemChanged.connect(self.selection)
        self.saved.itemDoubleClicked.connect(self.edit_item)
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
        columns = QHBoxLayout()
        columns.setSpacing(14)
        open_windows = QVBoxLayout()
        heading = QHBoxLayout()
        heading.addWidget(label("Open windows",size=16),1)
        heading.addWidget(push("Refresh",self.refresh_choices))
        open_windows.addLayout(heading)
        self.list = CatalogList()
        self.list.setAccessibleName("Open windows")
        self.list.currentRowChanged.connect(self.chosen)
        self.list.itemClicked.connect(lambda _: self.show_tabs())
        open_windows.addWidget(self.list,1)
        columns.addLayout(open_windows,1)
        self.tab_panel = QWidget()
        tabs = QVBoxLayout(self.tab_panel)
        tabs.setContentsMargins(0,0,0,0)
        tab_heading = label("Browser tabs",size=16)
        tab_heading.setMinimumHeight(36)
        tabs.addWidget(tab_heading)
        self.tab_choices = CatalogList()
        self.tab_choices.setAccessibleName("Browser tabs")
        self.tab_choices.itemClicked.connect(self.chosen_tab)
        self.tab_choices.itemActivated.connect(self.chosen_tab)
        tabs.addWidget(self.tab_choices,1)
        self.tab_status = label("","muted")
        self.tab_status.setProperty("i18nUserText",True)
        tabs.addWidget(self.tab_status)
        self.tab_match = QLineEdit()
        self.tab_match.setPlaceholderText("Tab title contains")
        self.tab_match.setAccessibleName("Tab title contains")
        self.tab_match.setMaxLength(300)
        self.tab_match.textChanged.connect(self.sync_tab_selection)
        tabs.addWidget(self.tab_match)
        columns.addWidget(self.tab_panel,1)
        edit.addLayout(columns,1)
        self.tab_panel.hide()
        buttons = QHBoxLayout()
        buttons.addWidget(push("Cancel",self.finish))
        buttons.addStretch()
        self.select_button = push("Save window",self.select,True)
        buttons.addWidget(self.select_button)
        edit.addLayout(buttons)
        self.stack.addWidget(editor)
        self.status = label("","muted")
        self.status.setProperty("i18nUserText",True)
        self.status.hide()
        box.addWidget(self.status)
        self.result = label("","muted")
        self.result.hide()
        box.addWidget(self.result)

    def set_result(self, message):
        self.result.setText(tr(message))
        self.result.setVisible(bool(message))

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
        self.live = live
        for ident,target in cfg["windows"].items():
            try:
                self.owner.controller.windows.target(ident,cfg,live)
                state = tr("Available")
            except RuntimeError:
                state = tr("Not open")
            roles = [tr(title) for role,title in (("mywhoosh","MyWhoosh"),("video","Media")) if role_ref(cfg,role) == ident]
            detail = " · ".join([*roles,state])
            match = target.get("tab_match")
            if match:
                detail += " · " + tr("Tab") + " · " + (tab_site(match) or match[:48])
            name = target["name"]
            if len(name) > 32 and name == target["title"][:60].strip() and not match:
                name = tr(application_name(target["path"]))
            self.saved.addItem(name+"\n"+detail)
            item = self.saved.item(self.saved.count()-1)
            item.setIcon(application_icon(target["path"]))
            item.setData(Qt.ItemDataRole.UserRole,ident)
            if ident == selected:
                self.saved.setCurrentItem(item)
        self.saved.blockSignals(False)
        self.empty.setVisible(not self.saved.count())
        self.saved.setVisible(bool(self.saved.count()))
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
            button.setVisible(bool(self.owner.controller.config["windows"]))

    def showEvent(self, event):
        super().showEvent(event)
        self.preload_tabs(getattr(self, "live", []))

    def edit_item(self, item):
        self.selection(item)
        self.edit()

    def new(self):
        self.editing = None
        self.name.clear()
        self.set_result("")
        self.role = None
        self.tab_match.clear()
        self.roles[None].setChecked(True)
        self.populate()
        self.stack.setCurrentIndex(1)
        self.show_tabs()

    def edit(self):
        if not self.ident or self.opening:
            return
        self.editing = self.ident
        self.set_result("")
        target = self.owner.controller.config["windows"][self.ident]
        self.name.setText(target["name"])
        self.role = next((r for r in ("mywhoosh","video") if role_ref(self.owner.controller.config,r) == self.ident),None)
        self.roles[self.role].setChecked(True)
        self.populate()
        try:
            window = self.owner.controller.windows.target(self.editing, self.owner.controller.config, self.available)
            self.list.setCurrentRow(self.available.index(window))
        except RuntimeError:
            pass
        self.tab_match.setText(target.get('tab_match',''))
        self.stack.setCurrentIndex(1)
        self.show_tabs()
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
        self.available = self.owner.controller.windows.native.list()
        self.list.clear()
        names = [tr(application_name(window.path)) for window in self.available]
        totals = Counter(names)
        sequence = Counter()
        for window, name in zip(self.available, names):
            sequence[name] += 1
            self.list.addItem(f"{name} {sequence[name]}" if totals[name] > 1 else name)
            item = self.list.item(self.list.count()-1)
            item.setIcon(application_icon(window.path))
            item.setData(Qt.ItemDataRole.AccessibleDescriptionRole, window.title)
            if totals[name] > 1:
                item.setToolTip(window.title)
        self.preload_tabs(self.available)
        self.update_save()

    def refresh_choices(self):
        index = self.list.currentRow()
        window = self.available[index] if index >= 0 else None
        match = self.tab_match.text()
        self.tab_cache.clear()
        self.populate()
        if window is None:
            self.tab_match.setText(match)
        else:
            for index, candidate in enumerate(self.available):
                if candidate.handle == window.handle and candidate.path == window.path:
                    self.list.setCurrentRow(index)
                    self.tab_match.setText(match)
                    break
        self.show_tabs()

    def chosen(self, index):
        if index >= 0:
            self.tab_match.clear()
            if not self.name.text().strip() or (not self.editing and not self.name.isModified() and not self.role):
                self.name.setText(self.list.item(index).text())
        self.show_tabs()
        self.update_save()

    def preload_tabs(self, windows):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return
        now = time.monotonic()
        for key, entry in list(self.tab_cache.items()):
            if entry[0] <= now:
                del self.tab_cache[key]
        for window in windows:
            key = (window.handle, window.path)
            if supported(window.path) and key not in self.tab_cache and key not in self.tab_requests:
                self.tab_requests.add(key)
                self.owner.launch(self.read_tabs(key))

    async def read_tabs(self, key):
        tabs, error = [], ""
        try:
            async with self.tab_slots:
                tabs = await asyncio.to_thread(list_tabs, key[0])
        except (RuntimeError, OSError) as exc:
            error = str(exc)
        finally:
            self.tab_requests.discard(key)
        self.tab_cache[key] = (time.monotonic() + 20, tabs, error)
        index = self.list.currentRow()
        if self.stack.currentIndex() == 1 and index >= 0:
            window = self.available[index]
            if key == (window.handle, window.path):
                self.show_tabs()

    def show_tabs(self):
        index = self.list.currentRow()
        window = self.available[index] if index >= 0 else None
        saved = self.owner.controller.config["windows"].get(self.editing, {})
        path = window.path if window else saved.get("path", "")
        self.tab_panel.setVisible(supported(path))
        self.tab_choices.clear()
        if not supported(path):
            return
        self.tab_choices.addItem(tr("Entire window"))
        self.tab_choices.item(0).setIcon(icon("window"))
        self.tab_choices.item(0).setData(Qt.ItemDataRole.UserRole, "")
        if window:
            self.preload_tabs([window])
            _, tabs, error = self.tab_cache.get((window.handle, window.path), (0, [], "Reading browser tabs…"))
        else:
            tabs, error = [], "Window is not open"
        for tab in tabs:
            title = tab["title"]
            site = tab_site(title)
            text = re.sub(r"^\(\d+\)\s*", "", title)
            if site and len(matching_tabs(tabs, site)) == 1:
                text = site
            self.tab_choices.addItem(text if len(text) <= 48 else text[:47].rstrip() + "…")
            item = self.tab_choices.item(self.tab_choices.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, title)
            item.setData(Qt.ItemDataRole.AccessibleDescriptionRole, title)
        self.tab_status.setText(tr(error))
        self.tab_status.setVisible(bool(error))
        self.tab_match.setVisible(bool(self.tab_match.text()))
        self.sync_tab_selection()

    def sync_tab_selection(self, *_):
        match = self.tab_match.text().strip()
        choices = [self.tab_choices.item(i) for i in range(self.tab_choices.count())]
        if not choices:
            return
        matching = [item for item in choices[1:]
                    if match.casefold() in item.data(Qt.ItemDataRole.UserRole).casefold()] if match else choices[:1]
        self.tab_choices.setCurrentItem(matching[0] if len(matching) == 1 else None)

    def chosen_tab(self,item,_previous=None):
        title = item.data(Qt.ItemDataRole.UserRole)
        if not title:
            self.tab_match.clear()
            self.tab_match.hide()
            index = self.list.currentRow()
            if index >= 0 and not self.editing and not self.name.isModified() and not self.role:
                self.name.setText(self.list.item(index).text())
            return
        needle = tab_site(title) or title
        choices = [{"title": self.tab_choices.item(i).data(Qt.ItemDataRole.UserRole)}
                   for i in range(1, self.tab_choices.count())]
        if len(matching_tabs(choices, needle)) != 1:
            needle = title
        self.tab_match.setText(needle)
        self.tab_match.show()
        if not self.editing and not self.name.isModified():
            self.name.setText(item.text()[:60])

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
                self.set_result("Choose two different windows")
                return
            target = dict(window.identity(),name=self.name.text().strip())
            if window.app_id:
                target["app_id"] = window.app_id
        else:
            target["name"] = self.name.text().strip()
        target.pop('tab_match',None)
        if supported(target["path"]) and self.tab_match.text().strip():
            target['tab_match']=self.tab_match.text().strip()
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
            self.set_result(str(exc))

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
            available = detected["windows"]
            self.preload_tabs(available)
            cfg = copy.deepcopy(self.owner.controller.config)
            selected = []
            for role,key,title in (("mywhoosh","mywhoosh","MyWhoosh"),("video","media","Media")):
                matches = detected[key]
                if role_ref(cfg,role) in cfg["windows"] or len(matches) != 1:
                    continue
                win = next(win for win in available if win.handle == matches[0])
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
            self.status.setText(tr(detected["warning"]) if detected["warning"] else "")
            self.status.setVisible(bool(detected["warning"]))
            self.reload()
        except (RuntimeError,OSError,ValueError) as exc:
            self.set_result(str(exc))
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
            self.set_result("Action completed" if completed else "Cancelled")
        except (RuntimeError,OSError) as exc:
            self.set_result(str(exc))
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
        for point in cfg["positions"].values():
            if point.get("window_id") == self.ident:
                point.pop("window_id")
        cfg["window_roles"] = {r:ref if ref != self.ident else None for r,ref in cfg["window_roles"].items()}
        self.owner.controller.windows.session.pop(self.ident,None)
        try:
            self.owner.controller.save(cfg)
            self.ident = None
            self.reload()
        except (ValueError,OSError) as exc:
            self.set_result(str(exc))
