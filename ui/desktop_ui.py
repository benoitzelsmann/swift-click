"""Qt views for connections, controller bindings and dashboard status."""

from pathlib import Path
import copy
from PySide6.QtCore import (
    Qt,
    QRectF,
    Signal,
    QSize,
)
from PySide6.QtGui import QPainter, QPixmap, QFont, QFontMetrics, QColor
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QStackedWidget,
    QTextEdit,
    QButtonGroup,
    QSizePolicy,
    QScrollArea,
)
from settings import ACTIONS, ASSIGNABLE, REPEATABLE, GESTURES, GESTURE_NAMES, action_id
from ui_controls import KeyboardButton, ToggleSwitch, SelectionList, GestureCheck
from i18n import tr, language
from ui_icons import action_icon,icon

ACTION_GROUPS = {
    "MyWhoosh": ("shift_up", "shift_down", "whoosh_left", "whoosh_right",
                 "junction_left", "junction_straight", "junction_right",
                 "intensity_down", "intensity_up"),
    "Media": ("volume_down", "volume_up", "volume_mute", "media_previous", "media_play_pause", "media_next", "seek_back", "seek_forward"),
    "Mouse": ("mouse_click", "mouse_position"),
    "Routines": ("routine",),
}

COLORS = {
    "y": "#00a8df",
    "z": "#ff7048",
    "a": "#8cc454",
    "b": "#f64098",
    "plus": "#253246",
}
from ui_theme import stylesheet, color
STYLE = stylesheet("light")

# Inside a group the context is already given, so tiles keep short names and clear symbols.
PICKER_TEXT = {"whoosh_left": "Move left", "whoosh_right": "Move right",
               "junction_left": "Left turn", "junction_straight": "Straight on", "junction_right": "Right turn",
               "intensity_down": "Intensity −", "intensity_up": "Intensity +"}
PICKER_SYMBOLS = {"shift_up": "chevron_up", "shift_down": "chevron_down",
                  "whoosh_left": "arrow_left", "whoosh_right": "arrow_right",
                  "junction_left": "turn_left", "junction_straight": "arrow_up", "junction_right": "turn_right",
                  "intensity_down": "minus", "intensity_up": "plus"}
GESTURE_MARKS = {"short": "", "double": "×2", "long": "Long", "hold": "Hold"}


def picker_icon(action):
    return icon(PICKER_SYMBOLS[action], role="accent") if action in PICKER_SYMBOLS else action_icon(action)


class UsageBadges(QWidget):
    """Coloured key badges on the right of an action tile: which presses already use it."""
    def __init__(self, button):
        super().__init__(button)
        self.button = button
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.summary = ""
        self.badges = []
        self.hide()
        button.installEventFilter(self)

    def text(self):
        return self.summary

    def set_uses(self, uses, summary):
        self.summary = summary if uses else ""
        self.badges = [({"a": "#5f9a2e"}.get(key, COLORS[key]), ("+" if key == "plus" else key.upper()) +
                        (" " + tr(GESTURE_MARKS[gesture]) if GESTURE_MARKS[gesture] else ""))
                       for key, gesture in uses[:3]]
        if len(uses) > 3:
            self.badges.append((None, f"+{len(uses) - 3}"))
        self.button.setToolTip(self.summary)
        self.button.setProperty("i18nUserTooltip", True)
        self.button.setAccessibleDescription(self.summary)
        self.setVisible(bool(uses))
        self.place()
        # Keep the label clear of the badges.
        self.button.setStyleSheet(f"padding-right:{self.width() + 18}px" if uses else "")
        self.update()

    def badge_font(self):
        font = QFont(self.font())
        font.setPixelSize(11)
        font.setBold(True)
        return font

    def place(self):
        metrics = QFontMetrics(self.badge_font())
        width = sum(metrics.horizontalAdvance(text) + 16 for _, text in self.badges) + 4 * max(0, len(self.badges) - 1)
        self.resize(max(1, width), 20)
        self.move(self.button.width() - self.width() - 10, (self.button.height() - self.height()) // 2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.badge_font())
        metrics = painter.fontMetrics()
        x = 0
        for fill, text in self.badges:
            width = metrics.horizontalAdvance(text) + 16
            rect = QRectF(x, 0, width, 20)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(fill or color("subtle")))
            painter.drawRoundedRect(rect, 10, 10)
            painter.setPen(QColor("white") if fill else QColor(color("muted")))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
            x += width + 4
        painter.end()

    def eventFilter(self, watched, event):
        if event.type() == event.Type.Resize:
            self.place()
        return False


