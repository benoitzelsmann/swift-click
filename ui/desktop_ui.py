"""Qt views for connections, controller bindings and dashboard status."""

from pathlib import Path
import copy
from PySide6.QtCore import (
    Qt,
    QRectF,
    Signal,
)
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QStackedWidget,
    QTextEdit,
    QButtonGroup,
    QSizePolicy,
    QScrollArea,
)
from settings import ACTIONS, ASSIGNABLE, REPEATABLE, action_id
from ui_controls import KeyboardButton, ToggleSwitch, SelectionList
from i18n import tr

ACTION_GROUPS = {
    "MyWhoosh": ("shift_up", "shift_down"),
    "Volume": ("volume_down", "volume_up"),
    "Playback": ("media_previous", "media_play_pause", "media_next"),
    "Video": ("seek_back", "seek_forward"),
    "Mouse": ("mouse_click", "mouse_position"),
}
from i18n import tr

COLORS = {
    "y": "#00a8df",
    "z": "#ff7048",
    "a": "#8cc454",
    "b": "#f64098",
    "plus": "#253246",
}
STYLE = """
QWidget { color:#18202b; font-family:'Segoe UI'; font-size:13px; }
QMainWindow, QWidget#shell, QWidget#page { background:#f4f5f7; }
QFrame#header { background:white; border-bottom:1px solid #e5e7ed; }
QPushButton#assignment { background:#f5f6f8; border:1px solid transparent; border-radius:5px; padding:4px 7px; font-weight:500; }
QPushButton#assignment:hover { border-color:#86b6a5; color:#14674e; }
QPushButton#choice { background:#f5f6f8; border:1px solid transparent; border-radius:6px; padding:8px 10px; }
QPushButton#choice:checked { background:#dff2e9; border-color:#78ae96; color:#14523e; }
QPushButton#choice:hover { border-color:#6d9e8c; }
QPushButton#category { background:#f7f8fa; border:1px solid #e1e5eb; border-radius:7px; text-align:left; padding:12px 16px; }
QPushButton#category:hover { background:#edf0f4; border-color:#b8c2ce; }
QLabel#brand { font-size:18px; font-weight:700; }
QLabel#title { font-size:24px; font-weight:700; }
QLabel#muted { color:#626d7c; }
QFrame#card { background:white; border:1px solid #e1e5eb; border-radius:8px; }
QFrame#binding { background:transparent; border:1px solid transparent; border-radius:6px; }
QFrame#binding[selected="true"] { background:#edf6f2; border-color:#86b6a5; }
QPushButton { background:white; border:1px solid #dfe3e9; border-radius:6px; padding:8px 16px; font-weight:600; }
QPushButton:hover { background:#f1f3f8; border-color:#c0c8d7; }
QPushButton:pressed { background:#e7ebf3; }
QPushButton#primary { background:#202632; color:white; border:1px solid #202632; }
QPushButton#primary:hover { background:#384357; }
QPushButton#primary:disabled, QPushButton:disabled { color:#a2a8b2; background:#f2f3f6; border-color:#e8ebef; }
QPushButton#nav { border:0; border-bottom:2px solid transparent; border-radius:0; background:transparent; color:#626d7c; padding:15px 12px; }
QPushButton#nav:checked { color:#18202b; border-bottom-color:#18202b; background:transparent; }
QFrame#subnav { background:white; border-bottom:1px solid #e5e7ed; }
QPushButton#subnavButton { border:1px solid transparent; background:transparent; color:#626d7c; padding:5px 13px; }
QPushButton#subnavButton:checked { color:#18202b; background:#edf0f3; }
QPushButton#disclosureButton { border:1px solid transparent; background:transparent; text-align:left; padding:4px 0; }
QPushButton#disclosureButton:checked { background:transparent; color:#18202b; }
QListWidget#positions { background:white; border:0; border-radius:0; padding:2px; }
QListWidget#positions::item:selected { background:#edf0f3; color:#18202b; }
QFrame#separator { background:#e8ebef; border:0; }
QLabel#eyebrow { color:#287e68; font-size:12px; font-weight:600; }
QScrollArea { border:0; background:#f4f5f7; }
QScrollBar:vertical { background:#edf0f3; width:8px; margin:0; }
QScrollBar::handle:vertical { background:#b8c3ca; border-radius:4px; min-height:30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QPushButton:checked { background:#e4f3ec; color:#14674e; }
QPushButton#quiet { border:1px solid transparent; background:transparent; color:#626d7c; padding:3px 5px; }
QComboBox, QSpinBox, QLineEdit { background:#f6f7fa; border:1px solid #e8ebf0; border-radius:5px; padding:4px 8px; min-height:19px; }
QComboBox:hover, QSpinBox:hover { border-color:#b6bfd0; }
QComboBox:focus, QSpinBox:focus, QLineEdit:focus { border-color:#b6bfd0; }
QComboBox::drop-down { border:0; width:18px; }
QComboBox QAbstractItemView { background:white; selection-background-color:#e9edff; color:#18202b; border:1px solid #e1e5eb; }
QTextEdit { background:white; border:1px solid #e1e5eb; border-radius:6px; padding:8px; color:#626d7c; font-size:12px; }
QListWidget, QWidget#emptyPositions { border:1px solid transparent; background:#f7f9f8; border-radius:8px; padding:6px; }
QListWidget::item { padding:12px; margin-bottom:5px; border-radius:8px; }
QListWidget::item:selected { background:#e4f3ec; color:#14674e; }
QStatusBar { background:#f4f5f7; color:#626d7c; }
"""


