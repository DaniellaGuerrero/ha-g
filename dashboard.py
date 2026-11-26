from __future__ import annotations

import csv
import math
import re
from datetime import datetime

from PyQt6.QtCore import QDateTime, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView, QAbstractSpinBox, QApplication, QButtonGroup, QCheckBox,
    QComboBox, QDateTimeEdit, QDialog, QDialogButtonBox, QFileDialog, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy,
    QSpinBox, QStackedWidget, QTableWidget, QTableWidgetItem, QToolButton,
    QVBoxLayout, QWidget,
)

import api_client
import config_store
from api_client import DATA_FIELDS, MAX_RECORDS, MIN_RECORDS, EmailConfig, SmsConfig
from database import Database, DatabaseError, User
from icons import icon, logo_icon, logo_pixmap, pixmap
from styles import BLUE, INDIGO, MUTED, NAVY, TEAL
from widgets import (
    Bubble, FieldCard, PageHeader, ToolCard, add_shadow, hline, mono_label, scrollable,
)
from workers import run_in_background

PAGE_HOME, PAGE_LINKS, PAGE_MESSAGES, PAGE_DATA = range(4)


def _page_frame() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("pageRoot")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(56, 28, 56, 80)
    lay.setSpacing(0)
    return frame, lay


def _card() -> tuple[QFrame, QVBoxLayout]:
    card = QFrame()
    card.setObjectName("card")
    add_shadow(card, blur=36, alpha=22, dy=10)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(32, 28, 32, 28)
    lay.setSpacing(0)
    return card, lay


class HomePage(QFrame):
    open_tool = pyqtSignal(int)

    def __init__(self, user: User) -> None:
        super().__init__()
        self.setObjectName("pageRoot")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(56, 24, 56, 80)
        lay.setSpacing(24)

        first = user.username.split()[0] if user.username.split() else user.username
        welcome = QLabel(f"Welcome, {first}.")
        welcome.setObjectName("welcome")
        lay.addWidget(welcome)

        row = QHBoxLayout()
        row.setSpacing(24)
        cards = [
            ("link", "URL Shortener", "Turn long URLs into clean, shareable links.", NAVY, PAGE_LINKS),
            ("chat", "SMS & Email", "Text, email, or both, with a live chat preview.", INDIGO, PAGE_MESSAGES),
            ("database", "Fake Data Generator", "Create realistic data for tests and prototypes.", TEAL, PAGE_DATA),
        ]
        for ic, title, desc, color, target in cards:
            card = ToolCard(ic, title, desc, color)
            card.clicked.connect(lambda t=target: self.open_tool.emit(t))
            row.addWidget(card, 1)
        lay.addLayout(row)
        lay.addStretch(1)