def label(text, name=None, size=None):
    widget = QLabel(text)
    if name:
        widget.setObjectName(name)
    if size:
        widget.setStyleSheet(f"font-size:{size}px;font-weight:600")
    widget.setWordWrap(True)
    return widget


BUTTON_ICONS = {
    "Connect": "link", "Disconnect": "unlink", "Edit": "edit", "Delete": "trash", "Remove": "trash",
    "Test": "play", "Show": "eye", "Save": "check", "Save window": "check", "Save directions": "check",
    "Save action": "check", "Done": "check", "Confirm action": "check", "Refresh": "refresh",
    "Refresh networks": "refresh", "Reset": "reset", "Reset timings": "reset", "Restore MyWhoosh link": "reset",
    "Start session": "play", "Stop": "stop", "Open MyWhoosh": "open", "Open GitHub": "code", "Visit website": "globe", "Join the community": "community",
    "View release": "open", "Third-party licenses": "document", "Check for updates": "update",
    "Send an email": "mail", "Report a problem": "bug", "Suggest an improvement": "idea",
    "Copy technical details": "copy", "Export settings": "export", "Restore settings": "import",
    "Add destination": "plus", "Add a position": "plus", "Create a position": "plus", "New action": "plus",
    "Duplicate": "copy", "Detect": "detect", "Choose a window": "window", "Choose a position": "position",
    "Capture position": "target", "Manage presses": "sliders", "Manage routines": "routine",
    "Advanced routines": "routine", "Open settings": "settings", "Choose destination": "window",
    "Back": "back", "Action types": "back",
}
DANGER_BUTTONS = {"Delete", "Remove"}


def decorate(widget, text, primary=False):
    """Give a button its symbol; primary buttons draw it in the accent ink."""
    from ui_icons import icon as symbol
    name = BUTTON_ICONS.get(text)
    if name:
        widget.setIcon(symbol(name, role="on_accent" if primary else "muted"))
        widget.setIconSize(QSize(16, 16))
    return widget


def push(text, callback, primary=False):
    widget = KeyboardButton(text)
    if primary:
        widget.setObjectName("primary")
    elif text in DANGER_BUTTONS:
        widget.setObjectName("danger")
    decorate(widget, text, primary)
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
    widget = ControllerImage("mywhoosh.png", "MyWhoosh")
    widget.setFixedSize(size, size)
    return widget


class AssignmentButton(KeyboardButton):
    changed = Signal()

    def __init__(self, caption):
        super().__init__()
        self.setObjectName("assignment")
        self.setProperty("i18nUserText", True)
        self.setProperty("i18nUserAccessible", True)
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
        if ident in ("whoosh_left","whoosh_right"):
            self.full_text = tr("Move left" if ident == "whoosh_left" else "Move right")
        self.setIcon(action_icon(ident))
        self.setIconSize(QSize(16,16))
        if ident == "mouse_position":
            points = self.window().controller.config["positions"]
            point = points.get(action["position_id"])
            self.full_text = point["name"] if point else "Choose a position"
        if ident == "routine":
            routine = self.window().controller.config["routines"].get(action["routine_id"])
            self.full_text = routine["name"] if routine else tr("Choose a routine")
        self.setToolTip("")
        self.setAccessibleName(tr(self.caption) + " · " + self.full_text)
        self.render_text()

    def render_text(self):
        self.setText(self.fontMetrics().elidedText(self.full_text, Qt.TextElideMode.ElideRight, max(0,self.width()-(36 if not self.icon().isNull() else 14))))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.render_text()


