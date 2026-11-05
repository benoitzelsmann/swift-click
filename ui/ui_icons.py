"""Small vector interface icons and cached native application icons."""
from PySide6.QtCore import Qt, QRect, QRectF, QPointF, QFileInfo
from PySide6.QtGui import QIconEngine, QIcon, QPixmap, QPainter, QPen, QColor, QPainterPath
from PySide6.QtWidgets import QFileIconProvider, QLabel
from pathlib import PureWindowsPath
from ui_theme import color as theme_color

_CACHE = {}

def application_name(path):
    stem = PureWindowsPath(path).stem
    names = {"msedge": "Edge", "chrome": "Chrome", "firefox": "Firefox", "brave": "Brave",
             "mywhoosh": "MyWhoosh", "mywhooshwin": "MyWhoosh",
             "systemsettings": "Settings", "applicationframehost": "Windows", "explorer": "Explorer"}
    return names.get(stem.casefold(), stem[:40] or "Window")


def _render_icon(name, color):
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
    if name in ("chevron_right", "chevron_down"):
        path = QPainterPath()
        if name == "chevron_right":
            points = [(9, 5), (16, 12), (9, 19)]
        else:
            points = [(5, 9), (12, 16), (19, 9)]
        path.moveTo(*points[0])
        for point in points[1:]:
            path.lineTo(*point)
        painter.drawPath(path)
    elif name in ("window","windows"):
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
    elif name in ("volume_up", "volume_down", "volume_mute"):
        path = QPainterPath(QPointF(3, 9))
        for x, y in ((7, 9), (12, 5), (12, 19), (7, 15), (3, 15), (3, 9)):
            path.lineTo(x, y)
        painter.drawPath(path)
        if name == "volume_mute":
            painter.drawLine(16, 9, 21, 15)
            painter.drawLine(21, 9, 16, 15)
        else:
            painter.drawLine(16, 12, 22, 12)
            if name == "volume_up":
                painter.drawLine(19, 9, 19, 15)
    elif name in ("media_previous", "media_next", "seek_back", "seek_forward", "media_play_pause"):
        if name in ("media_previous", "seek_back"):
            painter.translate(24, 0)
            painter.scale(-1, 1)
        path = QPainterPath(QPointF(5, 5))
        path.lineTo(15, 12)
        path.lineTo(5, 19)
        path.closeSubpath()
        painter.drawPath(path)
        if name == "media_play_pause":
            painter.drawLine(18, 6, 18, 18)
            painter.drawLine(22, 6, 22, 18)
        elif name in ("media_previous", "media_next"):
            painter.drawLine(19, 5, 19, 19)
        else:
            path = QPainterPath(QPointF(14, 5))
            path.lineTo(22, 12)
            path.lineTo(14, 19)
            painter.drawPath(path)
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


class ThemeIconEngine(QIconEngine):
    """Resolve symbol ink at paint time, including icons in existing list items."""
    def __init__(self, name):
        super().__init__()
        self.name = name

    def clone(self):
        return ThemeIconEngine(self.name)

    def paint(self, painter, rect, mode, state):
        ink = theme_color("disabled" if mode == QIcon.Mode.Disabled else "muted")
        _render_icon(self.name, ink).paint(painter, rect, Qt.AlignmentFlag.AlignCenter, QIcon.Mode.Normal, state)

    def pixmap(self, size, mode, state):
        result = QPixmap(size)
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        self.paint(painter, result.rect(), mode, state)
        painter.end()
        return result


def icon(name, color=None):
    return _render_icon(name, color) if color else QIcon(ThemeIconEngine(name))


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
    names = {"mouse_click": "click", "mouse_position": "position", "switch_windows": "windows"}
    if action.startswith(("volume_", "media_", "seek_")):
        return icon(action)
    return icon(names.get(action, "system"))


class IconBadge(QLabel):
    def __init__(self, name, size):
        super().__init__()
        self.picture = icon(name)
        self.setFixedSize(size,size)
        self.setObjectName("iconBadge")

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
