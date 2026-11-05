"""Small vector interface icons and cached native application icons."""
from PySide6.QtCore import Qt, QRect, QRectF, QPointF, QFileInfo
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QPainterPath
from PySide6.QtWidgets import QFileIconProvider, QLabel

_CACHE = {}


def icon(name, color="#287e68"):
    key = (name,color)
    if key in _CACHE:
        return _CACHE[key]
    pixmap = QPixmap(96,96)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(4,4)
    painter.setPen(QPen(QColor(color),1.6,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if name in ("window","windows"):
        if name == "windows":
            painter.drawRoundedRect(QRectF(3,3,15,13),2,2)
        painter.drawRoundedRect(QRectF(6,7,15,13),2,2)
        painter.drawLine(6,11,21,11)
    elif name in ("mouse","position"):
        painter.drawRoundedRect(QRectF(6,3,12,18),6,6)
        painter.drawLine(12,3,12,10)
        if name == "position":
            painter.drawLine(3,12,7,12)
            painter.drawLine(17,12,21,12)
    elif name == "routine":
        for x,y in ((5,5),(19,12),(5,19)):
            painter.drawEllipse(QPointF(x,y),2,2)
        path = QPainterPath(QPointF(7,5))
        path.cubicTo(17,5,10,12,17,12)
        path.moveTo(17,12)
        path.cubicTo(10,12,17,19,7,19)
        painter.drawPath(path)
    elif name == "switch":
        painter.drawLine(4,7,20,7)
        painter.drawLine(16,3,20,7)
        painter.drawLine(20,7,16,11)
        painter.drawLine(20,17,4,17)
        painter.drawLine(8,13,4,17)
        painter.drawLine(4,17,8,21)
    elif name == "controller":
        painter.drawRoundedRect(QRectF(3,6,18,12),4,4)
        painter.drawLine(6,12,10,12)
        painter.drawLine(8,10,8,14)
        painter.drawEllipse(QPointF(16,11),.7,.7)
        painter.drawEllipse(QPointF(18,14),.7,.7)
    elif name in ("forward","back"):
        painter.translate(24,0) if name == "back" else None
        painter.scale(-1,1) if name == "back" else None
        painter.drawLine(4,12,20,12)
        painter.drawLine(14,6,20,12)
        painter.drawLine(20,12,14,18)
    elif name == "click":
        path = QPainterPath(QPointF(5,3))
        for x,y in ((18,12),(12,13),(9,19),(5,3)):
            path.lineTo(x,y)
        painter.drawPath(path)
    elif name == "open":
        painter.drawRoundedRect(QRectF(3,8,13,13),2,2)
        painter.drawLine(10,14,21,3)
        painter.drawLine(14,3,21,3)
        painter.drawLine(21,3,21,10)
    elif name == "close":
        painter.drawLine(6,6,18,18)
        painter.drawLine(18,6,6,18)
    elif name == "minimize":
        painter.drawLine(4,18,20,18)
        painter.drawLine(12,3,12,13)
        painter.drawLine(8,9,12,13)
        painter.drawLine(16,9,12,13)
    elif name == "clock":
        painter.drawEllipse(QRectF(3,3,18,18))
        painter.drawLine(12,7,12,12)
        painter.drawLine(12,12,16,14)
    elif name == "detect":
        painter.drawEllipse(QRectF(3,3,13,13))
        painter.drawLine(15,15,21,21)
    elif name == "system":
        for x,y in ((3,3),(13,3),(3,13),(13,13)):
            painter.drawRect(QRectF(x,y,8,8))
    elif name == "settings":
        import math
        painter.drawEllipse(QRectF(5,5,14,14))
        painter.drawEllipse(QRectF(9,9,6,6))
        for angle in range(0,360,45):
            a=math.radians(angle)
            painter.drawLine(QPointF(12+7*math.cos(a),12+7*math.sin(a)),QPointF(12+10*math.cos(a),12+10*math.sin(a)))
    else:
        painter.drawEllipse(QRectF(4,4,16,16))
        painter.drawLine(10,8,16,12)
        painter.drawLine(16,12,10,16)
    painter.end()
    result = QIcon(pixmap)
    _CACHE[key] = result
    return result


def application_icon(path):
    key = ("app",path)
    if key not in _CACHE:
        result = QFileIconProvider().icon(QFileInfo(path)) if path else QIcon()
        _CACHE[key] = result if not result.isNull() else icon("window")
    return _CACHE[key]


def action_icon(action):
    if action in ("shift_up","shift_down","whoosh_left","whoosh_right"):
        from pathlib import Path
        return QIcon(str(Path(__file__).with_name("assets")/"mywhoosh.png"))
    if action == "none":
        return QIcon()
    if action == "routine":
        return icon("routine")
    return icon("system","#3278bb")


class IconBadge(QLabel):
    def __init__(self, name, size):
        super().__init__()
        self.picture = icon(name)
        self.setFixedSize(size,size)
        self.setStyleSheet("background:#eaf5ef;border-radius:11px;")

    def set_icon(self, value):
        self.picture = value
        self.update()

    def paintEvent(self,event):
        super().paintEvent(event)
        painter = QPainter(self)
        side = 28
        self.picture.paint(painter,QRect((self.width()-side)//2,(self.height()-side)//2,side,side))


def badge(name, size=42):
    return IconBadge(name,size)
