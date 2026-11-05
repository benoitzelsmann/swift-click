from ui_theme import color
"""Accessible, reorderable routine nodes with painted connectors."""
import copy
from PySide6.QtCore import Qt,QSize,QPointF,QRect,QMimeData,Signal
from PySide6.QtGui import QColor,QPainter,QPen,QPolygonF,QFont,QDrag
from PySide6.QtWidgets import QStyledItemDelegate,QAbstractItemView,QApplication
from ui_controls import SelectionList,KeyboardButton
from settings import STEP_ACTIONS,step_problem
from i18n import tr
from ui_icons import icon,action_icon

SYMBOLS = {"open":"open","activate":"window","close":"close","minimize":"minimize",
           "switch":"switch","click":"click","seek_back":"back","seek_forward":"forward","wait":"clock"}
ACTION_MIME = "application/x-swiftclick-action"


class ActionChoice(KeyboardButton):
    """An action supports both a normal click and a drag into the sequence."""
    def __init__(self, text, action):
        super().__init__(text)
        self.action = action
        self.press_position = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mousePressEvent(self, event):
        self.press_position = event.position().toPoint() if event.button() == Qt.MouseButton.LeftButton else None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.press_position is not None and event.buttons() & Qt.MouseButton.LeftButton and (event.position().toPoint()-self.press_position).manhattanLength() >= QApplication.startDragDistance():
            self.press_position = None
            self.setDown(False)
            data = QMimeData()
            data.setData(ACTION_MIME,self.action.encode("ascii"))
            drag = QDrag(self)
            drag.setMimeData(data)
            drag.setPixmap(self.grab())
            drag.setHotSpot(event.position().toPoint())
            drag.exec(Qt.DropAction.CopyAction)
            return
        super().mouseMoveEvent(event)


def step_text(step, cfg):
    if step["action"] == "wait":
        target = tr("{seconds} seconds").format(seconds=step["seconds"])
    else:
        target = cfg["windows"].get(step.get("window_id"),{}).get("name",tr("Choose a window"))
        if step["action"] == "click":
            target += " · " + cfg["positions"].get(step.get("position_id"),{}).get("name",tr("Choose a position"))
        elif step["action"] == "switch":
            target += " ↔ " + cfg["windows"].get(step.get("other_window_id"),{}).get("name",tr("Choose a window"))
    return tr(STEP_ACTIONS[step["action"]]),target


class FlowDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        return QSize(290,90)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect.adjusted(42,4,-4,-14)
        center = option.rect.left()+18
        mid = rect.center().y()
        painter.setPen(QPen(QColor(color("strong_border")),2))
        if index.row():
            painter.drawLine(center,option.rect.top(),center,mid-16)
            painter.setBrush(QColor(color("strong_border")))
            painter.drawPolygon(QPolygonF([QPointF(center-4,mid-21),QPointF(center+4,mid-21),QPointF(center,mid-16)]))
        if index.row() < index.model().rowCount()-1:
            painter.drawLine(center,mid+15,center,option.rect.bottom()+1)
        view = self.parent()
        selected = view.currentRow() == index.row()
        step = index.data(Qt.ItemDataRole.UserRole)
        cfg = view.config()
        problem = step_problem(step,cfg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color("accent") if selected else color("subtle")))
        number_rect = QRect(center-14,mid-14,28,28)
        painter.drawEllipse(number_rect)
        font = painter.font()
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        font.setPixelSize(13)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(color("on_accent") if selected else color("muted")))
        painter.drawText(number_rect,Qt.AlignmentFlag.AlignCenter,str(index.row()+1))
        painter.setPen(QPen(QColor(color("danger") if problem else color("focus") if selected else color("border")),2 if selected else 1))
        painter.setBrush(QColor(color("selection") if selected else color("surface")))
        painter.drawRoundedRect(rect,10,10)
        symbol_rect = QRect(rect.left()+12,rect.top()+12,22,22)
        icon(SYMBOLS[step["action"]],color("danger") if problem else color("focus")).paint(painter,symbol_rect)
        target = cfg["windows"].get(step.get("window_id"),{})
        if step["action"] != "wait":
            logo = action_icon("shift_up" if "mywhoosh" in target.get("path","").casefold() else "mouse_click")
            logo.paint(painter,QRect(rect.right()-29,rect.top()+12,18,18))
        title,target = step_text(step,cfg)
        font.setPixelSize(15)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(color("text")))
        text_rect = rect.adjusted(44,8,-36,-35)
        painter.drawText(text_rect,Qt.AlignmentFlag.AlignVCenter,painter.fontMetrics().elidedText(title,Qt.TextElideMode.ElideRight,text_rect.width()))
        font.setPixelSize(13)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor(color("danger") if problem else color("muted")))
        text_rect = rect.adjusted(14,38,-12,-10)
        text = tr(problem) if problem else target
        painter.drawText(text_rect,Qt.AlignmentFlag.AlignVCenter,painter.fontMetrics().elidedText(text,Qt.TextElideMode.ElideRight,text_rect.width()))
        painter.restore()


class FlowList(SelectionList):
    actionDropped = Signal(str,int)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.drop_row = None
        self.setItemDelegate(FlowDelegate(self))
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(False)
        self.setAutoScroll(True)
        self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAccessibleName("Routine diagram")
        self.setStyleSheet("QListWidget {background:transparent;border:0;padding:0;} QListWidget::item {padding:0;margin:0;}")

    def steps(self):
        return [copy.deepcopy(self.item(i).data(Qt.ItemDataRole.UserRole)) for i in range(self.count())]

    def set_steps(self, steps):
        self.clear()
        for step in steps:
            self.append(step)

    def append(self, step):
        self.insert_step(self.count(),step)

    def insert_step(self, row, step):
        self.insertItem(row,"")
        self.item(row).setFlags(self.item(row).flags() & ~Qt.ItemFlag.ItemIsDropEnabled)
        self.set_step(row,step)

    def insertion_row(self, position):
        index = self.indexAt(position)
        if not index.isValid():
            return self.count()
        return index.row() + int(position.y() >= self.visualRect(index).center().y())

    def is_action_drop(self, event):
        return isinstance(event.source(),ActionChoice) and event.source().action in STEP_ACTIONS and event.mimeData().hasFormat(ACTION_MIME)

    def dragEnterEvent(self, event):
        if self.is_action_drop(event) and self.count() < 32:
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        elif event.source() is self:
            super().dragEnterEvent(event)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if self.is_action_drop(event) and self.count() < 32:
            self.drop_row = self.insertion_row(event.position().toPoint())
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            self.viewport().update()
        elif event.source() is self:
            super().dragMoveEvent(event)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.drop_row = None
        super().dragLeaveEvent(event)
        self.viewport().update()

    def dropEvent(self, event):
        if self.is_action_drop(event) and self.count() < 32:
            row = self.insertion_row(event.position().toPoint())
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            self.drop_row = None
            self.actionDropped.emit(event.source().action,row)
        elif event.source() is self:
            super().dropEvent(event)
        else:
            event.ignore()
        self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.drop_row is not None:
            y = self.visualItemRect(self.item(self.drop_row)).top() if self.drop_row < self.count() else self.visualItemRect(self.item(self.count()-1)).bottom()+1 if self.count() else 4
            painter = QPainter(self.viewport())
            painter.setPen(QPen(QColor(color("focus")),3))
            painter.drawLine(42,y,self.viewport().width()-5,y)

    def set_step(self, row, step):
        item = self.item(row)
        item.setData(Qt.ItemDataRole.UserRole,copy.deepcopy(step))
        item.setText(" · ".join(step_text(step,self.config())))
        self.viewport().update()