class LinksPage(QFrame):
    def __init__(self, go_home) -> None:
        super().__init__()
        self.setObjectName("pageRoot")
        self._short_url = ""
        lay = QVBoxLayout(self)
        lay.setContentsMargins(56, 28, 56, 80)
        lay.setSpacing(22)
        lay.addWidget(PageHeader("link", "URL Shortener", "Make every link easier to share.", go_home))

        card, c = _card()
        c.setContentsMargins(42, 38, 42, 38)
        label = QLabel("Paste your long URL")
        label.setObjectName("fieldLabel")
        c.addWidget(label)
        c.addSpacing(14)

        row = QHBoxLayout()
        row.setSpacing(0)
        self.url_input = QLineEdit()
        self.url_input.setObjectName("joinLeft")
        self.url_input.setPlaceholderText("https://example.com/your/very/long/link")
        self.url_input.setMinimumHeight(54)
        self.shorten_btn = QPushButton("Shorten link  ")
        self.shorten_btn.setObjectName("joinRight")
        self.shorten_btn.setIcon(icon("arrow-right", "#FFFFFF", 18))
        self.shorten_btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.shorten_btn.setMinimumHeight(54)
        self.shorten_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        row.addWidget(self.url_input, 1)
        row.addWidget(self.shorten_btn)
        c.addLayout(row)
        c.addSpacing(20)

        box = QFrame()
        box.setObjectName("resultBox")
        b = QHBoxLayout(box)
        b.setContentsMargins(22, 16, 22, 16)
        col = QVBoxLayout()
        col.setSpacing(4)
        col.addWidget(mono_label("YOUR SHORT LINK"))
        self.result = QLabel("Your new link will appear here")
        self.result.setObjectName("resultValue")
        self.result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        col.addWidget(self.result)
        b.addLayout(col, 1)
        self.copy_btn = QPushButton("  Copy")
        self.copy_btn.setObjectName("copy")
        self.copy_btn.setIcon(icon("copy", MUTED, 16))
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setEnabled(False)
        b.addWidget(self.copy_btn)
        c.addWidget(box)
        lay.addWidget(card)
        lay.addStretch(1)

        self.shorten_btn.clicked.connect(self._shorten)
        self.url_input.returnPressed.connect(self._shorten)
        self.copy_btn.clicked.connect(self._copy)

    def _shorten(self) -> None:
        if not self.shorten_btn.isEnabled():
            return
        self.shorten_btn.setEnabled(False)
        self.shorten_btn.setText("Shortening...  ")
        run_in_background(
            api_client.shorten_url, self.url_input.text(),
            on_success=self._on_success, on_error=self._on_error,
        )

    def _reset_button(self) -> None:
        self.shorten_btn.setEnabled(True)
        self.shorten_btn.setText("Shorten link  ")

    def _on_success(self, short: str) -> None:
        self._reset_button()
        self._short_url = short
        self.result.setText(short)
        self.result.setObjectName("resultValueSet")
        self.result.style().unpolish(self.result)
        self.result.style().polish(self.result)
        self.copy_btn.setEnabled(True)

    def _on_error(self, message: str) -> None:
        self._reset_button()
        QMessageBox.warning(self, "Couldn't shorten link", message)

    def _copy(self) -> None:
        if not self._short_url:
            return
        QApplication.clipboard().setText(self._short_url)
        self.copy_btn.setText("  Copied!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText("  Copy"))


COUNTRY_CODES = [
    ("US", "+1"), ("CA", "+1"), ("GB", "+44"), ("AU", "+61"), ("PH", "+63"),
    ("IN", "+91"), ("DE", "+49"), ("FR", "+33"), ("SG", "+65"), ("JP", "+81"),
]
MAX_SMS_CHARS = 320
COST_PER_PART = 0.45


def build_e164(code: str, raw: str) -> str:
    raw = raw.strip()
    digits = re.sub(r"\D", "", raw)
    if not raw.startswith("+"):
        digits = code.lstrip("+") + digits.lstrip("0")
    if not 8 <= len(digits) <= 15:
        raise ValueError("Please enter a valid phone number.")
    return "+" + digits


def sms_parts(text: str) -> int:
    if not text:
        return 0
    single, multi = (160, 153) if text.isascii() else (70, 67)
    return 1 if len(text) <= single else math.ceil(len(text) / multi)


class MessagesPage(QFrame):
    def __init__(self, user: User, db: Database, go_home) -> None:
        super().__init__()
        self.setObjectName("pageRoot")
        self.user, self.db = user, db
        self._preview: Bubble | None = None
        self._has_messages = False
        self._inflight = 0
        self._from_addr = ""

        lay = QVBoxLayout(self)
        lay.setContentsMargins(56, 28, 56, 80)
        lay.setSpacing(22)
        lay.addWidget(PageHeader("chat", "SMS & Email", "Text, email, or both, with a live preview.", go_home))

        cols = QHBoxLayout()
        cols.setSpacing(28)
        cols.addWidget(self._build_compose(), 1)
        cols.addWidget(self._build_chat(), 1)
        lay.addLayout(cols)
        lay.addStretch(1)

        draft = self._safe_latest_draft()
        if draft:
            self.phone_input.setText(draft["phone"])
            self.email_input.setText(draft.get("email", ""))
            self.subject_input.setText(draft.get("subject", ""))
            self.message_edit.setPlainText(draft["body"])
            has_email = bool(draft.get("email"))
            self.mail_check.setChecked(has_email)
            self.sms_check.setChecked(bool(draft["phone"]) or not has_email)
        self._on_channels_changed()
        self._update_empty_hint()

    def _build_compose(self) -> QWidget:
        card, c = _card()
        c.setSpacing(0)

        head = QHBoxLayout()
        head.addWidget(mono_label("NEW MESSAGE"))
        head.addStretch(1)
        settings_btn = QPushButton("  Settings")
        settings_btn.setObjectName("linkBlue")
        settings_btn.setIcon(icon("mail", BLUE, 14))
        settings_btn.setIconSize(QSize(14, 14))
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self._open_settings)
        head.addWidget(settings_btn)
        c.addLayout(head)
        c.addSpacing(18)

        lbl = QLabel("Send via")
        lbl.setObjectName("fieldLabel")
        c.addWidget(lbl)
        c.addSpacing(8)
        chan = QHBoxLayout()
        chan.setSpacing(22)
        self.sms_check = QCheckBox("SMS")
        self.sms_check.setChecked(True)
        self.mail_check = QCheckBox("Email")
        self.status_label = QLabel()
        self.status_label.setObjectName("statusOk")
        chan.addWidget(self.sms_check)
        chan.addWidget(self.mail_check)
        chan.addStretch(1)
        chan.addWidget(self.status_label)
        c.addLayout(chan)
        c.addSpacing(18)

        self.sms_group = QWidget()
        sg = QVBoxLayout(self.sms_group)
        sg.setContentsMargins(0, 0, 0, 0)
        sg.setSpacing(8)
        pl = QLabel("Phone number")
        pl.setObjectName("fieldLabel")
        sg.addWidget(pl)
        prow = QHBoxLayout()
        prow.setSpacing(0)
        self.country = QComboBox()
        self.country.setObjectName("joinCombo")
        for iso, code in COUNTRY_CODES:
            self.country.addItem(f"{iso.lower()} {code}", code)
        self.country.setCurrentIndex(next(i for i, (iso, _c) in enumerate(COUNTRY_CODES) if iso == "PH"))
        self.phone_input = QLineEdit()
        self.phone_input.setObjectName("joinRightInput")
        self.phone_input.setPlaceholderText("0917 123 4567 or +63 917 123 4567")
        prow.addWidget(self.country)
        prow.addWidget(self.phone_input, 1)
        sg.addLayout(prow)
        sg.addSpacing(10)
        c.addWidget(self.sms_group)

        self.mail_group = QWidget()
        mg = QVBoxLayout(self.mail_group)
        mg.setContentsMargins(0, 0, 0, 0)
        mg.setSpacing(8)
        el = QLabel("Email address")
        el.setObjectName("fieldLabel")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("name@example.com")
        sl = QLabel("Subject")
        sl.setObjectName("fieldLabel")
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("What is this about?")
        mg.addWidget(el)
        mg.addWidget(self.email_input)
        mg.addSpacing(6)
        mg.addWidget(sl)
        mg.addWidget(self.subject_input)
        mg.addSpacing(10)
        c.addWidget(self.mail_group)

        mrow = QHBoxLayout()
        ml = QLabel("Message")
        ml.setObjectName("fieldLabel")
        self.counter = QLabel()
        self.counter.setObjectName("counter")
        mrow.addWidget(ml)
        mrow.addStretch(1)
        mrow.addWidget(self.counter)
        c.addLayout(mrow)
        c.addSpacing(8)
        self.message_edit = QPlainTextEdit()
        self.message_edit.setObjectName("messageEdit")
        self.message_edit.setPlaceholderText("Write your message...")
        self.message_edit.setMinimumHeight(130)
        c.addWidget(self.message_edit)
        c.addSpacing(8)

        info = QHBoxLayout()
        self.parts_label = QLabel()
        self.parts_label.setObjectName("subtle")
        self.cost_label = QLabel()
        self.cost_label.setObjectName("subtle")
        info.addWidget(self.parts_label)
        info.addStretch(1)
        info.addWidget(self.cost_label)
        c.addLayout(info)
        c.addSpacing(18)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        self.send_btn = self._button("  Send now", "blue", "send", "#FFFFFF")
        self.schedule_btn = self._button("  Schedule", "tonal", "clock", BLUE)
        self.draft_btn = self._button("  Save draft", "outline", "doc", MUTED)
        for b in (self.send_btn, self.schedule_btn, self.draft_btn):
            btns.addWidget(b, 1)
        c.addLayout(btns)

        self.send_btn.clicked.connect(self._send_now)
        self.schedule_btn.clicked.connect(self._schedule)
        self.draft_btn.clicked.connect(self._save_draft)
        self.message_edit.textChanged.connect(self._on_text_changed)
        self.sms_check.toggled.connect(self._on_channels_changed)
        self.mail_check.toggled.connect(self._on_channels_changed)
        self.phone_input.textChanged.connect(self._update_chat_header)
        self.email_input.textChanged.connect(self._update_chat_header)
        self.email_input.textChanged.connect(self._update_email_preview)
        self.subject_input.textChanged.connect(self._update_email_preview)
        self.country.currentIndexChanged.connect(self._update_chat_header)
        return card

    @staticmethod
    def _button(text: str, name: str, icon_name: str, color: str) -> QPushButton:
        b = QPushButton(text)
        b.setObjectName(name)
        b.setIcon(icon(icon_name, color, 16))
        b.setIconSize(QSize(16, 16))
        b.setMinimumHeight(46)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        return b

    @staticmethod
    def _set_status(label: QLabel, ok: bool, text: str) -> None:
        label.setObjectName("statusOk" if ok else "statusWarn")
        label.setText(f"●  {text}")
        label.style().unpolish(label)
        label.style().polish(label)

    def _refresh_status(self) -> None:
        mail_cfg = EmailConfig.from_settings(config_store.get_email_settings())
        self._from_addr = mail_cfg.from_address
        notes, ok = [], True
        if self.sms_check.isChecked():
            if SmsConfig.from_settings(config_store.get_sms_settings()).ready:
                notes.append("SMS ready")
            else:
                notes.append("SMS: not set up")
                ok = False
        if self.mail_check.isChecked():
            if mail_cfg.ready:
                notes.append("Email ready")
            else:
                notes.append("Email: not set up")
                ok = False
        if not notes:
            notes.append("Choose SMS, Email, or both")
            ok = False
        self._set_status(self.status_label, ok, "  ·  ".join(notes))
        self._update_email_preview()

    def _open_settings(self) -> None:
        if SettingsDialog(self).exec() == QDialog.DialogCode.Accepted:
            self._refresh_status()

    def _on_channels_changed(self, *_args) -> None:
        self.sms_group.setVisible(self.sms_check.isChecked())
        self.mail_group.setVisible(self.mail_check.isChecked())
        self._sync_preview_tabs()
        self._refresh_status()
        self._update_counters()
        self._update_chat_header()

    def _build_chat(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("chatPanel")
        add_shadow(panel, blur=36, alpha=22, dy=10)
        v = QVBoxLayout(panel)
        v.setContentsMargins(28, 24, 28, 28)
        v.setSpacing(16)

        box = QFrame()
        box.setObjectName("chatBox")
        box.setMinimumHeight(360)
        bv = QVBoxLayout(box)
        bv.setContentsMargins(0, 0, 0, 0)
        bv.setSpacing(0)

        header = QFrame()
        header.setObjectName("chatHeader")
        h = QHBoxLayout(header)
        h.setContentsMargins(18, 14, 18, 14)
        h.setSpacing(12)
        self.chat_avatar = QLabel("SMS")
        self.chat_avatar.setObjectName("avatar")
        self.chat_avatar.setFixedSize(36, 36)
        self.chat_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        who = QVBoxLayout()
        who.setSpacing(0)
        self.chat_name = QLabel()
        self.chat_name.setObjectName("sectionTitle")
        self.chat_sub = QLabel()
        self.chat_sub.setObjectName("subtle")
        who.addWidget(self.chat_name)
        who.addWidget(self.chat_sub)
        h.addWidget(self.chat_avatar)
        h.addLayout(who)
        h.addStretch(1)
        bv.addWidget(header)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("chatBody")
        self.chat_layout = QVBoxLayout(body)
        self.chat_layout.setContentsMargins(18, 14, 18, 14)
        self.chat_layout.setSpacing(10)
        self.empty_hint = QLabel("Your conversation will appear here.\nStart typing a message to see a live preview.")
        self.empty_hint.setObjectName("emptyHint")
        self.empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chat_layout.addWidget(self.empty_hint)
        self.chat_layout.addStretch(1)
        self.chat_scroll.setWidget(body)
        bv.addWidget(self.chat_scroll, 1)

        footer = QFrame()
        footer.setObjectName("chatFooter")
        f = QHBoxLayout(footer)
        f.setContentsMargins(14, 12, 14, 12)
        f.setSpacing(8)
        self.quick_input = QLineEdit()
        self.quick_input.setPlaceholderText("Message")
        self.quick_input.setStyleSheet("padding: 9px 12px;")
        quick_send = QPushButton()
        quick_send.setObjectName("iconSend")
        quick_send.setFixedSize(38, 38)
        quick_send.setIcon(icon("send", "#FFFFFF", 16))
        quick_send.setCursor(Qt.CursorShape.PointingHandCursor)
        f.addWidget(self.quick_input, 1)
        f.addWidget(quick_send)
        bv.addWidget(footer)

        tabs_row = QHBoxLayout()
        segment = QFrame()
        segment.setObjectName("segment")
        seg = QHBoxLayout(segment)
        seg.setContentsMargins(4, 4, 4, 4)
        seg.setSpacing(2)
        self.preview_group = QButtonGroup(self)
        self.preview_group.setExclusive(True)
        for idx, (name, ic) in enumerate((("Chat preview", "chat"), ("Email preview", "mail"))):
            btn = QToolButton()
            btn.setObjectName("navBtn")
            btn.setText(f" {name}")
            btn.setIcon(icon(ic, MUTED, 14, on_color=NAVY))
            btn.setIconSize(QSize(14, 14))
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.preview_group.addButton(btn, idx)
            seg.addWidget(btn)
        self.preview_group.button(0).setChecked(True)
        self.preview_group.idClicked.connect(self._show_preview)
        tabs_row.addWidget(segment)
        tabs_row.addStretch(1)
        v.addLayout(tabs_row)

        self.preview_stack = QStackedWidget()
        self.preview_stack.addWidget(box)
        self.preview_stack.addWidget(self._build_email_preview())
        v.addWidget(self.preview_stack, 1)

        quick_send.clicked.connect(self._quick_send)
        self.quick_input.returnPressed.connect(self._quick_send)
        return panel

    def _build_email_preview(self) -> QWidget:
        box = QFrame()
        box.setObjectName("chatBox")
        box.setMinimumHeight(360)
        bv = QVBoxLayout(box)
        bv.setContentsMargins(0, 0, 0, 0)
        bv.setSpacing(0)

        head = QFrame()
        head.setObjectName("chatHeader")
        hv = QVBoxLayout(head)
        hv.setContentsMargins(22, 18, 22, 16)
        hv.setSpacing(10)
        self.mail_subject = self._mail_label("mailSubject")
        hv.addWidget(self.mail_subject)
        self.mail_from = self._mail_label("mailAddr")
        self.mail_to = self._mail_label("mailAddr")
        for key, value in (("From", self.mail_from), ("To", self.mail_to)):
            row = QHBoxLayout()
            row.setSpacing(10)
            k = QLabel(key)
            k.setObjectName("subtle")
            k.setFixedWidth(34)
            row.addWidget(k, alignment=Qt.AlignmentFlag.AlignTop)
            row.addWidget(value, 1)
            hv.addLayout(row)
        bv.addWidget(head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("mailBody")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(22, 18, 22, 18)
        bl.setSpacing(0)
        self.mail_text = self._mail_label("mailText")
        self.mail_text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        bl.addWidget(self.mail_text)
        bl.addStretch(1)
        scroll.setWidget(body)
        bv.addWidget(scroll, 1)
        return box

    @staticmethod
    def _mail_label(name: str) -> QLabel:
        label = QLabel()
        label.setObjectName(name)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return label

    @staticmethod
    def _set_mail_text(label: QLabel, text: str, placeholder: str) -> None:
        empty = not text
        label.setText(placeholder if empty else text)
        label.setProperty("empty", empty)
        label.style().unpolish(label)
        label.style().polish(label)

    def _update_email_preview(self, *_args) -> None:
        self._set_mail_text(self.mail_subject, self.subject_input.text().strip(), "(no subject)")
        self._set_mail_text(self.mail_from, self._from_addr, "Using the default sender until you set one in Settings")
        self._set_mail_text(self.mail_to, self.email_input.text().strip(), "recipient@example.com")
        self._set_mail_text(self.mail_text, self.message_edit.toPlainText().strip(), "Your message will appear here.")

    def _show_preview(self, index: int) -> None:
        self.preview_stack.setCurrentIndex(index)

    def _sync_preview_tabs(self) -> None:
        sms_on, mail_on = self.sms_check.isChecked(), self.mail_check.isChecked()
        if mail_on and not sms_on:
            index = 1
        elif sms_on and not mail_on:
            index = 0
        else:
            index = max(0, self.preview_group.checkedId())
        self.preview_group.button(index).setChecked(True)
        self.preview_stack.setCurrentIndex(index)

    def _update_chat_header(self, *_args) -> None:
        sms_on, mail_on = self.sms_check.isChecked(), self.mail_check.isChecked()
        names = []
        raw = self.phone_input.text().strip()
        if sms_on and raw:
            try:
                names.append(build_e164(self.country.currentData(), raw))
            except ValueError:
                names.append(raw)
        address = self.email_input.text().strip()
        if mail_on and address:
            names.append(address)

        if sms_on and mail_on:
            self.chat_avatar.setText("S+@")
            kind = "SMS + Email conversation"
        elif mail_on:
            self.chat_avatar.setText("@")
            kind = "Email conversation"
        else:
            self.chat_avatar.setText("SMS")
            kind = "SMS conversation"

        if names:
            self.chat_name.setText("  ·  ".join(names))
            self.chat_sub.setText(kind)
        else:
            self.chat_name.setText("New conversation")
            self.chat_sub.setText("Enter a recipient to begin" if (sms_on or mail_on) else "Choose SMS, Email, or both")

    def _update_empty_hint(self) -> None:
        self.empty_hint.setVisible(not self._has_messages and self._preview is None)

    def _scroll_bottom(self) -> None:
        QTimer.singleShot(
            0, lambda: self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())
        )

    def _insert_chat_widget(self, widget: QWidget) -> None:
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, widget)
        self._scroll_bottom()

    @staticmethod
    def _now_text() -> str:
        return datetime.now().strftime("%I:%M %p").lstrip("0")

    def _remove_preview(self) -> None:
        if self._preview is not None:
            self._preview.setParent(None)
            self._preview.deleteLater()
            self._preview = None

    def _update_preview(self) -> None:
        text = self.message_edit.toPlainText().strip()
        if not text:
            self._remove_preview()
        elif self._preview is None:
            self._preview = Bubble(text, True, self._now_text(), "Preview")
            self._insert_chat_widget(self._preview)
        else:
            self._preview.set_text(text)
            self._scroll_bottom()
        self._update_empty_hint()

    def _add_message(self, text: str, status: str) -> Bubble:
        self._remove_preview()
        if not self._has_messages:
            self._has_messages = True
            day = QLabel("TODAY")
            day.setObjectName("dayDivider")
            day.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._insert_chat_widget(day)
        bubble = Bubble(text, True, self._now_text(), status)
        self._insert_chat_widget(bubble)
        self._update_preview()
        self._update_empty_hint()
        return bubble

    def _on_text_changed(self) -> None:
        text = self.message_edit.toPlainText()
        if self.sms_check.isChecked() and not self.mail_check.isChecked() and len(text) > MAX_SMS_CHARS:
            cursor = self.message_edit.textCursor()
            pos = min(cursor.position(), MAX_SMS_CHARS)
            self.message_edit.blockSignals(True)
            self.message_edit.setPlainText(text[:MAX_SMS_CHARS])
            self.message_edit.blockSignals(False)
            cursor.setPosition(pos)
            self.message_edit.setTextCursor(cursor)
        self._update_counters()
        self._update_preview()
        self._update_email_preview()

    def _update_counters(self) -> None:
        text = self.message_edit.toPlainText()
        sms_on = self.sms_check.isChecked()
        if sms_on:
            parts = sms_parts(text)
            self.counter.setText(f"{len(text)} / {MAX_SMS_CHARS}")
            self.parts_label.setText(f"{parts} SMS part{'s' if parts != 1 else ''}")
            self.cost_label.setText(f"Estimated SMS cost · ₱{parts * COST_PER_PART:.2f}")
        else:
            self.counter.setText(f"{len(text)} characters")
            self.parts_label.setText("")
            self.cost_label.setText("")

    def _build_jobs(self) -> tuple[list, str] | None:
        sms_on, mail_on = self.sms_check.isChecked(), self.mail_check.isChecked()
        if not (sms_on or mail_on):
            QMessageBox.warning(self, "Choose a channel", "Tick SMS, Email, or both.")
            return None
        body = self.message_edit.toPlainText().strip()
        if not body:
            QMessageBox.warning(self, "Empty message", "Please write a message first.")
            return None

        jobs = []
        if sms_on:
            sms_cfg = SmsConfig.from_settings(config_store.get_sms_settings())
            if not sms_cfg.ready:
                self._refresh_status()
                QMessageBox.warning(self, "SMS isn't set up", "Enter your SimGate API key and device ID in Settings first.")
                self._open_settings()
                return None
            try:
                to = build_e164(self.country.currentData(), self.phone_input.text())
            except ValueError as exc:
                QMessageBox.warning(self, "Check the number", str(exc))
                return None
            if len(body) > MAX_SMS_CHARS:
                QMessageBox.warning(
                    self, "Too long for SMS",
                    f"SMS messages are limited to {MAX_SMS_CHARS} characters (this one has {len(body)}).\n"
                    "Shorten it, or untick SMS to send it as an email only.",
                )
                return None
            jobs.append(("SMS", to, api_client.send_sms, (sms_cfg, to, body)))
        if mail_on:
            mail_cfg = EmailConfig.from_settings(config_store.get_email_settings())
            if not mail_cfg.ready:
                self._refresh_status()
                QMessageBox.warning(self, "Email isn't set up", "Enter your Resend API key in Settings first.")
                self._open_settings()
                return None
            address = self.email_input.text().strip()
            if not api_client.is_valid_email(address):
                QMessageBox.warning(self, "Check the address", "Please enter a valid email address.")
                return None
            subject = self.subject_input.text().strip() or "(no subject)"
            jobs.append(("Email", address, api_client.send_email, (mail_cfg, address, subject, body)))
        return jobs, body

    def _quick_send(self) -> None:
        text = self.quick_input.text().strip()
        if not text:
            return
        self.message_edit.setPlainText(text)
        self.quick_input.clear()
        self._send_now()

    def _send_now(self) -> None:
        built = self._build_jobs()
        if built is None:
            return
        jobs, body = built
        bubble = self._add_message(body, "Sending...")
        self.message_edit.clear()
        self.subject_input.clear()
        self._dispatch(jobs, bubble)

    def _dispatch(self, jobs: list, bubble: Bubble) -> None:
        batch = {"pending": len(jobs), "results": []}
        self._inflight += 1
        self.send_btn.setEnabled(False)
        bubble.set_status("Sending...")
        for label, target, func, args in jobs:
            run_in_background(
                func, *args,
                on_success=lambda res, l=label, t=target: self._job_done(batch, bubble, l, t, True, res),
                on_error=lambda msg, l=label, t=target: self._job_done(batch, bubble, l, t, False, msg),
            )

    def _job_done(self, batch: dict, bubble: Bubble, label: str, target: str, ok: bool, payload: object) -> None:
        batch["results"].append((label, target, ok, payload))
        batch["pending"] -= 1
        if batch["pending"] > 0:
            return
        self._finish_send()
        results = sorted(batch["results"], key=lambda r: r[0] != "SMS")
        bubble.set_status(self._bubble_status(results))
        self._summarise(results)

    def _finish_send(self) -> None:
        self._inflight = max(0, self._inflight - 1)
        if self._inflight == 0:
            self.send_btn.setEnabled(True)

    @staticmethod
    def _sms_waiting(payload: object) -> bool:
        return str(payload.get("status", "")).lower() == "queued"

    def _bubble_status(self, results: list) -> str:
        if len(results) == 1:
            label, _target, ok, payload = results[0]
            if not ok:
                return "Failed"
            return "Pending" if label == "SMS" and self._sms_waiting(payload) else "Sent ✓"
        parts = []
        for label, _target, ok, payload in results:
            if not ok:
                parts.append(f"{label} failed")
            elif label == "SMS" and self._sms_waiting(payload):
                parts.append("SMS pending")
            else:
                parts.append(f"{label} ✓")
        return "  ·  ".join(parts)

    def _summarise(self, results: list) -> None:
        lines, failures = [], 0
        for label, target, ok, payload in results:
            if not ok:
                failures += 1
                lines.append(f"{label} failed: {payload}")
            elif label == "SMS":
                status = payload.get("status", "Sent")
                line = f"SMS to {target}: {status}"
                if payload.get("sid"):
                    line += f"\nReference: {payload['sid']}"
                if self._sms_waiting(payload):
                    line += "\nYour phone is offline. SimGate will send it when the phone reconnects."
                lines.append(line)
            else:
                lines.append(f"Email sent to {target}")
        text = "\n\n".join(lines)
        if failures == len(results):
            QMessageBox.critical(self, "Message failed", text)
        elif failures:
            QMessageBox.warning(self, "Some messages failed", text)
        else:
            QMessageBox.information(self, "Message sent", text)

    def _schedule(self) -> None:
        built = self._build_jobs()
        if built is None:
            return
        jobs, body = built

        dialog = QDialog(self)
        dialog.setWindowTitle("Schedule message")
        v = QVBoxLayout(dialog)
        v.setContentsMargins(24, 22, 24, 20)
        v.setSpacing(12)
        v.addWidget(QLabel("Send this message at:"))
        picker = QDateTimeEdit(QDateTime.currentDateTime().addSecs(300))
        picker.setCalendarPopup(True)
        picker.setDisplayFormat("ddd, d MMM yyyy  h:mm AP")
        picker.setMinimumDateTime(QDateTime.currentDateTime().addSecs(60))
        v.addWidget(picker)
        note = QLabel("The app must stay open for the message to be sent.")
        note.setObjectName("subtle")
        v.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        v.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        when = picker.dateTime()
        delay_ms = max(1000, QDateTime.currentDateTime().msecsTo(when))
        bubble = self._add_message(body, f"Scheduled {when.toString('h:mm AP')}")
        self.message_edit.clear()
        self.subject_input.clear()
        self._arm_timer(delay_ms, jobs, bubble)

    def _arm_timer(self, delay_ms: int, jobs: list, bubble: Bubble) -> None:
        chunk = min(delay_ms, 2_000_000_000)
        remaining = delay_ms - chunk
        if remaining > 0:
            QTimer.singleShot(chunk, lambda: self._arm_timer(remaining, jobs, bubble))
        else:
            QTimer.singleShot(chunk, lambda: self._dispatch(jobs, bubble))

    def _safe_latest_draft(self) -> dict | None:
        try:
            return self.db.latest_draft(self.user.id)
        except DatabaseError:
            return None

    def _save_draft(self) -> None:
        body = self.message_edit.toPlainText().strip()
        if not body:
            QMessageBox.warning(self, "Nothing to save", "Write a message before saving a draft.")
            return
        try:
            self.db.save_draft(
                self.user.id, self.phone_input.text().strip(), body,
                self.email_input.text().strip(), self.subject_input.text().strip(),
            )
        except DatabaseError as exc:
            QMessageBox.critical(self, "Draft not saved", str(exc))
            return
        QMessageBox.information(self, "Draft saved", "Your draft was saved and will be restored next time.")