def label(text, name=None, size=None):
    widget = QLabel(text)
    if name:
        widget.setObjectName(name)
    if size:
        widget.setStyleSheet(f"font-size:{size}px;font-weight:600")
    widget.setWordWrap(True)
    return widget


def push(text, callback, primary=False):
    widget = KeyboardButton(text)
    if primary:
        widget.setObjectName("primary")
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    widget.clicked.connect(callback)
    return widget


def card():
    widget = QFrame()
    widget.setObjectName("card")
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(26, 24, 26, 24)
    layout.setSpacing(14)
    return widget, layout


def logo(size=64):
    widget = QLabel()
    pix = QPixmap(str(Path(__file__).with_name("assets") / "mywhoosh.png"))
    widget.setPixmap(
        pix.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    )
    widget.setFixedSize(size, size)
    return widget


class AssignmentButton(KeyboardButton):
    changed = Signal()

    def __init__(self, caption):
        super().__init__()
        self.setObjectName("assignment")
        self.setProperty("i18nUserText", True)
        self.caption = caption
        self.full_text = ""
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setAccessibleName(caption)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_action(self, action):
        self.action = action
        ident = action_id(action)
        self.setProperty("i18nUserTooltip", ident == "mouse_position")
        self.full_text = tr(ACTIONS[ident][1])
        if ident == "mouse_position":
            points = self.window().controller.config["positions"]
            point = points.get(action["position_id"])
            self.full_text = point["name"] if point else "Choose a position"
        self.setToolTip(self.full_text)
        self.render_text()

    def render_text(self):
        self.setText(self.fontMetrics().elidedText(self.full_text, Qt.TextElideMode.ElideRight, max(0,self.width()-14)))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.render_text()


class ControllerImage(QWidget):
    def __init__(self):
        super().__init__()
        self.image = QPixmap(str(Path(__file__).with_name("assets") / "click-right.png"))
        self.setAccessibleName("Right-hand Zwift Click V2 controller")

    def paintEvent(self, event):
        if self.image.isNull():
            return
        size = self.image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        target = QRectF(0, 0, size.width(), size.height())
        target.moveCenter(QRectF(self.rect()).center())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(target, self.image, QRectF(self.image.rect()))


