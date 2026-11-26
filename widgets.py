from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from icons import icon, pixmap
from styles import MONO, MUTED


def spaced(label: QLabel, px: float) -> QLabel:
    font = label.font()
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, px)
    label.setFont(font)
    return label


def mono_label(text: str, color: str = MUTED, size: int = 10) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{color}; font-family:{MONO}; font-size:{size}px;")
    return spaced(lbl, 1.2)


def add_shadow(widget: QWidget, blur: int = 40, alpha: int = 28, dy: int = 12) -> None:
    fx = QGraphicsDropShadowEffect(widget)
    fx.setBlurRadius(blur)
    fx.setOffset(0, dy)
    fx.setColor(QColor(16, 41, 77, alpha))
    widget.setGraphicsEffect(fx)


def scrollable(widget: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setWidget(widget)
    return area


def hline() -> QFrame:
    line = QFrame()
    line.setObjectName("hline")
    line.setFixedHeight(1)
    return line


class PageHeader(QWidget):

    def __init__(self, icon_name: str, title: str, tagline: str, on_back) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(18)

        back = QPushButton("  Back to all tools")
        back.setObjectName("link")
        back.setIcon(icon("arrow-left", MUTED, 14))
        back.setIconSize(QSize(14, 14))
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(on_back)
        outer.addWidget(back, alignment=Qt.AlignmentFlag.AlignLeft)

        row = QHBoxLayout()
        row.setSpacing(16)
        tile = QLabel()
        tile.setObjectName("headerTile")
        tile.setFixedSize(50, 50)
        tile.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tile.setPixmap(pixmap(icon_name, "#FFFFFF", 24))
        row.addWidget(tile)

        texts = QVBoxLayout()
        texts.setSpacing(0)
        t = QLabel(title.upper())
        t.setObjectName("pageTitle")
        spaced(t, 0.8)
        s = QLabel(tagline)
        s.setObjectName("pageTagline")
        texts.addWidget(t)
        texts.addWidget(s)
        row.addLayout(texts)
        row.addStretch(1)
        outer.addLayout(row)


class ToolCard(QFrame):

    clicked = pyqtSignal()

    def __init__(self, icon_name: str, title: str, desc: str, color: str) -> None:
        super().__init__()
        self.setObjectName("toolCard")
        hover = QColor(color).lighter(112).name()
        self.setStyleSheet(
            f"QFrame#toolCard {{ background:{color}; border-radius:26px; }}"
            f"QFrame#toolCard:hover {{ background:{hover}; }}"
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(340)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 30, 32, 26)
        lay.setSpacing(0)

        tile = QLabel()
        tile.setObjectName("toolIconTile")
        tile.setFixedSize(56, 56)
        tile.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tile.setPixmap(pixmap(icon_name, color, 26))
        lay.addWidget(tile, alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch(1)

        t = QLabel(title)
        t.setObjectName("toolTitle")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setWordWrap(True)
        d = QLabel(desc)
        d.setObjectName("toolDesc")
        d.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d.setWordWrap(True)
        lay.addWidget(t)
        lay.addSpacing(8)
        lay.addWidget(d)
        lay.addSpacing(22)

        sep = QFrame()
        sep.setObjectName("toolSep")
        sep.setFixedHeight(1)
        lay.addWidget(sep)
        lay.addSpacing(14)

        foot = QHBoxLayout()
        o = QLabel("Open tool")
        o.setObjectName("toolOpen")
        arrow = QLabel()
        arrow.setPixmap(pixmap("arrow-right", "#FFFFFF", 18))
        foot.addWidget(o)
        foot.addStretch(1)
        foot.addWidget(arrow)
        lay.addLayout(foot)

        for child in (tile, t, d, o, arrow):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class FieldCard(QFrame):

    toggled = pyqtSignal(bool)

    def __init__(self, key: str, title: str, hint: str = "") -> None:
        super().__init__()
        self.key = key
        self.setObjectName("fieldCard")
        self.setProperty("selected", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(60)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(12)

        self.check = QCheckBox()
        self.check.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.check.toggled.connect(self._on_toggled)
        lay.addWidget(self.check)

        col = QVBoxLayout()
        col.setSpacing(1)
        t = QLabel(title)
        t.setObjectName("fieldTitle")
        t.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        col.addWidget(t)
        if hint:
            h = QLabel(hint)
            h.setObjectName("fieldHint")
            h.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            col.addWidget(h)
        lay.addLayout(col, 1)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.check.toggle()

    def isChecked(self) -> bool:
        return self.check.isChecked()

    def setChecked(self, value: bool) -> None:
        self.check.setChecked(value)

    def _on_toggled(self, value: bool) -> None:
        self.setProperty("selected", value)
        self.style().unpolish(self)
        self.style().polish(self)
        self.toggled.emit(value)


class Bubble(QWidget):

    def __init__(self, text: str, outgoing: bool, time_text: str, status: str = "") -> None:
        super().__init__()
        self._time, self._outgoing = time_text, outgoing
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)

        frame = QFrame()
        frame.setObjectName("bubbleOut" if outgoing else "bubbleIn")
        v = QVBoxLayout(frame)
        v.setContentsMargins(14, 10, 14, 8)
        v.setSpacing(4)

        self.text_label = QLabel(text)
        self.text_label.setObjectName("bubbleTextOut" if outgoing else "bubbleTextIn")
        self.text_label.setWordWrap(True)
        self.text_label.setMaximumWidth(300)
        self.text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.meta = QLabel()
        self.meta.setObjectName("metaOut" if outgoing else "metaIn")
        self.meta.setAlignment(Qt.AlignmentFlag.AlignRight)
        v.addWidget(self.text_label)
        v.addWidget(self.meta)
        self.set_status(status)

        if outgoing:
            row.addStretch(1)
            row.addWidget(frame)
        else:
            row.addWidget(frame)
            row.addStretch(1)

    def set_text(self, text: str) -> None:
        self.text_label.setText(text)

    def set_status(self, status: str) -> None:
        self.meta.setText(f"{self._time}  ·  {status}" if status else self._time)
