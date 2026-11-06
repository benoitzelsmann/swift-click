"""Small vector interface icons and cached native application icons."""
from PySide6.QtCore import Qt, QRect, QRectF, QPointF, QFileInfo, QSize
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
    painter.setPen(QPen(QColor(color),1.7,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
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
        # One continuous gear outline: six rounded teeth around a hub.
        import math
        path = QPainterPath()
        teeth, outer, inner = 6, 9.6, 7.0
        for i in range(teeth * 4):
            step = i % 4
            radius = outer if step in (1, 2) else inner
            angle = math.radians(i * 360 / (teeth * 4) - 90 + 360 / (teeth * 8))
            point = QPointF(12 + radius * math.cos(angle), 12 + radius * math.sin(angle))
            path.moveTo(point) if i == 0 else path.lineTo(point)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawEllipse(QPointF(12,12),3,3)
    elif name == "plus":
        painter.drawLine(12,5,12,19)
        painter.drawLine(5,12,19,12)
    elif name == "minus":
        painter.drawLine(5,12,19,12)
    elif name == "chevron_up":
        path = QPainterPath(QPointF(5,15))
        path.lineTo(12,8)
        path.lineTo(19,15)
        painter.drawPath(path)
    elif name in ("arrow_left","arrow_right"):
        if name == "arrow_right":
            painter.translate(24,0)
            painter.scale(-1,1)
        painter.drawLine(5,12,19,12)
        painter.drawLine(11,6,5,12)
        painter.drawLine(5,12,11,18)
    elif name in ("turn_left","turn_right"):
        # Junction arrows as MyWhoosh draws them: up the stem, then a turn.
        if name == "turn_right":
            painter.translate(24,0)
            painter.scale(-1,1)
        path = QPainterPath(QPointF(16,20))
        path.lineTo(16,12)
        path.quadTo(16,8,12,8)
        path.lineTo(5,8)
        painter.drawPath(path)
        painter.drawLine(9,4,5,8)
        painter.drawLine(5,8,9,12)
    elif name == "check":
        path = QPainterPath(QPointF(5,12.5))
        path.lineTo(10,17.5)
        path.lineTo(19,7)
        painter.drawPath(path)
    elif name == "edit":
        path = QPainterPath(QPointF(15,5))
        for x,y in ((19,9),(9,19),(4.5,19.5),(5,15),(15,5)):
            path.lineTo(x,y)
        painter.drawPath(path)
        painter.drawLine(13,7,17,11)
    elif name == "trash":
        painter.drawLine(4,7,20,7)
        painter.drawLine(10,4,14,4)
        path = QPainterPath(QPointF(6,7))
        for x,y in ((7,20),(17,20),(18,7)):
            path.lineTo(x,y)
        painter.drawPath(path)
        painter.drawLine(10,11,10,16)
        painter.drawLine(14,11,14,16)
    elif name == "play":
        path = QPainterPath(QPointF(8,5))
        path.lineTo(19,12)
        path.lineTo(8,19)
        path.closeSubpath()
        painter.drawPath(path)
    elif name == "stop":
        painter.drawRoundedRect(QRectF(6,6,12,12),2.5,2.5)
    elif name == "eye":
        path = QPainterPath(QPointF(2.5,12))
        path.cubicTo(6,5.5,18,5.5,21.5,12)
        path.cubicTo(18,18.5,6,18.5,2.5,12)
        painter.drawPath(path)
        painter.drawEllipse(QPointF(12,12),3,3)
    elif name in ("refresh","reset"):
        if name == "reset":
            painter.translate(24,0)
            painter.scale(-1,1)
        painter.drawArc(QRectF(4.5,4.5,15,15),70*16,290*16)
        path = QPainterPath(QPointF(14.5,2.5))
        path.lineTo(15.5,6.2)
        path.lineTo(11.8,7.4)
        painter.drawPath(path)
    elif name in ("link","unlink"):
        painter.save()
        painter.translate(12,12)
        painter.rotate(-45)
        painter.drawRoundedRect(QRectF(-10,-3.5,9,7),3.5,3.5)
        painter.drawRoundedRect(QRectF(1,-3.5,9,7),3.5,3.5)
        if name == "link":
            painter.drawLine(QPointF(-3,0),QPointF(3,0))
        painter.restore()
        if name == "unlink":
            painter.drawLine(4,4,20,20)
    elif name == "mail":
        painter.drawRoundedRect(QRectF(3,5.5,18,13),2.5,2.5)
        path = QPainterPath(QPointF(4,7))
        path.lineTo(12,13)
        path.lineTo(20,7)
        painter.drawPath(path)
    elif name == "globe":
        painter.drawEllipse(QRectF(3,3,18,18))
        painter.drawEllipse(QRectF(8,3,8,18))
        painter.drawLine(QPointF(3.5,9),QPointF(20.5,9))
        painter.drawLine(QPointF(3.5,15),QPointF(20.5,15))
    elif name == "community":
        painter.drawEllipse(QRectF(6,4,6,6))
        path = QPainterPath(QPointF(3,19))
        path.cubicTo(3,14.5,6,13,9,13)
        path.cubicTo(12,13,15,14.5,15,19)
        painter.drawPath(path)
        painter.drawEllipse(QRectF(14,6,5,5))
        side = QPainterPath(QPointF(16,13.2))
        side.cubicTo(19,13,21,14.5,21,18)
        painter.drawPath(side)
    elif name == "bug":
        painter.drawRoundedRect(QRectF(7.5,7,9,13),4.5,4.5)
        painter.drawLine(12,11,12,20)
        for y in (10,14,18):
            painter.drawLine(QPointF(3.5,y),QPointF(7.5,y))
            painter.drawLine(QPointF(16.5,y),QPointF(20.5,y))
        painter.drawLine(9,7,8,4)
        painter.drawLine(15,7,16,4)
    elif name == "idea":
        path = QPainterPath(QPointF(9,16))
        path.cubicTo(9,13,5.5,12,5.5,8.5)
        path.cubicTo(5.5,1.5,18.5,1.5,18.5,8.5)
        path.cubicTo(18.5,12,15,13,15,16)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(9.5,19,14.5,19)
        painter.drawLine(10.5,21.5,13.5,21.5)
    elif name in ("export","import"):
        painter.drawLine(4,15,4,20)
        painter.drawLine(4,20,20,20)
        painter.drawLine(20,20,20,15)
        painter.drawLine(12,3,12,15)
        if name == "export":
            painter.drawLine(7,8,12,3)
            painter.drawLine(12,3,17,8)
        else:
            painter.drawLine(7,10,12,15)
            painter.drawLine(12,15,17,10)
    elif name == "copy":
        painter.drawRoundedRect(QRectF(8,8,12,12),2.5,2.5)
        path = QPainterPath(QPointF(16,8))
        for x,y in ((16,4),(4,4),(4,16),(8,16)):
            path.lineTo(x,y)
        painter.drawPath(path)
    elif name == "code":
        path = QPainterPath(QPointF(8,7))
        path.lineTo(3,12)
        path.lineTo(8,17)
        path.moveTo(16,7)
        path.lineTo(21,12)
        path.lineTo(16,17)
        painter.drawPath(path)
        painter.drawLine(14,4,10,20)
    elif name == "document":
        path = QPainterPath(QPointF(14,3))
        for x,y in ((6,3),(6,21),(18,21),(18,7),(14,3),(14,7),(18,7)):
            path.lineTo(x,y)
        painter.drawPath(path)
        painter.drawLine(9,12,15,12)
        painter.drawLine(9,16,15,16)
    elif name in ("arrow_up","arrow_down"):
        if name == "arrow_down":
            painter.translate(0,24)
            painter.scale(1,-1)
        painter.drawLine(12,5,12,19)
        painter.drawLine(6,11,12,5)
        painter.drawLine(12,5,18,11)
    elif name == "target":
        painter.drawEllipse(QPointF(12,12),8,8)
        painter.drawEllipse(QPointF(12,12),2.5,2.5)
        for a,b,c,d in ((12,1.5,12,5),(12,19,12,22.5),(1.5,12,5,12),(19,12,22.5,12)):
            painter.drawLine(QPointF(a,b),QPointF(c,d))
    elif name == "sliders":
        for y,x in ((7,15),(17,9)):
            painter.drawLine(QPointF(3.5,y),QPointF(20.5,y))
            painter.setBrush(QColor(color))
            painter.drawEllipse(QPointF(x,y),2.4,2.4)
            painter.setBrush(Qt.BrushStyle.NoBrush)
    elif name == "update":
        painter.drawEllipse(QPointF(12,12),9,9)
        painter.drawLine(12,7,12,16)
        painter.drawLine(QPointF(8.5,12.5),QPointF(12,16))
        painter.drawLine(QPointF(12,16),QPointF(15.5,12.5))
    elif name == "info":
        painter.drawEllipse(QPointF(12,12),9,9)
        painter.drawLine(12,11,12,17)
        painter.setBrush(QColor(color))
        painter.drawEllipse(QPointF(12,7.6),.6,.6)
    elif name == "sparkle":
        path = QPainterPath(QPointF(12,3))
        path.cubicTo(12.5,9,15,11.5,21,12)
        path.cubicTo(15,12.5,12.5,15,12,21)
        path.cubicTo(11.5,15,9,12.5,3,12)
        path.cubicTo(9,11.5,11.5,9,12,3)
        painter.drawPath(path)
    elif name == "bike":
        painter.drawEllipse(QPointF(6,16),4,4)
        painter.drawEllipse(QPointF(18,16),4,4)
        path = QPainterPath(QPointF(6,16))
        for x,y in ((10,9),(16,9),(18,16)):
            path.lineTo(x,y)
        path.moveTo(10,9)
        path.lineTo(12.5,16)
        path.lineTo(6,16)
        path.moveTo(9,6.5)
        path.lineTo(12,6.5)
        path.moveTo(16,9)
        path.lineTo(15,5.5)
        path.lineTo(17.5,5.5)
        painter.drawPath(path)
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
    def __init__(self, name, role="muted"):
        super().__init__()
        self.name = name
        self.role = role

    def clone(self):
        return ThemeIconEngine(self.name, self.role)

    def paint(self, painter, rect, mode, state):
        ink = theme_color("disabled" if mode == QIcon.Mode.Disabled else self.role)
        _render_icon(self.name, ink).paint(painter, rect, Qt.AlignmentFlag.AlignCenter, QIcon.Mode.Normal, state)

    def pixmap(self, size, mode, state):
        result = QPixmap(size)
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        self.paint(painter, result.rect(), mode, state)
        painter.end()
        return result


def icon(name, color=None, role="muted"):
    return _render_icon(name, color) if color else QIcon(ThemeIconEngine(name, role))


def application_icon(path):
    key = ("app",path)
    if key not in _CACHE:
        result = QFileIconProvider().icon(QFileInfo(path)) if path else QIcon()
        _CACHE[key] = result if not result.isNull() else icon("window")
    return _CACHE[key]


def action_icon(action):
    if action in ("shift_up","shift_down","whoosh_left","whoosh_right","junction_left","junction_straight","junction_right",
                  "intensity_down","intensity_up"):
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
        self.picture = icon(name, role="accent")
        self.setFixedSize(size,size)
        self.setObjectName("iconBadge")

    def set_icon(self, value):
        self.picture = value
        self.update()

    def paintEvent(self,event):
        super().paintEvent(event)
        painter = QPainter(self)
        side = min(26, self.width()-14)
        self.picture.paint(painter,QRect((self.width()-side)//2,(self.height()-side)//2,side,side))


def badge(name, size=42):
    return IconBadge(name,size)


def site_icon(site):
    """Small recognisable mark for a known streaming site; a globe for any other site."""
    key = ("site", site)
    if key in _CACHE:
        return _CACHE[key]
    if site not in ("YouTube", "Netflix", "Spotify", "Deezer", "Twitch"):
        return icon("globe", role="accent")
    pixmap = QPixmap(96, 96)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(4, 4)
    painter.setPen(Qt.PenStyle.NoPen)
    if site == "YouTube":
        painter.setBrush(QColor("#ff0000"))
        painter.drawRoundedRect(QRectF(1, 5, 22, 15), 4.5, 4.5)
        painter.setBrush(QColor("#ffffff"))
        painter.drawPolygon([QPointF(10, 9), QPointF(16, 12.5), QPointF(10, 16)])
    elif site == "Netflix":
        painter.setBrush(QColor("#141414"))
        painter.drawRoundedRect(QRectF(2, 2, 20, 20), 4, 4)
        painter.setBrush(QColor("#e50914"))
        painter.drawRect(QRectF(7, 5, 3, 14))
        painter.drawRect(QRectF(14, 5, 3, 14))
        painter.drawPolygon([QPointF(7, 5), QPointF(10, 5), QPointF(17, 19), QPointF(14, 19)])
    elif site == "Spotify":
        painter.setBrush(QColor("#1ed760"))
        painter.drawEllipse(QRectF(1.5, 1.5, 21, 21))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for y, width, half in ((9, 2.4, 6.5), (12.8, 2, 5.5), (16.2, 1.6, 4.5)):
            painter.setPen(QPen(QColor("#121212"), width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            path = QPainterPath(QPointF(12 - half, y))
            path.quadTo(12, y - 2.4, 12 + half, y + .8)
            painter.drawPath(path)
    elif site == "Deezer":
        painter.setBrush(QColor("#a238ff"))
        painter.drawRoundedRect(QRectF(2, 2, 20, 20), 5, 5)
        painter.setBrush(QColor("#ffffff"))
        for x, top in ((5, 12), (9.5, 9), (14, 6), (18.5 - 1, 10)):
            painter.drawRect(QRectF(x, top, 3, 18 - top))
    else:  # Twitch
        painter.setBrush(QColor("#9146ff"))
        painter.drawPolygon([QPointF(4, 2), QPointF(21, 2), QPointF(21, 14), QPointF(16, 19), QPointF(12, 19),
                             QPointF(9, 22), QPointF(9, 19), QPointF(4, 19)])
        painter.setBrush(QColor("#ffffff"))
        painter.drawRect(QRectF(11, 6, 2, 6))
        painter.drawRect(QRectF(15.5, 6, 2, 6))
    painter.end()
    _CACHE[key] = QIcon(pixmap)
    return _CACHE[key]


def paired_icon(first, second=None, side=30, gap=6):
    """Two icons side by side (browser, then site), or one at the same left position."""
    ratio = 2
    pixmap = QPixmap((side * 2 + gap) * ratio, side * ratio)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    full = side * ratio
    # QIcon.paint never enlarges a small native icon; draw a pixmap scaled to the slot instead.
    painter.drawPixmap(QRect(0, 0, full, full), first.pixmap(QSize(full, full)))
    if second is not None:
        inset = full // 8
        painter.drawPixmap(QRect((side + gap) * ratio + inset, inset, full - 2 * inset, full - 2 * inset),
                           second.pixmap(QSize(full, full)))
    painter.end()
    pixmap.setDevicePixelRatio(ratio)
    return QIcon(pixmap)
