"""Accessible, reorderable routine nodes with painted connectors."""
import copy
from PySide6.QtCore import Qt,QSize,QPointF
from PySide6.QtGui import QColor,QPainter,QPen,QPolygonF
from PySide6.QtWidgets import QStyledItemDelegate,QAbstractItemView
from ui_controls import SelectionList
from settings import STEP_ACTIONS,step_problem
from i18n import tr
from ui_icons import icon

SYMBOLS = {"open":"open","activate":"window","close":"close","minimize":"minimize",
           "switch":"switch","click":"click","seek_back":"back","seek_forward":"forward","wait":"clock"}


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
        return QSize(270,88)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect.adjusted(4,9,-5,-12)
        center = rect.center().x()
        painter.setPen(QPen(QColor("#b7cfc4"),1.5))
        if index.row():
            painter.drawLine(center,option.rect.top(),center,rect.top()-3)
            painter.setBrush(QColor("#86ae9b"))
            painter.drawPolygon(QPolygonF([QPointF(center-3,rect.top()-6),QPointF(center+3,rect.top()-6),QPointF(center,rect.top()-2)]))
        if index.row() < index.model().rowCount()-1:
            painter.drawLine(center,rect.bottom(),center,option.rect.bottom()+1)
        view = self.parent()
        selected = view.currentRow() == index.row()
        step = index.data(Qt.ItemDataRole.UserRole)
        cfg = view.config()
        problem = step_problem(step,cfg)
        painter.setPen(QPen(QColor("#bd6b54" if problem else "#67a88c" if selected else "#dce6e1"),1.3))
        painter.setBrush(QColor("#ecf6f1" if selected else "#ffffff"))
        painter.drawRoundedRect(rect,9,9)
        symbol_rect = rect.adjusted(12,19,0,0)
        symbol_rect.setSize(QSize(26,26))
        icon(SYMBOLS[step["action"]],"#a74f3c" if problem else "#287e68").paint(painter,symbol_rect)
        title,target = step_text(step,cfg)
        font = painter.font()
        font.setPixelSize(13)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#18202b"))
        text_rect = rect.adjusted(48,10,-10,-30)
        painter.drawText(text_rect,Qt.AlignmentFlag.AlignVCenter,painter.fontMetrics().elidedText(str(index.row()+1)+" · "+title,Qt.TextElideMode.ElideRight,text_rect.width()))
        font.setPixelSize(12)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#a74f3c" if problem else "#66756e"))
        text_rect = rect.adjusted(48,34,-10,-8)
        text = tr(problem) if problem else target
        painter.drawText(text_rect,Qt.AlignmentFlag.AlignVCenter,painter.fontMetrics().elidedText(text,Qt.TextElideMode.ElideRight,text_rect.width()))
        painter.restore()


class FlowList(SelectionList):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setItemDelegate(FlowDelegate(self))
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
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
        self.addItem("")
        self.set_step(self.count()-1,step)

    def set_step(self, row, step):
        item = self.item(row)
        item.setData(Qt.ItemDataRole.UserRole,copy.deepcopy(step))
        item.setText(" · ".join(step_text(step,self.config())))
        self.viewport().update()
