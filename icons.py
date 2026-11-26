from __future__ import annotations

import math
import os
import tempfile

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF


def _pt(x: float, y: float) -> QPointF:
    return QPointF(x, y)


def _line(p: QPainter, x1: float, y1: float, x2: float, y2: float) -> None:
    p.drawLine(_pt(x1, y1), _pt(x2, y2))


def _poly(p: QPainter, *coords: tuple[float, float]) -> None:
    p.drawPolyline(QPolygonF([_pt(x, y) for x, y in coords]))


def _rrect(p: QPainter, x: float, y: float, w: float, h: float, r: float) -> None:
    p.drawRoundedRect(QRectF(x, y, w, h), r, r)


def _star(p: QPainter, cx: float, cy: float, r: float, ri: float) -> None:
    pts = []
    for i in range(8):
        ang = math.pi / 4 * i - math.pi / 2
        rad = r if i % 2 == 0 else ri
        pts.append(_pt(cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    p.drawPolygon(QPolygonF(pts))


def _sparkle(p: QPainter) -> None:
    color = p.pen().color()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    _star(p, 13.5, 10.5, 8.5, 2.2)
    _star(p, 5.8, 18.5, 4.2, 1.2)


def _grid(p: QPainter) -> None:
    for x, y in ((4, 4), (13.5, 4), (4, 13.5), (13.5, 13.5)):
        _rrect(p, x, y, 6.5, 6.5, 1.8)


def _link(p: QPainter) -> None:
    p.translate(12, 12)
    p.rotate(-45)
    _rrect(p, -9.5, -3.6, 11.5, 7.2, 3.6)
    _rrect(p, -2, -3.6, 11.5, 7.2, 3.6)


def _chat(p: QPainter) -> None:
    path = QPainterPath()
    path.addRoundedRect(QRectF(3.5, 4, 17, 12.5), 3.5, 3.5)
    p.drawPath(path)
    _poly(p, (8, 16.5), (8, 20.5), (12.5, 16.5))


def _database(p: QPainter) -> None:
    p.drawEllipse(QRectF(5, 3.5, 14, 5))
    _line(p, 5, 6, 5, 18)
    _line(p, 19, 6, 19, 18)
    p.drawArc(QRectF(5, 8.5, 14, 5), 180 * 16, 180 * 16)
    p.drawArc(QRectF(5, 15.5, 14, 5), 180 * 16, 180 * 16)


def _arrow_right(p: QPainter) -> None:
    _line(p, 4.5, 12, 19.5, 12)
    _poly(p, (13, 5.5), (19.5, 12), (13, 18.5))


def _arrow_left(p: QPainter) -> None:
    _line(p, 19.5, 12, 4.5, 12)
    _poly(p, (11, 5.5), (4.5, 12), (11, 18.5))


def _eye(p: QPainter) -> None:
    path = QPainterPath()
    path.moveTo(2, 12)
    path.quadTo(12, 1.5, 22, 12)
    path.quadTo(12, 22.5, 2, 12)
    p.drawPath(path)
    p.drawEllipse(_pt(12, 12), 3.2, 3.2)


def _eye_off(p: QPainter) -> None:
    _eye(p)
    _line(p, 4, 20, 20, 4)


def _signin(p: QPainter) -> None:
    _poly(p, (14, 4), (19.5, 4), (19.5, 20), (14, 20))
    _line(p, 4, 12, 15.5, 12)
    _poly(p, (10.5, 7), (15.5, 12), (10.5, 17))


def _send(p: QPainter) -> None:
    _poly(p, (3, 11), (21, 3), (14, 21), (11, 13), (3, 11))
    _line(p, 11, 13, 21, 3)


def _clock(p: QPainter) -> None:
    p.drawEllipse(_pt(12, 12), 9, 9)
    _poly(p, (12, 7), (12, 12), (15.5, 14))


def _doc(p: QPainter) -> None:
    _rrect(p, 5, 3, 14, 18, 2.5)
    _line(p, 8.5, 9, 15.5, 9)
    _line(p, 8.5, 13, 15.5, 13)


def _copy(p: QPainter) -> None:
    _rrect(p, 8.5, 8.5, 11.5, 11.5, 2.5)
    _poly(p, (15.5, 8.5), (15.5, 6.5), (13.5, 4), (6.5, 4))
    _poly(p, (6.5, 4), (4, 6.5), (4, 14), (6, 15.5), (8.5, 15.5))


def _download(p: QPainter) -> None:
    _line(p, 12, 4, 12, 15)
    _poly(p, (7, 10.5), (12, 15.5), (17, 10.5))
    _line(p, 5, 20, 19, 20)


def _refresh(p: QPainter) -> None:
    p.drawArc(QRectF(4.5, 4.5, 15, 15), 60 * 16, 270 * 16)
    _poly(p, (19.5, 3.5), (19.5, 8.5), (14.5, 8.5))


def _check(p: QPainter) -> None:
    _poly(p, (5, 12.5), (10, 17.5), (19, 7))


def _mail(p: QPainter) -> None:
    _rrect(p, 3.5, 5.5, 17, 13, 3)
    _poly(p, (4.5, 8), (12, 13.5), (19.5, 8))


def _chevron_down(p: QPainter) -> None:
    _poly(p, (6, 9), (12, 15), (18, 9))


def _chevron_up(p: QPainter) -> None:
    _poly(p, (6, 15), (12, 9), (18, 15))


_DRAWERS = {
    "sparkle": _sparkle,
    "grid": _grid,
    "link": _link,
    "chat": _chat,
    "database": _database,
    "arrow-right": _arrow_right,
    "arrow-left": _arrow_left,
    "eye": _eye,
    "eye-off": _eye_off,
    "signin": _signin,
    "send": _send,
    "clock": _clock,
    "doc": _doc,
    "copy": _copy,
    "download": _download,
    "refresh": _refresh,
    "check": _check,
    "mail": _mail,
    "chevron-down": _chevron_down,
    "chevron-up": _chevron_up,
}


def pixmap(name: str, color: str = "#FFFFFF", size: int = 20) -> QPixmap:
    dpr = 2.0
    pm = QPixmap(int(size * dpr), int(size * dpr))
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.GlobalColor.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(size / 24, size / 24)
    pen = QPen(QColor(color), 1.9)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    _DRAWERS[name](p)
    p.end()
    return pm


def logo_pixmap(size: int = 32) -> QPixmap:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
    pm = QPixmap(path)
    dpr = 2.0
    pm = pm.scaled(int(size * dpr), int(size * dpr), Qt.AspectRatioMode.KeepAspectRatio,
                   Qt.TransformationMode.SmoothTransformation)
    pm.setDevicePixelRatio(dpr)
    return pm


def logo_icon() -> QIcon:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
    return QIcon(path)


def icon(name: str, color: str = "#FFFFFF", size: int = 20, on_color: str | None = None) -> QIcon:
    ic = QIcon()
    ic.addPixmap(pixmap(name, color, size), QIcon.Mode.Normal, QIcon.State.Off)
    ic.addPixmap(pixmap(name, on_color or color, size), QIcon.Mode.Normal, QIcon.State.On)
    return ic


def ensure_style_assets() -> dict[str, str]:
    folder = tempfile.gettempdir()
    assets = {}
    for key, name, color, size in (("check", "check", "#FFFFFF", 14), ("chevron", "chevron-down", "#6B7A99", 14),
                                  ("chevron_up", "chevron-up", "#6B7A99", 14)):
        path = os.path.join(folder, f"utilkit_{key}.png")
        pixmap(name, color, size).save(path, "PNG")
        assets[key] = path.replace("\\", "/")
    return assets
