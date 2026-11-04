"""Two window targets, with native app icons and an inline window chooser."""
import copy
from pathlib import Path
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy
from desktop_ui import card, label, push, make_page, show_page, PAGE_BUTTONS
from ui_controls import SelectionList
from ui_icons import badge, icon, application_icon
from i18n import tr, language


class WindowTitle(QLabel):
    def __init__(self):
        super().__init__()
        self.full_text = ""
        self.setObjectName("muted")
        self.setProperty("i18nUserText",True)
        self.setProperty("i18nUserAccessible",True)
        self.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)

    def set_title(self, text):
        self.full_text = text
        self.setAccessibleName(text)
        self.render()

    def render(self):
        self.setText(self.fontMetrics().elidedText(self.full_text,Qt.TextElideMode.ElideRight,max(0,self.width())))

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.render()


class WindowsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.owner, self.role = window,"mywhoosh"
        self.available = []
        self.rendered_language = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0,0,0,0)
        page,box = make_page("Windows")
        box.setSpacing(14)
        outer.addWidget(page)
        targets = QGridLayout()
        targets.setSpacing(14)
        self.summaries, self.app_icons, self.role_buttons = {},{},{}
        for column,(role,title) in enumerate((("mywhoosh","MyWhoosh"),("video","Video"))):
            surface,content = card()
            content.setContentsMargins(18,16,18,16)
            content.setSpacing(10)
            heading = QHBoxLayout()
            image = badge("window")
            if role == "mywhoosh":
                image.set_icon(QIcon(str(Path(__file__).with_name("assets")/"mywhoosh.png")))
            heading.addWidget(image)
            heading.addWidget(label(title,size=17),1)
            content.addLayout(heading)
            summary = WindowTitle()
            content.addWidget(summary)
            choose = push("Choose window",lambda _=False,r=role:self.choose_role(r))
            choose.setIcon(icon("window"))
            content.addWidget(choose)
            self.summaries[role], self.app_icons[role], self.role_buttons[role] = summary,image,choose
            targets.addWidget(surface,0,column)
        box.addLayout(targets)
        self.picker,content = card()
        content.setContentsMargins(16,12,16,12)
        content.setSpacing(8)
        heading = QHBoxLayout()
        self.picker_title = label("Open windows",size=16)
        self.picker_title.setProperty("i18nUserText",True)
        heading.addWidget(self.picker_title,1)
        refresh = push("Refresh",self.populate)
        refresh.setObjectName("quiet")
        heading.addWidget(refresh)
        content.addLayout(heading)
        self.list = SelectionList()
        self.list.setObjectName("windowChoices")
        self.list.setStyleSheet("QListWidget { background:#fff; border:0; padding:0; } QListWidget::item { padding:7px 10px; margin:1px; }")
        self.list.setIconSize(QSize(30,30))
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.list.setMinimumHeight(75)
        self.list.setMaximumHeight(110)
        self.list.setAccessibleName("Open windows")
        self.list.currentItemChanged.connect(lambda *_:self.select_button.setEnabled(self.list.currentRow() >= 0))
        content.addWidget(self.list)
        controls = QHBoxLayout()
        controls.addStretch()
        controls.addWidget(push("Cancel",self.close_picker))
        self.select_button = push("Use selected window",self.select,True)
        self.select_button.setEnabled(False)
        controls.addWidget(self.select_button)
        content.addLayout(controls)
        box.addWidget(self.picker)
        self.picker.hide()
        self.function,content = card()
        content.setContentsMargins(18,16,18,16)
        row = QHBoxLayout()
        row.addWidget(badge("switch"))
        text = QVBoxLayout()
        text.setSpacing(3)
        text.addWidget(label("Switch windows",size=16))
        text.addWidget(label("Assign this action to a controller button.","muted"))
        row.addLayout(text,1)
        self.test_button = push("Test",lambda:window.launch(self.test()))
        row.addWidget(self.test_button)
        row.addWidget(push("Buttons",lambda:show_page(window,PAGE_BUTTONS)))
        content.addLayout(row)
        box.addWidget(self.function)
        self.result = label("","muted")
        box.addWidget(self.result)
        box.addStretch()

    def choose_role(self, role):
        self.role = role
        self.picker_title.setText(tr("Choose window") + " · " + tr("MyWhoosh" if role == "mywhoosh" else "Video"))
        self.populate()
        self.function.hide()
        self.picker.show()

    def close_picker(self):
        self.picker.hide()
        self.function.show()

    def populate(self):
        try:
            self.available = self.owner.controller.windows.native.list()
            self.list.clear()
            for window in self.available:
                self.list.addItem(window.title + "\n" + Path(window.path).stem)
                self.list.item(self.list.count()-1).setIcon(application_icon(window.path))
            self.select_button.setEnabled(False)
        except (RuntimeError,OSError) as exc:
            self.owner.controller.windows.result = str(exc)

    def reload(self):
        self.rendered_language = language()
        self.picker_title.setText(tr("Choose window") + " · " + tr("MyWhoosh" if self.role == "mywhoosh" else "Video"))
        ready = True
        for role,summary in self.summaries.items():
            identity = self.owner.controller.config["windows"].get(role)
            if identity:
                title = identity["title"]
                try:
                    self.owner.controller.windows.target(role,self.owner.controller.config)
                except RuntimeError:
                    ready = False
                    title = tr("Select again") + " · " + title
                summary.set_title(title)
                self.app_icons[role].set_icon(application_icon(identity["path"]))
            else:
                ready = False
                summary.set_title(tr("No window selected"))
        self.test_button.setEnabled(ready)
        self.function.setVisible(self.picker.isHidden())

    def select(self):
        index = self.list.currentRow()
        if index < 0:
            return
        window = self.available[index]
        config = copy.deepcopy(self.owner.controller.config)
        other = "video" if self.role == "mywhoosh" else "mywhoosh"
        if other in config["windows"]:
            try:
                current = self.owner.controller.windows.target(other,config)
            except RuntimeError:
                current = None
            if current and current.handle == window.handle:
                self.owner.controller.windows.result = "Choose a different window for each target."
                return
        config["windows"][self.role] = window.identity()
        try:
            self.owner.controller.save(config)
            self.owner.controller.windows.select(self.role,window)
            self.picker.hide()
            self.function.show()
            self.reload()
        except (RuntimeError,OSError,ValueError) as exc:
            self.owner.controller.windows.result = str(exc)

    async def test(self):
        await self.owner.controller.windows.run("switch_windows",copy.deepcopy(self.owner.controller.config))