class ControllerEditor(QWidget):
    def __init__(self, bindings, window):
        super().__init__()
        self.window_owner = window
        self.pressed = set()
        self.cards = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.settings = QStackedWidget()
        layout.addWidget(self.settings)

        diagram = QWidget()
        self.settings.addWidget(diagram)
        grid = QGridLayout(diagram)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(20)
        for column in range(6):
            grid.setColumnStretch(column, 1)
        grid.setRowStretch(1, 1)

        self.photo = ControllerImage()
        grid.addWidget(self.photo, 1, 2, 1, 2)
        for key, row, column in (("y", 0, 2), ("z", 1, 0), ("a", 1, 4),
                                 ("b", 2, 1), ("plus", 2, 3)):
            frame = self.binding_card(key, bindings)
            grid.addWidget(frame, row, column, 1, 2, Qt.AlignmentFlag.AlignVCenter)

        self.restore = KeyboardButton("Reset")
        self.restore.setAccessibleName("Reset button assignments")
        self.restore.setToolTip("Reset button assignments")
        self.restore.setObjectName("quiet")
        grid.addWidget(self.restore, 0, 4, 1, 2,
                       Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        choices, choice_box = card()
        self.choices_frame = choices
        choice_box.setContentsMargins(18, 16, 18, 16)
        choice_box.setSpacing(10)
        self.choice_title = label("", size=18)
        choice_box.addWidget(self.choice_title)
        self.current_assignment = label("","muted")
        choice_box.addWidget(self.current_assignment)
        self.back_to_actions = push("Action types",self.show_actions)
        self.back_to_actions.setObjectName("quiet")
        self.back_to_actions.hide()
        choice_box.addWidget(self.back_to_actions,alignment=Qt.AlignmentFlag.AlignLeft)
        self.pick_pages = QStackedWidget()
        choice_box.addWidget(self.pick_pages)
        categories = QWidget()
        category_grid = QGridLayout(categories)
        category_grid.setContentsMargins(0,0,0,0)
        category_grid.setSpacing(10)
        self.category_buttons = {}
        for index, group in enumerate(ACTION_GROUPS):
            button = push(group,lambda _=False,g=group:self.show_group(g))
            button.setObjectName("category")
            button.setMinimumHeight(62)
            category_grid.addWidget(button,index//2,index%2)
            self.category_buttons[group] = button
        self.pick_pages.addWidget(categories)
        action_page = QWidget()
        actions_box = QVBoxLayout(action_page)
        actions_box.setContentsMargins(0,0,0,0)
        actions_box.setSpacing(14)
        self.group_title = label("",size=16)
        actions_box.addWidget(self.group_title)
        self.action_grid = QGridLayout()
        self.action_grid.setSpacing(14)
        actions_box.addLayout(self.action_grid)
        self.pick_pages.addWidget(action_page)
        self.options = QButtonGroup(self)
        self.option_cells = {}
        self.usage_labels = {}
        for index, action in enumerate(ASSIGNABLE):
            option = KeyboardButton(ACTIONS[action][1])
            option.setObjectName("choice")
            option.setProperty("action", action)
            option.setCheckable(True)
            option.setMinimumHeight(34)
            self.options.addButton(option)
            if action == "none":
                option.setMinimumHeight(62)
                category_grid.addWidget(option,2,1)
            else:
                cell = QWidget(action_page)
                cell_box = QVBoxLayout(cell)
                cell_box.setContentsMargins(0,0,0,0)
                cell_box.setSpacing(6)
                cell_box.addWidget(option)
                used = label("","muted")
                used.setStyleSheet("font-size:12px")
                cell_box.addWidget(used)
                self.usage_labels[action] = used
                self.option_cells[action] = cell
                cell.hide()
        self.options.buttonClicked.connect(self.apply_choice)
        positions_page = QWidget()
        positions_box = QVBoxLayout(positions_page)
        positions_box.setContentsMargins(0,0,0,0)
        positions_box.setSpacing(10)
        self.pick_pages.addWidget(positions_page)
        self.position_hint = label("Choose a saved screen point for this gesture.","muted")
        positions_box.addWidget(self.position_hint)
        self.position_choices = SelectionList()
        self.position_choices.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.position_choices.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.position_choices.setMaximumHeight(104)
        self.position_choices.currentItemChanged.connect(self.apply_position)
        positions_box.addWidget(self.position_choices)
        self.add_position = push("Create a position", self.create_position)
        self.add_position.setObjectName("quiet")
        positions_box.addWidget(self.add_position,alignment=Qt.AlignmentFlag.AlignLeft)
        self.pending_label = label("","muted")
        choice_box.addWidget(self.pending_label)
        controls = QHBoxLayout()
        controls.addWidget(push("Cancel",self.end_edit))
        controls.addStretch()
        self.save_button = push("Save",self.save_action,True)
        controls.addWidget(self.save_button)
        choice_box.addLayout(controls)
        choice_box.addStretch()
        picker = QWidget()
        picker_layout = QVBoxLayout(picker)
        choices.setMinimumWidth(540)
        choices.setMaximumWidth(640)
        picker_layout.addWidget(choices, alignment=Qt.AlignmentFlag.AlignCenter)
        self.settings.addWidget(picker)

    def edit_action(self, field):
        self.field = field
        self.pending = copy.deepcopy(field.action)
        self.choice_title.setText(field.caption)
        self.current_assignment.setText(tr("Current action: {action}").format(action=self.binding_text(field.action)))
        self.refresh_usage()
        self.show_actions()
        self.save_button.setEnabled(True)
        self.settings.setCurrentIndex(1)

    def show_actions(self):
        self.choices_frame.setMinimumWidth(540)
        self.choices_frame.setMaximumWidth(640)
        for option in self.options.buttons():
            option.setChecked(self.pending is not None and option.property("action") == action_id(self.pending))
        for group, button in self.category_buttons.items():
            allowed = [a for a in ACTION_GROUPS[group] if self.field.gesture != "hold" or a in REPEATABLE]
            button.setEnabled(bool(allowed))
        self.pick_pages.setCurrentIndex(0)
        self.back_to_actions.hide()
        self.update_pending()

    def show_group(self, group):
        self.choices_frame.setMinimumWidth(540)
        self.choices_frame.setMaximumWidth(640)
        self.refresh_usage()
        self.group_title.setText(tr(group))
        for cell in self.option_cells.values():
            self.action_grid.removeWidget(cell)
            cell.hide()
        allowed = [a for a in ACTION_GROUPS[group] if self.field.gesture != "hold" or a in REPEATABLE]
        for index, action in enumerate(allowed):
            cell = self.option_cells[action]
            self.action_grid.addWidget(cell,index//2,index%2)
            cell.show()
        self.pick_pages.setCurrentIndex(1)
        self.back_to_actions.show()

    def binding_text(self, binding):
        if binding is None:
            return tr("Choose a position")
        if action_id(binding) == "mouse_position":
            point = self.window_owner.controller.config["positions"].get(binding["position_id"])
            return point["name"] if point else tr("Choose a position")
        return tr(ACTIONS[action_id(binding)][1])

    def uses(self, action, position_id=None):
        found = []
        for key, gestures in self.window_owner.controller.config["buttons"].items():
            for gesture, binding in gestures.items():
                if action_id(binding) != action:
                    continue
                if position_id is not None and binding.get("position_id") != position_id:
                    continue
                found.append(("+" if key == "plus" else key.upper()) + " · " +
                             tr({"short":"Short","long":"Long","hold":"Hold"}[gesture]))
        return found

    def usage_text(self, action, position_id=None):
        uses = self.uses(action,position_id)
        if not uses:
            return tr("Not assigned")
        summary = ", ".join(uses[:2])
        if len(uses) > 2:
            summary += f" (+{len(uses)-2})"
        return tr("Used by {gestures}").format(gestures=summary)

    def refresh_usage(self):
        for action, used in self.usage_labels.items():
            used.setText(self.usage_text(action))
            used.setToolTip(", ".join(self.uses(action)))
        for group, button in self.category_buttons.items():
            allowed = [a for a in ACTION_GROUPS[group] if self.field.gesture != "hold" or a in REPEATABLE]
            assigned = sum(bool(self.uses(a)) for a in allowed)
            button.setText(tr(group) + "\n" + tr("{count} actions, {used} assigned").format(count=len(allowed),used=assigned))

    def update_pending(self):
        self.save_button.setEnabled(self.pending is not None)
        self.pending_label.setText(tr("Selected action: {action}").format(action=self.binding_text(self.pending)))
        self.pending_label.setVisible(self.pending != self.field.action)

    def apply_choice(self, option):
        action = option.property("action")
        if action == "mouse_position":
            self.pending = copy.deepcopy(self.field.action) if action_id(self.field.action) == "mouse_position" else None
            self.show_positions()
            return
        self.pending = action
        self.update_pending()

    def show_positions(self):
        self.choices_frame.setMinimumWidth(360)
        self.choices_frame.setMaximumWidth(480)
        signals_blocked = self.position_choices.blockSignals(True)
        self.position_choices.clear()
        for ident, point in self.window_owner.controller.config["positions"].items():
            self.position_choices.addItem(point["name"])
            item = self.position_choices.item(self.position_choices.count()-1)
            item.setText(point["name"] + "\n" + self.usage_text("mouse_position",ident))
            item.setData(Qt.ItemDataRole.UserRole,ident)
            item.setToolTip(point["name"])
            if isinstance(self.pending,dict) and self.pending.get("position_id") == ident:
                self.position_choices.setCurrentItem(item)
        self.position_choices.blockSignals(signals_blocked)
        count = self.position_choices.count()
        self.position_choices.ensurePolished()
        rows = sum(self.position_choices.sizeHintForRow(i) for i in range(min(2,count)))
        self.position_choices.setFixedHeight(max(1,rows+2*self.position_choices.frameWidth()))
        self.position_choices.setVisible(count > 0)
        self.position_hint.setText("Choose a saved screen point for this gesture." if count else "Create a screen point to use for this gesture.")
        self.position_hint.show()
        self.pick_pages.setCurrentIndex(2)
        self.back_to_actions.show()
        self.add_position.show()
        self.update_pending()

    def apply_position(self, item, _previous=None):
        if item is not None:
            self.pending = {"action":"mouse_position","position_id":item.data(Qt.ItemDataRole.UserRole)}
            self.update_pending()

    def select_position(self, ident):
        self.pending = {"action":"mouse_position","position_id":ident}
        self.show_positions()

    def save_action(self):
        if self.pending is not None:
            self.commit(copy.deepcopy(self.pending))

    def create_position(self):
        field = self.field
        self.end_edit()
        show_page(self.window_owner, PAGE_MOUSE)
        self.window_owner.mouse_page.new(binding_field=field)

    def commit(self, binding):
        previous = copy.deepcopy(self.field.action)
        self.field.set_action(binding)
        if self.window_owner.save_bindings():
            self.end_edit()
        else:
            self.field.set_action(previous)

    def end_edit(self):
        self.pending = None
        self.settings.setCurrentIndex(0)
        self.field.setFocus()


    def binding_card(self, key, bindings):
        frame = QFrame()
        frame.setObjectName("binding")
        grid = QGridLayout(frame)
        grid.setContentsMargins(10, 9, 10, 9)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)
        name = "+" if key == "plus" else key.upper()
        badge = label(name)
        badge.setFixedSize(25, 25)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ink = "white" if key == "plus" else "#101822"
        badge.setStyleSheet(f"background:{COLORS[key]};color:{ink};border-radius:12px;font-weight:700")
        grid.addWidget(badge, 0, 0, 3, 1)
        for row, (kind, title) in enumerate((("short", "Short"), ("long", "Long"), ("hold", "Hold"))):
            grid.addWidget(label(title, "muted"), row, 1)
            field = AssignmentButton(f"{name} · {title}")
            field.gesture = kind
            field.clicked.connect(lambda checked=False, select=field: self.edit_action(select))
            bindings[key, kind] = field
            grid.addWidget(field, row, 2)
        grid.setColumnStretch(2, 1)
        self.cards[key] = frame
        return frame

    def set_pressed(self, pressed):
        pressed = set(pressed)
        for key in pressed ^ self.pressed:
            frame = self.cards.get(key)
            if frame is not None:
                frame.setProperty("selected", key in pressed)
                frame.style().unpolish(frame)
                frame.style().polish(frame)
        self.pressed = pressed


def make_page(title, subtitle="", action=None):
    page = QWidget()
    page.setObjectName("page")
    layout = QVBoxLayout(page)
    layout.setContentsMargins(32, 28, 32, 28)
    layout.setSpacing(24)
    heading = QHBoxLayout()
    heading.addWidget(label(title, "title"), 1)
    if action is not None:
        heading.addWidget(action)
    layout.addLayout(heading)
    if subtitle:
        layout.addWidget(label(subtitle, "muted"))
    return page, layout


PAGE_DASHBOARD, PAGE_MYWHOOSH, PAGE_CONTROLLER, PAGE_MOUSE, PAGE_BUTTONS, PAGE_GENERAL, PAGE_CREDITS, PAGE_CONTACT = range(8)
PAGE_SECTIONS = (0, 1, 1, 2, 2, 2, 2, 2)


def scroll_page(page):
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setWidget(page)
    return scroll


def build_ui(w):
    from connection_help import GuidePanel, Disclosure, MYWHOOSH_STEPS, CONTROLLER_STEPS

    shell = QWidget()
    shell.setObjectName("shell")
    w.setCentralWidget(shell)
    outer = QVBoxLayout(shell)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)
    header = QFrame()
    header.setObjectName("header")
    header.setFixedHeight(54)
    nav = QHBoxLayout(header)
    nav.setContentsMargins(32, 0, 32, 0)
    nav.addWidget(label("Swift Click", "brand"))
    w.version_label = label(f"v{w.app_version} · UI {w.ui_revision}","muted")
    w.version_label.setWordWrap(False)
    w.version_label.setStyleSheet("font-size:11px")
    nav.addWidget(w.version_label)
    nav.addStretch()
    w.pages = QStackedWidget()
    w.nav = []
    w.last_section_pages = {0: PAGE_DASHBOARD, 1: PAGE_CONTROLLER, 2: PAGE_BUTTONS}
    for index, name in enumerate(("Dashboard", "Connections", "Settings")):
        item = push(name, lambda _=False, i=index: show_section(w, i))
        item.setObjectName("nav")
        item.setCheckable(True)
        nav.addWidget(item)
        w.nav.append(item)
    outer.addWidget(header)
    w.subnav_frame = QFrame()
    w.subnav_frame.setObjectName("subnav")
    subnav = QHBoxLayout(w.subnav_frame)
    subnav.setContentsMargins(32, 6, 32, 6)
    w.subnav = {}
    for target, name in ((PAGE_CONTROLLER, "Controller"), (PAGE_MYWHOOSH, "MyWhoosh"),
                         (PAGE_BUTTONS, "Buttons"), (PAGE_MOUSE, "Mouse positions"),
                         (PAGE_GENERAL, "General"), (PAGE_CREDITS, "Credits"), (PAGE_CONTACT, "Contact")):
        item = push(name, lambda _=False, i=target: show_page(w, i))
        item.setObjectName("subnavButton")
        item.setCheckable(True)
        subnav.addWidget(item)
        w.subnav[target] = item
    subnav.addStretch()
    outer.addWidget(w.subnav_frame)
    outer.addWidget(w.pages, 1)

    w.session_button = push("Start session", w.start_session, True)
    page, box = make_page("Dashboard", action=w.session_button)
    summary, summary_box = card()
    summary_box.setContentsMargins(28, 12, 28, 12)
    summary_box.setSpacing(0)
    w.dashboard_states = []
    for index, name in enumerate(("MyWhoosh", "Controller")):
        row = QHBoxLayout()
        row.setContentsMargins(0, 20, 0, 20)
        row.addWidget(label(name, size=16), 1)
        state = label("Not connected" if index == 0 else "Not connected")
        state.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(state)
        w.dashboard_states.append(state)
        summary_box.addLayout(row)
        if index == 0:
            divider = QFrame()
            divider.setObjectName("separator")
            divider.setFixedHeight(1)
            summary_box.addWidget(divider)
    box.addWidget(summary)
    box.addStretch()
    w.pages.addWidget(page)

    page, box = make_page("MyWhoosh")
    frame, items = card()
    items.setContentsMargins(24, 24, 24, 24)
    line = QHBoxLayout()
    line.addWidget(logo(40))
    line.addSpacing(14)
    info = QVBoxLayout()
    info.addWidget(label("Network connection", size=16))
    w.game_status = label("Not connected", "muted")
    info.addWidget(w.game_status)
    line.addLayout(info, 1)
    w.start_button = push("Connect", lambda: w.launch(w.start_link()), True)
    w.stop_button = push("Disconnect", lambda: w.launch(w.stop_link()))
    line.addWidget(w.start_button)
    line.addWidget(w.stop_button)
    items.addLayout(line)
    box.addWidget(frame)
    w.game_hint = label("", "muted")
    w.game_hint.hide()
    items.addWidget(w.game_hint)
    w.game_guide = GuidePanel("mywhoosh", MYWHOOSH_STEPS)
    box.addWidget(w.game_guide)
    trouble = Disclosure("Connection trouble?")
    trouble.body.addWidget(label(
        "<b>Grey LAN:</b> check Direct Connect under Connectivity and allow Bonjour if MyWhoosh asks.<br>"
        "<b>No prompt:</b> start the Swift Click connection, then click the OpenBikeControl handlebar in MyWhoosh.<br>"
        "<b>Two devices:</b> use the same local network. If discovery fails, check the selected network and network permissions.<br>"
        "<b>Connected but not shifting:</b> check the controller, assignments under Settings → Buttons and Virtual Shifting in MyWhoosh."
    ))
    w.network = QComboBox()
    w.network.setAccessibleName("Local network used for MyWhoosh")
    w.network_panel = Disclosure("Network and diagnostics")
    w.network_panel.body.addWidget(label("Local network", "muted"))
    w.network_panel.body.addWidget(w.network)
    w.network_refresh = push("Refresh networks", w.load_networks)
    w.network_panel.body.addWidget(w.network_refresh)
    w.activity = QTextEdit()
    w.activity.setReadOnly(True)
    w.activity.setMaximumHeight(130)
    w.activity.setAccessibleName("Connection diagnostics")
    w.activity.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    w.network_panel.body.addWidget(w.activity)
    w.network_panel.body.addWidget(trouble)
    box.addWidget(w.network_panel)
    box.addStretch()
    w.pages.addWidget(scroll_page(page))

    page, box = make_page("Controller")
    surface, content = card()
    content.setContentsMargins(24, 24, 24, 24)
    content.setSpacing(20)
    box.addWidget(surface)
    line = QHBoxLayout()
    line.setSpacing(12)
    info = QVBoxLayout()
    info.setSpacing(4)
    info.addWidget(label("Zwift Click V2 · Right", size=18))
    w.ble_status = label("Not connected", size=15)
    w.ble_status.setWordWrap(False)
    w.ble_details = label("", "muted")
    info.addWidget(w.ble_status)
    info.addWidget(w.ble_details)
    line.addLayout(info, 1)
    w.connect_button = push("Connect", lambda: w.launch(w.connect_ble()), True)
    w.connect_button.setToolTip("Press a button to wake the controller.")
    w.disconnect_button = push("Disconnect", lambda: w.launch(w.controller.stop()))
    w.maintenance = ToggleSwitch("Keep awake")
    w.maintenance.setChecked(w.controller.maintenance_allowed)
    w.maintenance.clicked.connect(w.choose_maintenance)
    line.addWidget(w.connect_button)
    line.addWidget(w.disconnect_button)
    content.addLayout(line)
    w.received_buttons = label("Button input · waiting for a connection", "muted")
    content.addWidget(w.received_buttons)
    content.addWidget(w.maintenance, alignment=Qt.AlignmentFlag.AlignLeft)
    w.controller_guide = GuidePanel("controller", CONTROLLER_STEPS, title="Help")
    box.addWidget(w.controller_guide)
    box.addStretch()
    w.pages.addWidget(scroll_page(page))

    from mouse_view import MousePage
    w.mouse_page = MousePage(w)
    w.pages.addWidget(w.mouse_page)

    page, box = make_page("Controller buttons", "")
    surface, content = card()
    content.setContentsMargins(20, 20, 20, 20)
    content.setSpacing(16)
    box.addWidget(surface, 1)
    w.bindings = {}
    w.editor = ControllerEditor(w.bindings, w)
    w.editor.restore.clicked.connect(w.restore_assignments)
    content.addWidget(w.editor, 1)
    w.pages.addWidget(page)

    from about_view import build_about_pages
    build_about_pages(w)
    show_page(w, PAGE_DASHBOARD)


def show_section(w, section):
    show_page(w, w.last_section_pages[section])


def show_page(w, index):
    section = PAGE_SECTIONS[index]
    w.last_section_pages[section] = index
    w.pages.setCurrentIndex(index)
    for i, item in enumerate(w.nav):
        item.setChecked(i == section)
    w.subnav_frame.setVisible(section != 0)
    for target, item in w.subnav.items():
        item.setVisible(PAGE_SECTIONS[target] == section)
        item.setChecked(target == index)


def refresh_ui(w):
    running = bool(w.service_task and not w.service_task.done())
    w.start_button.setEnabled(not running and not w.stopping)
    w.start_button.setText(
        "Connection started" if w.is_ready else "Connecting…" if running else "Connect"
    )
    w.stop_button.setEnabled(running and not w.stopping)
    w.network.setEnabled(not running)
    w.network_refresh.setEnabled(not running)
    connected = bool(
        w.is_ready
        and any(info["id"] == "mywhoosh" for info in w.shifter.app_info.values())
    )
    game = (
        "Connected"
        if connected
        else "Waiting for MyWhoosh"
        if w.is_ready
        else "Connecting…"
        if running
        else "Not connected"
    )
    w.game_status.setText(game)
    w.game_hint.setText("In MyWhoosh, click the OpenBikeControl handlebar, then accept with YES.")
    w.game_hint.setVisible(w.is_ready and not connected)
    w.dashboard_states[0].setText(game)
    status = w.controller.status()
    ble = (
        "Connected"
        if status["connected"]
        else "Searching…"
        if w.controller.task and not w.controller.task.done()
        else "Not connected"
    )
    w.ble_status.setText(ble)
    w.dashboard_states[1].setText(ble)
    w.ble_status.setToolTip(status["state"])
    battery = f"Battery {status['battery']}%" if status["battery"] is not None else ""
    w.ble_details.setText(
        "   ·   ".join(filter(None, (w.controller.oad_status, battery)))
        if status["connected"]
        else ""
    )
    w.ble_details.setVisible(bool(w.ble_details.text()))
    busy = status["running"] or status["connected"]
    stopping = w.controller.shutdown_lock.locked()
    w.session_button.setEnabled(
        not (w.stopping or stopping or w.connecting_ble or (running and busy))
    )
    w.session_button.setText(
        "Session connected"
        if connected and status["connected"]
        else "Connecting…"
        if running and busy
        else "Start session"
    )
    w.maintenance.setEnabled(not (busy or w.connecting_ble or stopping))
    w.connect_button.setEnabled(not (busy or w.connecting_ble or stopping))
    w.connect_button.setText("Searching…" if w.connecting_ble else "Connect")
    w.disconnect_button.setEnabled(busy and not stopping)
    for field, active in (
        (w.game_status, connected),
        (w.dashboard_states[0], connected),
        (w.ble_status, status["connected"]),
        (w.dashboard_states[1], status["connected"]),
    ):
        color = "#168064" if active else "#626d7c"
        if field.property("statusColor") != color:
            field.setStyleSheet(f"color:{color};font-weight:600")
            field.setProperty("statusColor", color)
    w.editor.set_pressed(status["pressed"])
    w.received_buttons.setVisible(status["connected"] and bool(status["pressed"] or status["last_pressed"]))
    if status["connected"]:
        if status["pressed"]:
            names = " · ".join("+" if key == "plus" else key.upper() for key in sorted(status["pressed"]))
            w.received_buttons.setText("Button input · " + names)
        else:
            names = " · ".join("+" if key == "plus" else key.upper() for key in status["last_pressed"])
            w.received_buttons.setText("Last button received · " + names if names else "Button input · press a button to test")
    else:
        w.received_buttons.setText("Button input · waiting for a connection")
    lines = list(reversed(status["events"])) + w.messages
    snapshot = "\n".join(lines[-35:])
    if snapshot != w.log_snapshot:
        w.activity.setPlainText(tr(snapshot))
        w.log_snapshot = snapshot
