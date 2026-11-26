from __future__ import annotations

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication, QMessageBox

from auth_window import AuthWindow
from dashboard import DashboardWindow
from database import Database, DatabaseError, User
from icons import ensure_style_assets, logo_icon
from styles import build_stylesheet
from workers import wait_for_workers


def _excepthook(exc_type, exc, tb) -> None:
    traceback.print_exception(exc_type, exc, tb)
    try:
        QMessageBox.critical(None, "Unexpected error", f"{exc_type.__name__}: {exc}")
    except Exception:
        pass


class AppController:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.dashboard: DashboardWindow | None = None
        self._retired: list[DashboardWindow] = []
        self.auth = AuthWindow(db)
        self.auth.authenticated.connect(self._on_login)

    def start(self) -> None:
        self.auth.show()

    def _on_login(self, user: User) -> None:
        self.dashboard = DashboardWindow(user, self.db)
        self.dashboard.logout_requested.connect(self._on_logout)
        self.dashboard.show()
        self.auth.hide()

    def _on_logout(self) -> None:
        old = self.dashboard
        self.auth.reset()
        self.auth.show()
        if old is not None:
            old.close()
            self._retired.append(old)
        self.dashboard = None


def main() -> int:
    sys.excepthook = _excepthook
    app = QApplication(sys.argv)
    app.setApplicationName("UtilKit")
    app.setWindowIcon(logo_icon())

    font = QFont()
    font.setFamilies(["Manrope", "Segoe UI", "Helvetica Neue", "Ubuntu", "Arial"])
    font.setPixelSize(13)
    app.setFont(font)

    palette = app.palette()
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#9AA6BF"))
    app.setPalette(palette)
    app.setStyleSheet(build_stylesheet(ensure_style_assets()))

    try:
        db = Database()
    except DatabaseError as exc:
        QMessageBox.critical(None, "Database error", f"Could not open users.db:\n{exc}")
        return 1

    controller = AppController(db)
    controller.start()
    app.aboutToQuit.connect(wait_for_workers)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