class ControllerImage(QWidget):
    def __init__(self, source="click-right.png", accessible_name="Right-hand Zwift Click V2 controller"):
        super().__init__()
        self.image = QPixmap(str(Path(__file__).with_name("assets") / source))
        self.setAccessibleName(accessible_name)

    def sizeHint(self):
        return QSize(170, 170)

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
        self.gesture_rows = {}
        self.enable_switches = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.settings = QStackedWidget()
        layout.addWidget(self.settings)

        diagram = QWidget()
        self.settings.addWidget(diagram)
        grid = QGridLayout(diagram)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        for column in range(6):
            grid.setColumnStretch(column, 1)
        grid.setRowStretch(1, 1)

        self.photo = ControllerImage()
        self.photo.setMinimumSize(110, 110)
        self.photo.setMaximumSize(190, 190)
        self.photo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        grid.addWidget(self.photo, 1, 2, 1, 2, Qt.AlignmentFlag.AlignCenter)
        for key, row, column in (("y", 0, 2), ("z", 1, 0), ("a", 1, 4),
                                 ("b", 2, 1), ("plus", 2, 3)):
            frame = self.binding_card(key, bindings)
            grid.addWidget(frame, row, column, 1, 2, Qt.AlignmentFlag.AlignVCenter)

        # Gesture checks appear only while managing presses, to keep the diagram compact.
        self.manage = push("Manage presses", self.toggle_presses)
        self.manage.setCheckable(True)
        grid.addWidget(self.manage, 0, 0, 1, 2, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.restore = KeyboardButton("Reset")
        self.restore.setAccessibleName("Reset button assignments")
        grid.addWidget(self.restore, 0, 4, 1, 2,
                       Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        choices, choice_box = card()
        self.choices_frame = choices
        choice_box.setContentsMargins(18, 16, 18, 16)
        choice_box.setSpacing(10)
        # Title and current action on one line; no explanatory grey notes.
        header = QHBoxLayout()
        header.setSpacing(10)
        self.choice_title = label("", size=18)
        self.choice_title.setProperty("i18nUserText", True)
        self.choice_title.setWordWrap(False)
        header.addWidget(self.choice_title)
        header.addStretch()
        self.current_assignment = label("","pill")
        self.current_assignment.setProperty("i18nUserText",True)
        self.current_assignment.setWordWrap(False)
        header.addWidget(self.current_assignment, alignment=Qt.AlignmentFlag.AlignVCenter)
        choice_box.addLayout(header)
        self.timing = label("","muted")
        self.timing.hide()
        self.back_to_actions = push("Action types",self.show_actions)
        self.back_to_actions.setObjectName("quiet")
        self.back_to_actions.hide()
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
            button.setIcon(action_icon("shift_up" if group == "MyWhoosh" else "routine" if group == "Routines" else "mouse_click"))
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
        self.action_grid.setHorizontalSpacing(10)
        self.action_grid.setVerticalSpacing(10)
        actions_box.addLayout(self.action_grid)
        self.pick_pages.addWidget(action_page)
        self.options = QButtonGroup(self)
        self.option_cells = {}
        self.usage_labels = {}
        self.rendered_language = None
        self.active_group = None
        for index, action in enumerate(ASSIGNABLE):
            option = KeyboardButton(PICKER_TEXT.get(action, ACTIONS[action][1]))
            option.setObjectName("choice")
            option.setProperty("action", action)
            option.setIcon(picker_icon(action))
            option.setIconSize(QSize(18,18))
            option.setCheckable(True)
            option.setMinimumHeight(34)
            self.options.addButton(option)
            if action == "switch_windows":
                option.hide()
                continue
            if action == "none":
                option.setMinimumHeight(34)
                category_grid.addWidget(option,2,0,1,2)
            else:
                # One clean tile per action; tiles already in use carry coloured key badges.
                option.setObjectName("option")
                option.setMinimumHeight(42)
                option.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
                self.usage_labels[action] = UsageBadges(option)
                self.option_cells[action] = option
                option.hide()
        self.options.buttonClicked.connect(self.apply_choice)
        positions_page = QWidget()
        positions_box = QVBoxLayout(positions_page)
        positions_box.setContentsMargins(0,0,0,0)
        positions_box.setSpacing(10)
        self.pick_pages.addWidget(positions_page)
        self.position_hint = label("Choose a saved screen point for this gesture.","muted")
        positions_box.addWidget(self.position_hint)
        self.position_choices = SelectionList()
        self.position_choices.setStyleSheet("QListWidget::item { padding:5px 8px; margin-bottom:2px; font-size:12px; }")
        self.position_choices.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.position_choices.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.position_choices.setMaximumHeight(104)
        self.position_choices.currentItemChanged.connect(self.apply_position)
        positions_box.addWidget(self.position_choices)
        self.add_position = push("Create a position", self.create_position)
        self.add_position.setObjectName("quiet")
        positions_box.addWidget(self.add_position,alignment=Qt.AlignmentFlag.AlignLeft)
        routines_page = QWidget()
        routines_box = QVBoxLayout(routines_page)
        routines_box.setContentsMargins(0,0,0,0)
        self.routine_choices = SelectionList()
        self.routine_choices.setMaximumHeight(125)
        self.routine_choices.currentItemChanged.connect(self.apply_routine)
        routines_box.addWidget(self.routine_choices)
        routines_box.addWidget(push("Manage routines",lambda:show_page(self.window_owner,PAGE_ROUTINES)))
        self.pick_pages.addWidget(routines_page)
        controls = QHBoxLayout()
        controls.addWidget(self.back_to_actions)
        controls.addWidget(push("Cancel",self.end_edit))
        controls.addStretch()
        self.save_button = push("Save",self.save_action,True)
        self.save_button.setProperty("i18nUserTooltip",True)
        self.save_button.setProperty("i18nUserAccessible",True)
        controls.addWidget(self.save_button)
        choice_box.addLayout(controls)
        choice_box.addStretch()
        picker = QWidget()
        picker_layout = QVBoxLayout(picker)
        choices.setMinimumWidth(540)
        choices.setMaximumWidth(640)
        picker_layout.addWidget(choices, alignment=Qt.AlignmentFlag.AlignCenter)
        self.settings.addWidget(picker)

    def enable_gesture(self, key, kind, checked):
        config = copy.deepcopy(self.window_owner.controller.config)
        config["enabled"][key][kind] = checked
        try:
            self.window_owner.controller.save(config)
        except (ValueError,OSError) as exc:
            self.enable_switches[key,kind].setChecked(not checked)
            self.window_owner.show_error(str(exc))
        self.refresh_enabled()

    def toggle_presses(self, checked=None):
        self.managing = self.manage.isChecked() if checked is None else bool(checked)
        self.manage.setChecked(self.managing)
        self.manage.setText(tr("Done" if self.managing else "Manage presses"))
        self.manage.setIcon(icon("check" if self.managing else "sliders"))
        self.refresh_enabled()

    def refresh_enabled(self):
        managing = getattr(self, "managing", False)
        for (key,kind), (caption, field) in self.gesture_rows.items():
            enabled = self.window_owner.controller.config["enabled"][key][kind]
            toggle = self.enable_switches[key,kind]
            toggle.setChecked(enabled)
            toggle.setVisible(managing)
            # Outside management, disabled presses disappear; while managing, their row stays to re-enable it.
            caption.setVisible(enabled or managing)
            caption.setEnabled(enabled)
            field.setVisible(enabled)

    def edit_action(self, field):
        self.field = field
        self.pending = copy.deepcopy(field.action)
        self.choice_title.setText(tr(field.caption))
        rules = {"short":"On release. With Double enabled, waits up to 300 ms.",
                 "double":"Two presses shorter than 650 ms; second starts within 300 ms.",
                 "long":"On release after 650 ms, before continuous hold starts.",
                 "hold":"Starts at 1.5 s. Volume repeats every 150 ms; video every 400 ms; MyWhoosh arrows stay down."}
        self.timing.setText(rules[field.gesture])
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
        self.fit_stage()

    def show_group(self, group):
        self.active_group = group
        if group == "Routines":
            # Routines has a single action: go straight to choosing the routine.
            self.show_routines()
            return
        self.choices_frame.setMinimumWidth(620 if group in ("Media", "MyWhoosh") else 540)
        self.choices_frame.setMaximumWidth(640)
        self.refresh_usage()
        self.group_title.setText(tr(group))
        for cell in self.option_cells.values():
            self.action_grid.removeWidget(cell)
            cell.hide()
        allowed = [a for a in ACTION_GROUPS[group] if self.field.gesture != "hold" or a in REPEATABLE]
        for index, action in enumerate(allowed):
            cell = self.option_cells[action]
            if group == "MyWhoosh":
                # Gears, then lateral moves, then the three junction buttons on one line,
                # then ERG intensity − / + on the last line.
                if action.startswith("junction_"):
                    row, column, span = 2, ("junction_left", "junction_straight", "junction_right").index(action) * 2, 2
                elif action.startswith("intensity_"):
                    row, column, span = 3, (0 if action == "intensity_down" else 3), 3
                else:
                    row, column, span = index // 2, index % 2 * 3, 3
                self.action_grid.addWidget(cell, row, column, 1, span)
            else:
                columns = 2
                self.action_grid.addWidget(cell,index//columns,index%columns)
            cell.show()
        self.pick_pages.setCurrentIndex(1)
        self.back_to_actions.show()
        self.fit_stage()

    def fit_stage(self):
        page = self.pick_pages.currentWidget()
        if page.layout():
            page.layout().invalidate()
            page.layout().activate()
        self.pick_pages.setFixedHeight(page.sizeHint().height())
        self.choices_frame.updateGeometry()

    def binding_text(self, binding):
        if binding is None:
            return tr("Choose a position")
        if action_id(binding) == "mouse_position":
            point = self.window_owner.controller.config["positions"].get(binding["position_id"])
            return point["name"] if point else tr("Choose a position")
        if action_id(binding) == "routine":
            routine = self.window_owner.controller.config["routines"].get(binding["routine_id"])
            return routine["name"] if routine else tr("Choose a routine")
        return tr(ACTIONS[action_id(binding)][1])

    def uses(self, action, position_id=None, detailed=False):
        found = []
        for key, gestures in self.window_owner.controller.config["buttons"].items():
            for gesture, binding in gestures.items():
                if action_id(binding) != action:
                    continue
                if position_id is not None and binding.get("position_id") != position_id:
                    continue
                found.append((key, gesture) if detailed else
                             ("+" if key == "plus" else key.upper()) + " · " + tr(GESTURE_NAMES[gesture]))
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
        self.rendered_language = language()
        self.choice_title.setText(tr(self.field.caption))
        self.current_assignment.setText(tr("Current action: {action}").format(action=self.binding_text(self.field.action)))
        if self.active_group:
            self.group_title.setText(tr(self.active_group))
        for action, used in self.usage_labels.items():
            used.set_uses(self.uses(action, detailed=True), self.usage_text(action))
        for group, button in self.category_buttons.items():
            allowed = [a for a in ACTION_GROUPS[group] if self.field.gesture != "hold" or a in REPEATABLE]
            button.setText(tr(group))
        self.update_pending()

    def update_pending(self):
        self.save_button.setEnabled(self.pending is not None)
        self.save_button.setAccessibleName(tr("Save") + " · " + self.binding_text(self.pending))

    def apply_choice(self, option):
        action = option.property("action")
        if action == "mouse_position":
            self.pending = copy.deepcopy(self.field.action) if action_id(self.field.action) == "mouse_position" else None
            self.show_positions()
            return
        if action == "routine":
            self.show_routines()
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
            if isinstance(self.pending,dict) and self.pending.get("position_id") == ident:
                self.position_choices.setCurrentItem(item)
        self.position_choices.blockSignals(signals_blocked)
        count = self.position_choices.count()
        self.position_choices.ensurePolished()
        rows = sum(self.position_choices.sizeHintForRow(i) for i in range(min(2,count)))
        self.position_choices.setFixedHeight(max(1,rows+2*self.position_choices.frameWidth()))
        self.position_choices.setVisible(count > 0)
        self.position_hint.setText("Select a saved position." if count else "No saved positions. Create one below.")
        self.position_hint.show()
        self.pick_pages.setCurrentIndex(2)
        self.back_to_actions.show()
        self.add_position.show()
        self.update_pending()
        self.fit_stage()

    def show_routines(self):
        self.routine_choices.blockSignals(True)
        self.routine_choices.clear()
        self.pending = None
        for ident,routine in self.window_owner.controller.config["routines"].items():
            self.routine_choices.addItem(routine["name"])
            item = self.routine_choices.item(self.routine_choices.count()-1)
            item.setData(Qt.ItemDataRole.UserRole,ident)
            if action_id(self.field.action) == "routine" and self.field.action["routine_id"] == ident:
                self.routine_choices.setCurrentItem(item)
                self.pending = copy.deepcopy(self.field.action)
        self.routine_choices.blockSignals(False)
        self.pick_pages.setCurrentIndex(3)
        self.back_to_actions.show()
        self.update_pending()
        self.fit_stage()

    def apply_routine(self, item, _previous=None):
        if item:
            self.pending = {"action":"routine","routine_id":item.data(Qt.ItemDataRole.UserRole)}
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
        field = getattr(self, "field", None)
        if field is not None:
            field.setFocus()


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
        badge.setStyleSheet(f"background:{COLORS[key]};color:{ink};border-radius:8px;font-weight:700")
        grid.addWidget(badge, 0, 0, 4, 1)
        for row,kind in enumerate(GESTURES):
            title = GESTURE_NAMES[kind]
            toggle = GestureCheck(f"{name} · {title}")
            toggle.clicked.connect(lambda checked, k=key, g=kind: self.enable_gesture(k, g, checked))
            self.enable_switches[key, kind] = toggle
            grid.addWidget(toggle, row, 1)
            caption = label("Hold" if kind == "hold" else title, "muted")
            caption.setStyleSheet("font-size:12px")
            grid.addWidget(caption, row, 2)
            field = AssignmentButton(f"{name} · {title}")
            field.gesture = kind
            field.clicked.connect(lambda checked=False, select=field: self.edit_action(select))
            bindings[key, kind] = field
            field.setMinimumHeight(26)
            grid.addWidget(field, row, 3)
            self.gesture_rows[key,kind] = (caption,field)
        grid.setColumnStretch(3, 1)
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
    heading.setSpacing(14)
    from ui_icons import badge
    symbol = {"Mouse positions":"position","Windows":"windows","Routines":"routine"}.get(title)
    if symbol:
        heading.addWidget(badge(symbol))
    heading.addWidget(label(title, "title"), 1)
    if action is not None:
        heading.addWidget(action)
    layout.addLayout(heading)
    if subtitle:
        layout.addWidget(label(subtitle, "muted"))
    return page, layout


PAGE_DASHBOARD, PAGE_CONNECTIONS, _PAGE_RESERVED, PAGE_MOUSE, PAGE_BUTTONS, PAGE_GENERAL, PAGE_CREDITS, PAGE_CONTACT = range(8)
# Controller and MyWhoosh share one Connections page.
PAGE_MYWHOOSH = PAGE_CONTROLLER = PAGE_CONNECTIONS
PAGE_WINDOWS, PAGE_ROUTINES = 8,9
PAGE_SECTIONS = (0, 1, 1, 3, 2, 2, 2, 2, 3, 3)


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
    header.setFixedHeight(64)
    nav = QHBoxLayout(header)
    nav.setContentsMargins(28, 0, 28, 0)
    nav.setSpacing(10)
    mark = ControllerImage("app-mark.png", "Swift Click")
    mark.setFixedSize(30, 30)
    nav.addWidget(mark)
    nav.addWidget(label("Swift Click", "brand"))
    w.version_label = label(f"v{w.app_version}","version")
    w.version_label.setWordWrap(False)
    nav.addWidget(w.version_label, 0, Qt.AlignmentFlag.AlignVCenter)
    nav.addStretch()
    w.pages = QStackedWidget()
    w.nav = [None]*4
    w.last_section_pages = {0: PAGE_DASHBOARD, 1: PAGE_CONTROLLER, 2: PAGE_BUTTONS, 3:PAGE_MOUSE}
    group = QFrame()
    group.setObjectName("navGroup")
    group_row = QHBoxLayout(group)
    group_row.setContentsMargins(4, 4, 4, 4)
    group_row.setSpacing(2)
    nav_icons = {0: "system", 1: "link", 3: "sparkle", 2: "settings"}
    for index, name in ((0,"Dashboard"),(1,"Connections"),(3,"Actions"),(2,"Settings")):
        item = push(name, lambda _=False, i=index: show_section(w, i))
        item.setObjectName("settingsNav" if index == 2 else "nav")
        item.setCheckable(True)
        item.setIcon(icon(nav_icons[index]))
        item.setIconSize(QSize(16,16))
        group_row.addWidget(item)
        w.nav[index] = item
    nav.addWidget(group, 0, Qt.AlignmentFlag.AlignVCenter)
    outer.addWidget(header)
    w.subnav_frame = QFrame()
    w.subnav_frame.setObjectName("subnav")
    subnav = QHBoxLayout(w.subnav_frame)
    subnav.setContentsMargins(32, 6, 32, 6)
    w.subnav = {}
    for target, name in ((PAGE_BUTTONS, "Buttons"),
                         (PAGE_GENERAL, "General"), (PAGE_CREDITS, "Credits"), (PAGE_CONTACT, "Contact"),
                         (PAGE_MOUSE, "Mouse positions"),
                         (PAGE_WINDOWS,"Applications and media"),(PAGE_ROUTINES,"Routines")):
        item = push(name, lambda _=False, i=target: show_page(w, i))
        item.setObjectName("subnavButton")
        item.setCheckable(True)
        subnav.addWidget(item)
        w.subnav[target] = item
    subnav.addStretch()
    outer.addWidget(w.subnav_frame)
    w.recovery_notice = QFrame()
    w.recovery_notice.setObjectName("recoveryNotice")
    recovery_row = QHBoxLayout(w.recovery_notice)
    recovery_row.setContentsMargins(24, 12, 24, 12)
    recovery_row.addWidget(label("Some settings could not be loaded."), 1)
    recovery_row.addWidget(push("Open settings", lambda: show_page(w, PAGE_GENERAL)))
    w.recovery_notice.setVisible(bool(w.controller.config_error))
    outer.addWidget(w.recovery_notice)
    w.destination_choice = push("Choose destination", w.choose_destination)
    w.destination_choice.hide()
    outer.addWidget(w.destination_choice)
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
        from ui_icons import badge
        picture = badge("window" if index == 0 else "controller")
        if index == 0:
            from PySide6.QtGui import QIcon
            picture.set_icon(QIcon(str(Path(__file__).with_name("assets")/"mywhoosh.png")))
        row.addWidget(picture)
        row.addSpacing(10)
        row.addWidget(label(name, size=16), 1)
        state = label("Not connected" if index == 0 else "Not connected")
        state.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(state)
        if index == 0:
            w.open_game_button = push("Open MyWhoosh",lambda:w.launch(w.open_mywhoosh()))
            w.open_game_button.setIcon(icon("open"))
            w.open_game_button.setIconSize(QSize(18,18))
            row.addSpacing(12)
            row.addWidget(w.open_game_button)
        w.dashboard_states.append(state)
        summary_box.addLayout(row)
        if index == 0:
            divider = QFrame()
            divider.setObjectName("separator")
            divider.setFixedHeight(1)
            summary_box.addWidget(divider)
    box.addWidget(summary)
    w.command_status = label("No command sent yet", "muted")
    box.addWidget(w.command_status)
    box.addStretch()
    w.pages.addWidget(page)

    page, box = make_page("Connections")
    # Controller first: it is the device the rider holds.
    surface, content = card()
    content.setContentsMargins(24, 22, 24, 22)
    content.setSpacing(14)
    line = QHBoxLayout()
    line.setSpacing(12)
    from ui_icons import badge
    line.addWidget(badge("controller", 40))
    line.addSpacing(2)
    info = QVBoxLayout()
    info.setSpacing(2)
    info.addWidget(label("Zwift Click V2 · Right", size=16))
    w.ble_status = label("Not connected", "muted")
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
    footer = QHBoxLayout()
    w.received_buttons = label("Button input · waiting for a connection", "muted")
    footer.addWidget(w.received_buttons, 1)
    footer.addWidget(w.maintenance)
    content.addLayout(footer)
    box.addWidget(surface)

    frame, items = card()
    items.setContentsMargins(24, 22, 24, 22)
    items.setSpacing(14)
    line = QHBoxLayout()
    line.setSpacing(12)
    line.addWidget(logo(40))
    line.addSpacing(2)
    info = QVBoxLayout()
    info.setSpacing(2)
    info.addWidget(label("MyWhoosh", size=16))
    w.game_status = label("Not connected", "muted")
    info.addWidget(w.game_status)
    w.route_status = label("", "muted")
    w.route_status.hide()
    info.addWidget(w.route_status)
    line.addLayout(info, 1)
    w.recover_button = push("Restore MyWhoosh link", lambda: w.launch(w.recover_link()))
    w.recover_button.setObjectName("quiet")
    w.recover_button.setToolTip("Restore MyWhoosh link")
    w.start_button = push("Connect", lambda: w.launch(w.start_link()), True)
    w.stop_button = push("Disconnect", lambda: w.launch(w.stop_link()))
    line.addWidget(w.start_button)
    line.addWidget(w.stop_button)
    items.addLayout(line)
    w.game_hint = label("", "muted")
    w.game_hint.hide()
    items.addWidget(w.game_hint)
    items.addWidget(w.recover_button, alignment=Qt.AlignmentFlag.AlignLeft)
    box.addWidget(frame)

    box.addWidget(label("Guides", "eyebrow"))
    w.controller_guide = GuidePanel("controller", CONTROLLER_STEPS, title="Controller guide")
    box.addWidget(w.controller_guide)
    w.game_guide = GuidePanel("mywhoosh", MYWHOOSH_STEPS, title="MyWhoosh guide")
    box.addWidget(w.game_guide)
    trouble = Disclosure("Connection trouble?")
    trouble.body.addWidget(label(
        "<b>Grey LAN:</b> check Direct Connect under Connectivity and allow Bonjour if MyWhoosh asks.<br>"
        "<b>No prompt:</b> start the Swift Click connection, then click the OpenBikeControl handlebar in MyWhoosh.<br>"
        "<b>Two devices:</b> use the same local network. If discovery fails, check the selected network and network permissions.<br>"
        "<b>Connected but not shifting:</b> check the controller, assignments under Settings → Buttons and Virtual Shifting in MyWhoosh."
    ))
    from ui_controls import ChoiceGroup
    w.network = ChoiceGroup()
    w.network.setAccessibleName("Local network used for MyWhoosh")
    w.network_panel = Disclosure("Network and diagnostics")
    w.network_panel.body.addWidget(label("Local network", "muted"))
    w.network_panel.body.addWidget(w.network)
    w.network_refresh = push("Refresh networks", w.load_networks)
    w.network_panel.body.addWidget(w.network_refresh, alignment=Qt.AlignmentFlag.AlignLeft)
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
    # The former controller page slot stays reserved so other page indices keep their meaning.
    w.pages.addWidget(QWidget())

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
    from automation_view import WindowsPage, RoutinesPage
    w.windows_page = WindowsPage(w)
    w.routines_page = RoutinesPage(w)
    w.pages.addWidget(w.windows_page)
    w.pages.addWidget(w.routines_page)
    show_page(w, PAGE_DASHBOARD)


def show_section(w, section):
    show_page(w, w.last_section_pages[section])


def show_page(w, index):
    if index == PAGE_WINDOWS:
        w.windows_page.reload()
    elif index == PAGE_ROUTINES:
        w.routines_page.reload()
    section = PAGE_SECTIONS[index]
    w.last_section_pages[section] = index
    w.pages.setCurrentIndex(index)
    for i, item in enumerate(w.nav):
        item.setChecked(i == section)
    w.subnav_frame.setVisible(any(PAGE_SECTIONS[t] == section for t in w.subnav))
    for target, item in w.subnav.items():
        item.setVisible(PAGE_SECTIONS[target] == section)
        item.setChecked(target == index)


def refresh_ui(w):
    w.destination_choice.setVisible(w.controller.windows.pending_choice is not None)
    w.recover_button.setEnabled(not w.recovering_link and not w.stopping and not w.closing)
    w.command_status.setText(w.controller.last_command or "No command sent yet")
    w.command_status.setStyleSheet("color:" + color("danger" if w.controller.last_command_error else "muted"))
    w.recovery_notice.setVisible(bool(w.controller.config_error))
    if w.routines_page.rendered_language != language():
        w.routines_page.reload()
    if w.windows_page.rendered_language != language():
        w.windows_page.reload()
    if w.windows_page.opening:
        w.windows_page.set_result(w.controller.windows.result)
    if w.routines_page.testing:
        w.routines_page.result.setText(w.controller.windows.result)
    w.open_game_button.setEnabled(not w.opening_game and not w.closing)
    w.open_game_button.setText("Opening…" if w.opening_game else "Open MyWhoosh")
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
        and bool(w.shifter.game_clients())
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
    if connected:
        from controller import ROUTE_BUTTONS
        keyboard = w.controller.config.get("navigation", {}).get("route_via", "network") == "keyboard"
        network = not keyboard and all(w.shifter.supports(b) for b in ROUTE_BUTTONS.values())
        w.route_status.setText("Directions sent through the network link" if network else
                               "Directions sent as A / D keys: keep MyWhoosh in front")
    w.route_status.setVisible(connected)
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
        status_color = color("success" if active else "muted")
        if field.property("statusColor") != status_color:
            field.setStyleSheet(f"color:{status_color};font-weight:500")
            field.setProperty("statusColor", status_color)
    w.editor.set_pressed(status["pressed"])
    if w.editor.settings.currentIndex() == 1 and w.editor.rendered_language != language():
        w.editor.refresh_usage()
        w.editor.update_pending()
        if w.editor.pick_pages.currentIndex() == 2:
            w.editor.show_positions()
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
