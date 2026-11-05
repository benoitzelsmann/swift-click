"""Linear visual routine editor using previously saved windows and positions."""
import copy
import threading
import uuid
from PySide6.QtCore import Qt,QSize
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QStackedWidget,QLineEdit,QDoubleSpinBox
from desktop_ui import make_page,card,label,push
from ui_controls import SelectionList,ToggleSwitch,confirm_dialog
from ui_icons import icon,badge,application_icon
from flow_widgets import FlowList,step_text,SYMBOLS
from settings import STEP_ACTIONS,routine_steps,step_problem
from i18n import tr,language


class RoutinesPage(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.ident = None
        self.rendered_language = None
        self.editing_row = None
        self.pending_step = None
        self.testing = False
        self.test_stop = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0,0,0,0)
        page,body = make_page("Routines",action=push("New routine",self.new,True))
        outer.addWidget(page)
        surface,content = card()
        content.setContentsMargins(16,12,16,12)
        content.setSpacing(8)
        body.addWidget(surface,1)
        content.addWidget(label("Build a sequence from your saved windows and mouse positions. Actions run from top to bottom.","muted"))
        self.stack = QStackedWidget()
        content.addWidget(self.stack,1)
        catalogue = QWidget()
        box = QVBoxLayout(catalogue)
        box.setContentsMargins(0,0,0,0)
        self.list = SelectionList()
        self.list.setIconSize(QSize(34,34))
        self.list.setAccessibleName("Saved routines")
        self.list.setStyleSheet("QListWidget {background:white;border:0;padding:0;} QListWidget::item {padding:14px;margin-bottom:6px;background:#f6f8f8;}")
        self.list.currentItemChanged.connect(self.selection)
        box.addWidget(self.list,1)
        self.empty = QWidget()
        empty = QVBoxLayout(self.empty)
        empty.addStretch()
        empty.addWidget(badge("routine",56),alignment=Qt.AlignmentFlag.AlignCenter)
        empty.addWidget(label("No saved routines","muted"),alignment=Qt.AlignmentFlag.AlignCenter)
        empty.addStretch()
        box.addWidget(self.empty,1)
        controls = QHBoxLayout()
        self.edit_button = push("Edit",self.edit)
        self.test = push("Test",lambda:owner.launch(self.run()))
        self.delete = push("Delete",self.remove)
        self.stop_button = push("Stop",self.stop_test)
        self.stop_button.hide()
        for widget in (self.edit_button,self.test,self.stop_button,self.delete):
            controls.addWidget(widget)
        controls.addStretch()
        box.addLayout(controls)
        self.stack.addWidget(catalogue)
        editor = QWidget()
        edit = QVBoxLayout(editor)
        edit.setContentsMargins(0,0,0,0)
        edit.setSpacing(8)
        self.name = QLineEdit()
        self.name.setMaxLength(60)
        self.name.setAccessibleName("Routine name")
        self.name.setPlaceholderText("Routine name")
        self.name.textChanged.connect(self.update_controls)
        edit.addWidget(self.name)
        columns = QHBoxLayout()
        columns.setSpacing(14)
        diagram = QVBoxLayout()
        head = QHBoxLayout()
        head.addWidget(label("Start","muted"),1)
        self.add_button = push("Add action",self.choose_action)
        self.add_button.setObjectName("quiet")
        head.addWidget(self.add_button)
        diagram.addLayout(head)
        self.flow = FlowList(lambda:owner.controller.config)
        self.flow.currentRowChanged.connect(self.show_step)
        self.flow.model().rowsMoved.connect(self.reordered)
        diagram.addWidget(self.flow,1)
        order = QHBoxLayout()
        self.up_button = push("↑",lambda:self.move(-1))
        self.up_button.setAccessibleName("Move step up")
        self.down_button = push("↓",lambda:self.move(1))
        self.down_button.setAccessibleName("Move step down")
        self.remove_step_button = push("Remove",self.remove_step)
        for widget in (self.up_button,self.down_button,self.remove_step_button):
            widget.setObjectName("quiet")
            order.addWidget(widget)
        order.addStretch()
        self.end = label("End","muted")
        order.addWidget(self.end)
        diagram.addLayout(order)
        columns.addLayout(diagram,3)
        self.panels = QStackedWidget()
        self.panels.setMinimumWidth(230)
        self.panels.setMaximumWidth(340)
        columns.addWidget(self.panels,2)
        chooser = QWidget()
        choices = QVBoxLayout(chooser)
        choices.setContentsMargins(0,0,0,0)
        choices.addWidget(label("Add action",size=16))
        grid = QGridLayout()
        grid.setSpacing(7)
        short = {"open":"Open","activate":"Activate","minimize":"Minimize","close":"Close",
                 "switch":"Switch","click":"Click","seek_back":"Back","seek_forward":"Forward","wait":"Wait"}
        for index,action in enumerate(STEP_ACTIONS):
            button = push(short[action],lambda _=False,a=action:self.add_action(a))
            button.setObjectName("choice")
            button.setIcon(icon(SYMBOLS[action]))
            button.setAccessibleName(STEP_ACTIONS[action])
            grid.addWidget(button,index//2,index%2)
        choices.addLayout(grid)
        choices.addStretch()
        self.panels.addWidget(chooser)
        props = QWidget()
        prop = QVBoxLayout(props)
        prop.setContentsMargins(0,0,0,0)
        prop.setSpacing(10)
        self.step_title = label("",size=16)
        prop.addWidget(self.step_title)
        self.window_button = push("Choose a window",lambda:self.pick("window_id"))
        self.other_button = push("Choose a window",lambda:self.pick("other_window_id"))
        self.position_button = push("Choose a position",lambda:self.pick("position_id"))
        for widget in (self.window_button,self.other_button,self.position_button):
            widget.setProperty("i18nUserText",True)
            widget.setProperty("i18nUserAccessible",True)
            prop.addWidget(widget)
        self.seconds = QDoubleSpinBox()
        self.seconds.setRange(.1,10.)
        self.seconds.setSingleStep(.1)
        self.seconds.setDecimals(1)
        self.seconds.setAccessibleName("Wait in seconds")
        self.seconds.valueChanged.connect(self.set_seconds)
        prop.addWidget(self.seconds)
        self.step_note = label("","muted")
        self.step_note.setStyleSheet("font-size:12px")
        prop.addWidget(self.step_note)
        prop.addStretch()
        prop.addWidget(push("Back to actions",self.choose_action))
        self.apply_step_button = push("Apply step",self.apply_step,True)
        prop.addWidget(self.apply_step_button)
        self.panels.addWidget(props)
        picks = QWidget()
        pick = QVBoxLayout(picks)
        pick.setContentsMargins(0,0,0,0)
        self.pick_title = label("",size=16)
        pick.addWidget(self.pick_title)
        self.target_choices = SelectionList()
        self.target_choices.setIconSize(QSize(26,26))
        self.target_choices.itemClicked.connect(self.picked)
        self.target_choices.itemActivated.connect(self.picked)
        pick.addWidget(self.target_choices,1)
        pick.addWidget(push("Back",lambda:self.panels.setCurrentIndex(1)))
        self.panels.addWidget(picks)
        edit.addLayout(columns,1)
        footer = QHBoxLayout()
        self.return_previous = ToggleSwitch("Return to previous window")
        self.return_previous.toggled.connect(self.update_controls)
        footer.addWidget(self.return_previous)
        footer.addStretch()
        footer.addWidget(push("Cancel",self.finish))
        self.save = push("Save",self.persist,True)
        footer.addWidget(self.save)
        edit.addLayout(footer)
        self.stack.addWidget(editor)
        self.result = label("","muted")
        content.addWidget(self.result)
        self.new()
        self.stack.setCurrentIndex(0)

    def config(self):
        return self.owner.controller.config

    def reload(self, selected=None):
        self.rendered_language = language()
        selected = selected or self.ident
        self.list.blockSignals(True)
        self.list.clear()
        for ident,routine in self.config()["routines"].items():
            steps = routine_steps(routine,self.config())
            invalid = any(step_problem(step,self.config()) for step in steps)
            summary = tr("Needs configuration") if invalid else tr("{count} actions").format(count=len(steps))
            if steps:
                summary += " · " + step_text(steps[0],self.config())[0]
                if len(steps) > 1:
                    summary += " → " + step_text(steps[-1],self.config())[0]
            self.list.addItem(routine["name"]+"\n"+summary)
            item = self.list.item(self.list.count()-1)
            item.setIcon(icon("routine"))
            item.setData(Qt.ItemDataRole.UserRole,ident)
            if ident == selected:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        self.list.setVisible(bool(self.list.count()))
        self.empty.setVisible(not self.list.count())
        if self.stack.currentIndex() == 0:
            self.selection(self.list.currentItem())
        else:
            self.flow.viewport().update()
            self.refresh_step()
        self.update_controls()

    def selection(self, item, _previous=None):
        if self.stack.currentIndex() != 0:
            return
        self.ident = item.data(Qt.ItemDataRole.UserRole) if item else None
        self.update_controls()

    def new(self):
        if self.testing:
            return
        self.ident = None
        self.name.clear()
        self.flow.set_steps([])
        self.return_previous.setChecked(False)
        self.choose_action()
        self.stack.setCurrentIndex(1)
        self.update_controls()

    def edit(self):
        if not self.ident:
            return
        routine = self.config()["routines"][self.ident]
        self.name.setText(routine["name"])
        self.flow.set_steps(routine_steps(routine,self.config()))
        self.return_previous.setChecked(routine["return"])
        self.choose_action()
        self.stack.setCurrentIndex(1)
        self.update_controls()

    def choose_action(self):
        self.pending_step = None
        self.editing_row = None
        self.flow.setCurrentRow(-1)
        self.panels.setCurrentIndex(0)
        self.update_controls()

    def add_action(self, action):
        if self.flow.count() >= 32:
            return
        self.flow.setCurrentRow(-1)
        self.editing_row = None
        self.pending_step = {"action":action,"seconds":.5} if action == "wait" else {"action":action,"window_id":None}
        if action == "switch": self.pending_step["other_window_id"] = None
        if action == "click": self.pending_step["position_id"] = None
        self.refresh_step()
        self.panels.setCurrentIndex(1)

    def show_step(self, row):
        if row < 0 or not hasattr(self,"panels"):
            return
        self.editing_row = row
        self.pending_step = copy.deepcopy(self.flow.item(row).data(Qt.ItemDataRole.UserRole))
        self.refresh_step()
        self.panels.setCurrentIndex(1)

    def refresh_step(self):
        if not self.pending_step:
            return
        step = self.pending_step
        action = step["action"]
        self.step_title.setText(tr(STEP_ACTIONS[action]))
        for field,button in (("window_id",self.window_button),("other_window_id",self.other_button),("position_id",self.position_button)):
            button.setVisible(field in step)
            source = self.config()["positions" if field == "position_id" else "windows"]
            target = source.get(step.get(field))
            text = target["name"] if target else tr("Choose a position" if field == "position_id" else "Choose a window")
            button.setText(button.fontMetrics().elidedText(text,Qt.TextElideMode.ElideRight,max(170,button.width()-40)))
            button.setAccessibleName(text)
            button.setIcon(icon("position") if field == "position_id" else application_icon(target["path"]) if target else icon("window"))
        self.seconds.setVisible(action == "wait")
        if action == "wait":
            self.seconds.blockSignals(True)
            self.seconds.setValue(step["seconds"])
            self.seconds.blockSignals(False)
        notes = {"close":"Normal close: the application's confirmation dialogs remain active.",
                 "switch":"Switches to the other selected window. From any other app, shows the first window.",
                 "open":"Opens the application. Restoring a document or tab depends on that app.",
                 "click":"The point must be inside the chosen window and not covered.",
                 "seek_back":"Keep keyboard focus on the video player inside the selected browser window.",
                 "seek_forward":"Keep keyboard focus on the video player inside the selected browser window."}
        self.step_note.setText(notes.get(action,""))
        self.apply_step_button.setEnabled(not step_problem(step,self.config()))
        self.update_controls()

    def set_seconds(self, value):
        if self.pending_step and self.pending_step["action"] == "wait":
            self.pending_step["seconds"] = value
            self.update_controls()

    def pick(self, field):
        self.pick_field = field
        positions = field == "position_id"
        self.pick_title.setText("Mouse positions" if positions else "Windows")
        self.target_choices.clear()
        for ident,target in self.config()["positions" if positions else "windows"].items():
            self.target_choices.addItem(target["name"])
            item = self.target_choices.item(self.target_choices.count()-1)
            item.setData(Qt.ItemDataRole.UserRole,ident)
            item.setIcon(icon("position") if positions else application_icon(target["path"]))
        self.panels.setCurrentIndex(2)
        if not self.target_choices.count():
            self.pick_title.setText("Create a mouse position first in Actions → Mouse positions." if positions else "Add a window first in Actions → Windows.")
        self.target_choices.setFocus()

    def picked(self, item):
        self.pending_step[self.pick_field] = item.data(Qt.ItemDataRole.UserRole)
        self.refresh_step()
        self.panels.setCurrentIndex(1)

    def apply_step(self):
        if not self.pending_step or step_problem(self.pending_step,self.config()):
            return
        row = self.editing_row
        if row is None:
            self.flow.append(self.pending_step)
            row = self.flow.count()-1
        else:
            self.flow.set_step(row,self.pending_step)
        self.pending_step = None
        self.flow.setCurrentRow(row)
        self.show_step(row)
        self.flow.scrollToItem(self.flow.item(row))
        self.update_controls()

    def move(self, delta):
        row = self.flow.currentRow()
        if row < 0 or not 0 <= row+delta < self.flow.count():
            return
        item = self.flow.takeItem(row)
        self.flow.insertItem(row+delta,item)
        self.flow.setCurrentRow(row+delta)
        self.update_controls()

    def reordered(self, *_):
        self.show_step(self.flow.currentRow())
        self.flow.viewport().update()
        self.update_controls()

    def remove_step(self):
        row = self.flow.currentRow()
        if row >= 0:
            self.flow.takeItem(row)
            self.choose_action()

    def update_controls(self, *_):
        if not hasattr(self,"save"):
            return
        steps = self.flow.steps()
        dirty = self.pending_step is not None and (self.editing_row is None or self.editing_row >= len(steps) or self.pending_step != steps[self.editing_row])
        valid = bool(self.name.text().strip()) and bool(steps) and not any(step_problem(step,self.config()) for step in steps)
        self.save.setEnabled(valid and not dirty and not self.testing)
        selected = self.ident in self.config()["routines"]
        self.edit_button.setEnabled(selected and not self.testing)
        self.delete.setEnabled(selected and not self.testing)
        routine = self.config()["routines"].get(self.ident)
        self.test.setEnabled(selected and not self.testing and not any(step_problem(s,self.config()) for s in routine_steps(routine,self.config())) if routine else False)
        self.stop_button.setVisible(self.testing)
        self.add_button.setEnabled(len(steps) < 32)
        row = self.flow.currentRow()
        self.up_button.setEnabled(row > 0)
        self.down_button.setEnabled(0 <= row < len(steps)-1)
        self.remove_step_button.setEnabled(row >= 0)
        self.end.setText(tr("Return") if self.return_previous.isChecked() else tr("End"))

    def draft(self):
        return {"name":self.name.text().strip(),"steps":self.flow.steps(),"return":self.return_previous.isChecked()}

    def persist(self):
        if not self.save.isEnabled():
            return
        cfg = copy.deepcopy(self.config())
        ident = self.ident or str(uuid.uuid4())
        cfg["routines"][ident] = self.draft()
        try:
            self.owner.controller.save(cfg)
            self.ident = ident
            self.stack.setCurrentIndex(0)
            self.reload(ident)
            self.owner.load_bindings()
            self.result.setText("Saved")
        except (ValueError,OSError) as exc:
            self.result.setText(str(exc))

    def finish(self):
        self.pending_step = None
        self.stack.setCurrentIndex(0)
        self.reload(self.ident)

    async def run(self):
        if self.testing or not self.ident:
            return
        self.testing = True
        self.test_stop = threading.Event()
        self.update_controls()
        try:
            completed = await self.owner.controller.windows.run({"action":"routine","routine_id":self.ident},copy.deepcopy(self.config()),self.test_stop)
            self.result.setText("Action completed" if completed else "Cancelled")
        except (RuntimeError,OSError) as exc:
            self.result.setText(str(exc))
        finally:
            self.testing = False
            self.test_stop = None
            self.update_controls()

    def stop_test(self):
        if self.test_stop:
            self.test_stop.set()

    def remove(self):
        if not self.ident or not confirm_dialog(self,"Delete routine","Delete this routine? Its assignments will become None.",accept="Delete"):
            return
        cfg = copy.deepcopy(self.config())
        del cfg["routines"][self.ident]
        for mapping in cfg["buttons"].values():
            for gesture,binding in mapping.items():
                if isinstance(binding,dict) and binding.get("routine_id") == self.ident:
                    mapping[gesture] = "none"
        self.owner.controller.save(cfg)
        self.ident = None
        self.reload()
        self.owner.load_bindings()