DEFAULT_FIELDS = {"full_name", "gender", "dob", "email", "phone", "street", "city", "postal", "company", "job"}


class DataPage(QFrame):
    def __init__(self, user: User, db: Database, go_home) -> None:
        super().__init__()
        self.user, self.db = user, db
        self.setObjectName("pageRoot")
        self._users: list[dict] = []
        self._loaded = False
        self._busy = False
        self._refetch = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(56, 28, 56, 80)
        lay.setSpacing(22)
        lay.addWidget(PageHeader("database", "Fake Data Generator", "Choose exactly what you need.", go_home))
        lay.addWidget(self._build_selector())
        lay.addWidget(self._build_preview())
        lay.addStretch(1)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(600)
        self._debounce.timeout.connect(self._fetch)
        self.count_spin.valueChanged.connect(lambda _v: self._debounce.start())

    def _build_selector(self) -> QWidget:
        card, c = _card()
        head = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel("Select data fields")
        t.setObjectName("sectionTitle")
        self.selected_label = QLabel()
        self.selected_label.setObjectName("subtle")
        col.addWidget(t)
        col.addWidget(self.selected_label)
        self.select_all_btn = QPushButton("Select all")
        self.select_all_btn.setObjectName("linkBlue")
        self.select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_all_btn.clicked.connect(self._toggle_all)
        head.addLayout(col)
        head.addStretch(1)
        head.addWidget(self.select_all_btn, alignment=Qt.AlignmentFlag.AlignTop)
        c.addLayout(head)
        c.addSpacing(18)

        grid = QGridLayout()
        grid.setSpacing(14)
        self.cards: list[FieldCard] = []
        for i, (key, label, hint) in enumerate(DATA_FIELDS):
            fc = FieldCard(key, label, hint)
            fc.setChecked(key in DEFAULT_FIELDS)
            fc.toggled.connect(self._on_selection_changed)
            self.cards.append(fc)
            grid.addWidget(fc, i // 3, i % 3)
        for col_idx in range(3):
            grid.setColumnStretch(col_idx, 1)
        c.addLayout(grid)
        c.addSpacing(20)
        c.addWidget(hline())
        c.addSpacing(18)

        row = QHBoxLayout()
        col2 = QVBoxLayout()
        col2.setSpacing(2)
        n = QLabel("Number of records")
        n.setObjectName("sectionTitle")
        hint = QLabel(f"Generate between {MIN_RECORDS} and {MAX_RECORDS} rows (saved to the database)")
        hint.setObjectName("subtle")
        col2.addWidget(n)
        col2.addWidget(hint)
        self.count_spin = QSpinBox()
        self.count_spin.setRange(MIN_RECORDS, MAX_RECORDS)
        self.count_spin.setValue(10)
        self.count_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.count_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_spin.setKeyboardTracking(False)
        self.count_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.count_spin.setFixedSize(110, 44)
        row.addLayout(col2)
        row.addStretch(1)
        row.addWidget(self.count_spin)
        c.addLayout(row)
        self._update_selected_label()
        return card

    def _build_preview(self) -> QWidget:
        card, c = _card()
        c.setContentsMargins(0, 24, 0, 0)
        head = QHBoxLayout()
        head.setContentsMargins(32, 0, 32, 18)
        head.setSpacing(12)
        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel("Generated preview")
        t.setObjectName("sectionTitle")
        self.count_label = QLabel("No records yet")
        self.count_label.setObjectName("subtle")
        col.addWidget(t)
        col.addWidget(self.count_label)
        head.addLayout(col)
        head.addStretch(1)
        self.export_btn = QPushButton("  Export CSV")
        self.export_btn.setObjectName("blue")
        self.export_btn.setIcon(icon("download", "#FFFFFF", 16))
        self.regen_btn = QPushButton("  Regenerate")
        self.regen_btn.setObjectName("primary")
        self.regen_btn.setIcon(icon("refresh", "#FFFFFF", 16))
        for b in (self.export_btn, self.regen_btn):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setIconSize(QSize(16, 16))
            head.addWidget(b)
        c.addLayout(head)

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.horizontalHeader().setFixedHeight(44)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c.addWidget(self.table)

        self.export_btn.clicked.connect(self._export_csv)
        self.regen_btn.clicked.connect(self._fetch)
        self.export_btn.setEnabled(False)
        return card


    def ensure_loaded(self) -> None:
        if not self._loaded:
            self._loaded = True
            self._fetch()

    def _selected_keys(self) -> list[str]:
        return [fc.key for fc in self.cards if fc.isChecked()]

    def _update_selected_label(self) -> None:
        n = len(self._selected_keys())
        self.selected_label.setText(f"{n} of {len(self.cards)} selected")
        self.select_all_btn.setText("Clear all" if n == len(self.cards) else "Select all")

    def _toggle_all(self) -> None:
        target = len(self._selected_keys()) != len(self.cards)
        for fc in self.cards:
            fc.blockSignals(True)
            fc.check.blockSignals(True)
            fc.check.setChecked(target)
            fc.check.blockSignals(False)
            fc.blockSignals(False)
            fc.setProperty("selected", target)
            fc.style().unpolish(fc)
            fc.style().polish(fc)
        self._on_selection_changed()

    def _on_selection_changed(self, *_args) -> None:
        self._update_selected_label()
        self._render()


    def _fetch(self) -> None:
        if self._busy:
            self._refetch = True
            return
        self._busy = True
        self.regen_btn.setEnabled(False)
        self.count_label.setText("Generating...")
        run_in_background(
            api_client.fetch_random_users, self.count_spin.value(),
            on_success=self._on_users, on_error=self._on_error,
        )

    def _done(self) -> None:
        self._busy = False
        self.regen_btn.setEnabled(True)
        if self._refetch:
            self._refetch = False
            self._fetch()

    def _on_users(self, users: list) -> None:
        self._users = users
        self._store(users)
        self._render()
        self._done()

    def _store(self, users: list) -> None:
        self._saved = False
        try:
            headers, rows = api_client.build_table(users, [k for k, _, _ in DATA_FIELDS])
            self.db.save_fake_records(self.user.id, [dict(zip(headers, r)) for r in rows])
            self._saved = True
        except (DatabaseError, Exception) as exc:
            QMessageBox.warning(self, "Couldn't save records", f"The records were generated but not saved:\n{exc}")

    def _on_error(self, message: str) -> None:
        self.count_label.setText("Generation failed")
        self._done()
        QMessageBox.warning(self, "Couldn't generate data", message)


    def _render(self) -> None:
        keys = self._selected_keys()
        headers, rows = api_client.build_table(self._users, keys)
        t = self.table
        t.clear()
        t.setRowCount(0)
        t.setColumnCount(len(headers) + 1 if headers else 0)
        if headers:
            t.setHorizontalHeaderLabels(["#"] + [h.upper() for h in headers])
            t.setRowCount(len(rows))
            for r, row in enumerate(rows):
                num = QTableWidgetItem(str(r + 1))
                num.setForeground(QColor(MUTED))
                t.setItem(r, 0, num)
                for c, value in enumerate(row, start=1):
                    t.setItem(r, c, QTableWidgetItem(value))
            hdr = t.horizontalHeader()
            hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        t.setFixedHeight(44 + 44 * len(rows) + 2 if rows else 90)
        n = len(self._users)
        if not keys:
            self.count_label.setText("Select at least one field to see data")
        else:
            saved = " · saved to database" if getattr(self, "_saved", False) else ""
            self.count_label.setText(f"{n} generated record{'s' if n != 1 else ''}{saved}")
        self.export_btn.setEnabled(bool(rows))

    def _export_csv(self) -> None:
        headers, rows = api_client.build_table(self._users, self._selected_keys())
        if not rows:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "fake_data.csv", "CSV files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as fh:
                writer = csv.writer(fh)
                writer.writerow(headers)
                writer.writerows(rows)
        except OSError as exc:
            QMessageBox.critical(self, "Export failed", f"Could not write the file:\n{exc}")
            return
        QMessageBox.information(self, "Export complete", f"Saved {len(rows)} records to:\n{path}")


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(460)
        email = config_store.get_email_settings()
        sms = config_store.get_sms_settings()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(0)

        self.api_key = QLineEdit(email["api_key"])
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("re_...")
        self.sender = QLineEdit(email["sender"])
        self.sender.setPlaceholderText(f"Optional - defaults to {api_client.DEFAULT_SENDER}")
        self.sms_key = QLineEdit(sms["api_key"])
        self.sms_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.sms_key.setPlaceholderText("From the SimGate dashboard")
        self.sms_device = QLineEdit(sms["device_id"])
        self.sms_device.setPlaceholderText("android-xxxxxxxxxxxxxxxx")

        self._section(lay, "Email (Resend)", "Create an API key at resend.com. Use a From address on a domain you have verified.")
        for text, edit in (("API key", self.api_key), ("From address", self.sender)):
            self._field(lay, text, edit)
        lay.addSpacing(6)
        self._section(lay, "SMS (SimGate)", "Create an API key at simgate.app and copy your paired phone's Device ID.")
        for text, edit in (("API key", self.sms_key), ("Device ID", self.sms_device)):
            self._field(lay, text, edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    @staticmethod
    def _section(lay: QVBoxLayout, title: str, hint: str) -> None:
        t = QLabel(title)
        t.setObjectName("sectionTitle")
        h = QLabel(hint)
        h.setObjectName("subtle")
        h.setWordWrap(True)
        lay.addWidget(t)
        lay.addWidget(h)
        lay.addSpacing(12)

    @staticmethod
    def _field(lay: QVBoxLayout, text: str, edit: QLineEdit) -> None:
        lbl = QLabel(text)
        lbl.setObjectName("fieldLabel")
        lay.addWidget(lbl)
        lay.addSpacing(6)
        lay.addWidget(edit)
        lay.addSpacing(14)

    def _save(self) -> None:
        sender = self.sender.text().strip()
        if sender and not api_client.is_valid_email(api_client._sender_address(sender)):
            QMessageBox.warning(self, "Check the address", "The From address isn't a valid email address.")
            return
        if bool(self.sms_key.text().strip()) != bool(self.sms_device.text().strip()):
            QMessageBox.warning(self, "Missing details", "Enter both the SimGate API key and device ID.")
            return
        try:
            config_store.save_email_settings({"api_key": self.api_key.text(), "sender": sender})
            config_store.save_sms_settings({"api_key": self.sms_key.text(), "device_id": self.sms_device.text()})
        except OSError as exc:
            QMessageBox.critical(self, "Couldn't save", f"The settings could not be saved:\n{exc}")
            return
        self.accept()


class DashboardWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, user: User, db: Database) -> None:
        super().__init__()
        self.user = user
        self.setWindowTitle("UtilKit")
        self.setWindowIcon(logo_icon())
        self.resize(1280, 820)
        self.setMinimumSize(1060, 700)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_topbar())

        self.stack = QStackedWidget()
        self.home = HomePage(user)
        self.links = LinksPage(self.show_home)
        self.messages = MessagesPage(user, db, self.show_home)
        self.data = DataPage(user, db, self.show_home)
        for page in (self.home, self.links, self.messages, self.data):
            self.stack.addWidget(scrollable(page))
        root.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.home.open_tool.connect(self.switch_page)
        self.switch_page(PAGE_HOME)

    def _build_topbar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("topbar")
        bar.setFixedHeight(68)
        row = QHBoxLayout(bar)
        row.setContentsMargins(24, 10, 24, 12)

        logo = QLabel()
        logo.setObjectName("logoTile")
        logo.setFixedSize(34, 34)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setPixmap(logo_pixmap(30))
        brand = QLabel("UTILKIT")
        brand.setObjectName("brand")
        row.addWidget(logo)
        row.addSpacing(10)
        row.addWidget(brand)
        row.addStretch(1)

        segment = QFrame()
        segment.setObjectName("segment")
        seg = QHBoxLayout(segment)
        seg.setContentsMargins(4, 4, 4, 4)
        seg.setSpacing(2)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for idx, (name, ic) in enumerate((("All tools", "grid"), ("URL Shortener", "link"), ("SMS & Email", "chat"), ("Data Generator", "database"))):
            btn = QToolButton()
            btn.setObjectName("navBtn")
            btn.setText(f" {name}".replace("&", "&&"))
            btn.setIcon(icon(ic, MUTED, 14, on_color=NAVY))
            btn.setIconSize(QSize(14, 14))
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.nav_group.addButton(btn, idx)
            seg.addWidget(btn)
        self.nav_group.idClicked.connect(self.switch_page)
        row.addWidget(segment)
        row.addStretch(1)

        avatar = QLabel(self.user.username[:1].upper() or "?")
        avatar.setObjectName("avatarUser")
        avatar.setFixedSize(30, 30)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info = QVBoxLayout()
        info.setSpacing(0)
        name = QLabel(self.user.username)
        name.setObjectName("userName")
        info.addWidget(name)
        logout = QToolButton()
        logout.setObjectName("logout")
        logout.setIcon(icon("signin", MUTED, 18))
        logout.setIconSize(QSize(18, 18))
        logout.setToolTip("Sign out")
        logout.setCursor(Qt.CursorShape.PointingHandCursor)
        logout.clicked.connect(self.logout_requested.emit)
        row.addWidget(avatar)
        row.addSpacing(10)
        row.addLayout(info)
        row.addSpacing(14)
        row.addWidget(logout)
        return bar

    def show_home(self) -> None:
        self.switch_page(PAGE_HOME)

    def switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        button = self.nav_group.button(index)
        if button:
            button.setChecked(True)
        if index == PAGE_DATA:
            self.data.ensure_loaded()
