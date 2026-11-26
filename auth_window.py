from __future__ import annotations

from PyQt6.QtCore import QPointF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from database import AuthError, Database, DatabaseError
from icons import icon, logo_pixmap, pixmap, logo_icon
from styles import NAVY, SKY
from widgets import add_shadow, scrollable, spaced


class HeroPanel(QFrame):

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(NAVY))
        p.setPen(QPen(QColor(255, 255, 255, 30), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        w, h = self.width(), self.height()
        p.drawEllipse(QPointF(w * 0.98, h * 0.2), w * 0.55, w * 0.55)
        p.drawEllipse(QPointF(-w * 0.02, h * 0.97), w * 0.3, w * 0.3)
        p.end()


class AuthWindow(QWidget):
    authenticated = pyqtSignal(object)

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.setWindowTitle("UtilKit - Sign in")
        self.setWindowIcon(logo_icon())
        self.resize(1280, 760)
        self.setMinimumSize(1000, 780)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_hero(), 9)
        root.addWidget(self._build_right(), 11)

        self._sync_stack_sizes()


    def _build_hero(self) -> QWidget:
        hero = HeroPanel()
        lay = QVBoxLayout(hero)
        lay.setContentsMargins(56, 36, 56, 32)
        lay.setSpacing(0)

        brand = QHBoxLayout()
        brand.setSpacing(12)
        logo = QLabel()
        logo.setObjectName("heroLogo")
        logo.setFixedSize(38, 38)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setPixmap(logo_pixmap(28))
        name = spaced(QLabel("UTILKIT"), 1.5)
        name.setObjectName("heroBrand")
        brand.addWidget(logo)
        brand.addWidget(name)
        brand.addStretch(1)
        lay.addLayout(brand)
        lay.addSpacing(120)

        eyebrow = spaced(QLabel("ONE WORKSPACE · THREE ESSENTIALS"), 1.6)
        eyebrow.setObjectName("heroEyebrow")
        title = QLabel("Simple tools.")
        title.setObjectName("heroTitle")
        italic = QLabel("Smarter work.")
        italic.setObjectName("heroItalic")
        sub = QLabel("Everything you need to manage for utilities right in one place.")
        sub.setObjectName("heroSub")
        sub.setWordWrap(True)
        lay.addWidget(eyebrow)
        lay.addSpacing(12)
        lay.addWidget(title)
        lay.addWidget(italic)
        lay.addSpacing(16)
        lay.addWidget(sub)
        lay.addSpacing(24)

        strip = QFrame()
        strip.setObjectName("featStrip")
        srow = QHBoxLayout(strip)
        srow.setContentsMargins(0, 0, 0, 0)
        srow.setSpacing(0)
        features = [
            ("link", "Short links", "Clean and shareable"),
            ("chat", "Messages", "Simple conversations"),
            ("database", "Generate data", "Ready in seconds"),
        ]
        for i, (ic, t, s) in enumerate(features):
            if i:
                sep = QFrame()
                sep.setObjectName("vline")
                sep.setFixedWidth(1)
                srow.addWidget(sep)
            cell = QWidget()
            c = QHBoxLayout(cell)
            c.setContentsMargins(0 if i == 0 else 16, 16, 8, 16)
            c.setSpacing(12)
            tile = QLabel()
            tile.setObjectName("featTile")
            tile.setFixedSize(32, 32)
            tile.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tile.setPixmap(pixmap(ic, NAVY, 15))
            col = QVBoxLayout()
            col.setSpacing(1)
            tl, sl = QLabel(t), QLabel(s)
            tl.setObjectName("featTitle")
            sl.setObjectName("featSub")
            col.addWidget(tl)
            col.addWidget(sl)
            c.addWidget(tile)
            c.addLayout(col)
            c.addStretch(1)
            srow.addWidget(cell, 1)
        lay.addWidget(strip)
        lay.addSpacing(16)
        foot = QLabel("Built for makers, teams, and quick-moving ideas.")
        foot.setObjectName("heroFoot")
        lay.addWidget(foot)
        lay.addStretch(1)
        return hero


    def _build_right(self) -> QWidget:
        pane = QFrame()
        pane.setObjectName("rightPane")
        outer = QVBoxLayout(pane)
        outer.setContentsMargins(40, 32, 40, 32)

        self.card = QFrame()
        self.card.setObjectName("authCard")
        self.card.setFixedWidth(400)
        add_shadow(self.card)
        card = QVBoxLayout(self.card)
        card.setContentsMargins(34, 26, 34, 24)
        card.setSpacing(0)

        logo = QLabel()
        logo.setObjectName("authLogo")
        logo.setFixedSize(56, 56)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setPixmap(logo_pixmap(50))
        card.addWidget(logo, alignment=Qt.AlignmentFlag.AlignHCenter)
        card.addSpacing(12)

        self.title = QLabel("Sign in to UtilKit")
        self.title.setObjectName("authTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle = QLabel("Sign in to continue to your utility workspace.")
        self.subtitle.setObjectName("authSub")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setWordWrap(True)
        card.addWidget(self.title)
        card.addSpacing(4)
        card.addWidget(self.subtitle)
        card.addSpacing(18)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_login())
        self.stack.addWidget(self._build_register())
        card.addWidget(self.stack)

        outer.addStretch(1)
        outer.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignHCenter)
        outer.addStretch(2)
        area = scrollable(pane)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return area

    @staticmethod
    def _field(label: str, widget: QWidget) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        lbl = QLabel(label)
        lbl.setObjectName("fieldLabel")
        lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        widget.setMinimumHeight(40)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        v.addWidget(lbl)
        v.addWidget(widget)
        return box

    @staticmethod
    def _password_input(placeholder: str) -> QLineEdit:
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setEchoMode(QLineEdit.EchoMode.Password)
        action = QAction(edit)
        action.setIcon(icon("eye", SKY, 16))
        edit.addAction(action, QLineEdit.ActionPosition.TrailingPosition)

        def toggle() -> None:
            hidden = edit.echoMode() == QLineEdit.EchoMode.Password
            edit.setEchoMode(QLineEdit.EchoMode.Normal if hidden else QLineEdit.EchoMode.Password)
            action.setIcon(icon("eye-off" if hidden else "eye", SKY, 16))

        action.triggered.connect(toggle)
        return edit

    @staticmethod
    def _error_label() -> QLabel:
        lbl = QLabel()
        lbl.setObjectName("errorLabel")
        lbl.setWordWrap(True)
        lbl.hide()
        return lbl

    @staticmethod
    def _switch_row(prompt: str, link_text: str, slot) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(4)
        row.addStretch(1)
        lbl = QLabel(prompt)
        lbl.setObjectName("plainMuted")
        btn = QPushButton(link_text)
        btn.setObjectName("linkBold")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(slot)
        row.addWidget(lbl)
        row.addWidget(btn)
        row.addStretch(1)
        return row

    def _build_login(self) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(12)

        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter your username")
        self.login_password = self._password_input("Enter your password")
        v.addWidget(self._field("Username", self.login_username))
        v.addWidget(self._field("Password", self.login_password))

        self.login_error = self._error_label()
        v.addWidget(self.login_error)

        btn = QPushButton("Sign in  ")
        btn.setObjectName("primary")
        btn.setIcon(icon("arrow-right", "#FFFFFF", 16))
        btn.setIconSize(QSize(16, 16))
        btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(40)
        btn.clicked.connect(self._do_login)
        v.addWidget(btn)
        v.addSpacing(2)
        v.addLayout(self._switch_row("New to UtilKit?", "Create an account", self.show_register))

        self.login_username.returnPressed.connect(self.login_password.setFocus)
        self.login_password.returnPressed.connect(self._do_login)
        for edit in (self.login_username, self.login_password):
            edit.textEdited.connect(self.login_error.hide)
        return page

    def _build_register(self) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(12)

        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("Choose a username")
        self.reg_password = self._password_input("At least 8 characters")
        self.reg_confirm = self._password_input("Repeat your password")
        v.addWidget(self._field("Username", self.reg_username))
        v.addWidget(self._field("Password", self.reg_password))
        v.addWidget(self._field("Confirm password", self.reg_confirm))

        self.reg_error = self._error_label()
        v.addWidget(self.reg_error)

        btn = QPushButton("Create account")
        btn.setObjectName("primary")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(40)
        btn.clicked.connect(self._do_register)
        v.addWidget(btn)
        v.addSpacing(2)
        v.addLayout(self._switch_row("Already have an account?", "Sign in", self.show_login))

        self.reg_confirm.returnPressed.connect(self._do_register)
        for edit in (self.reg_username, self.reg_password, self.reg_confirm):
            edit.textEdited.connect(self.reg_error.hide)
        return page


    def _sync_stack_sizes(self) -> None:
        current = self.stack.currentIndex()
        for i in range(self.stack.count()):
            vertical = QSizePolicy.Policy.Preferred if i == current else QSizePolicy.Policy.Ignored
            self.stack.widget(i).setSizePolicy(QSizePolicy.Policy.Preferred, vertical)
        self.stack.updateGeometry()

    def show_login(self) -> None:
        self.stack.setCurrentIndex(0)
        self._sync_stack_sizes()
        self.title.setText("Sign in to UtilKit")
        self.subtitle.setText("Sign in to continue to your utility workspace.")
        self.setWindowTitle("UtilKit - Sign in")

    def show_register(self) -> None:
        self.stack.setCurrentIndex(1)
        self._sync_stack_sizes()
        self.title.setText("Create your account")
        self.subtitle.setText("Start using your utility workspace in seconds.")
        self.setWindowTitle("UtilKit - Create account")

    def reset(self) -> None:
        self.login_password.clear()
        self.login_error.hide()
        self.show_login()


    @staticmethod
    def _show_error(label: QLabel, message: str) -> None:
        label.setText(message)
        label.show()

    def _do_login(self) -> None:
        username, password = self.login_username.text().strip(), self.login_password.text()
        if not username or not password:
            self._show_error(self.login_error, "Enter your username and password.")
            return
        try:
            user = self.db.authenticate(username, password)
        except AuthError as exc:
            self.login_password.clear()
            self._show_error(self.login_error, str(exc))
            return
        except DatabaseError as exc:
            self._show_error(self.login_error, f"Could not read the user database. {exc}")
            return

        self.login_password.clear()
        self.authenticated.emit(user)

    def _do_register(self) -> None:
        username = self.reg_username.text().strip()
        password, confirm = self.reg_password.text(), self.reg_confirm.text()
        if password != confirm:
            self._show_error(self.reg_error, "Passwords do not match.")
            return
        try:
            self.db.register_user(username, password)
        except AuthError as exc:
            self._show_error(self.reg_error, str(exc))
            return
        except DatabaseError as exc:
            self._show_error(self.reg_error, f"Could not save your account. {exc}")
            return

        QMessageBox.information(self, "Account created", "Your account is ready. Please sign in.")
        self.login_username.setText(username)
        for edit in (self.reg_username, self.reg_password, self.reg_confirm):
            edit.clear()
        self.show_login()
        self.login_password.setFocus()
