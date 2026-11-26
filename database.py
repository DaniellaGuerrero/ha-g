from __future__ import annotations

import hashlib
import hmac
import os
import re
import sqlite3
import json
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

DB_PATH = Path(__file__).resolve().parent / "users.db"
PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16
MIN_PASSWORD_LENGTH = 8
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,20}$")


class DatabaseError(Exception):
    pass


class AuthError(Exception):
    pass


@dataclass(frozen=True)
class User:
    id: int
    username: str


def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    salt = salt if salt is not None else os.urandom(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return digest.hex(), salt.hex()


class Database:

    def __init__(self, path: Path | str = DB_PATH) -> None:
        self.path = str(path)
        self._init_schema()


    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = None
        try:
            conn = sqlite3.connect(self.path, timeout=10)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except sqlite3.IntegrityError:
            if conn:
                conn.rollback()
            raise
        except sqlite3.Error as exc:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Database error: {exc}") from exc
        finally:
            if conn:
                conn.close()

    def _migrate_old_schema(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            conn = sqlite3.connect(self.path)
            try:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(users)")]
            finally:
                conn.close()
        except sqlite3.Error:
            return
        if "email" in cols:
            backup = self.path + ".old"
            try:
                os.replace(self.path, backup)
            except OSError as exc:
                raise DatabaseError(f"Could not upgrade the old database: {exc}") from exc

    def _init_schema(self) -> None:
        self._migrate_old_schema()
        try:
            with self._connect() as conn:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id            INTEGER PRIMARY KEY AUTOINCREMENT,
                        username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                        password_hash TEXT    NOT NULL,
                        salt          TEXT    NOT NULL,
                        created_at    TEXT    NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS drafts (
                        id         INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        phone      TEXT    NOT NULL,
                        body       TEXT    NOT NULL,
                        created_at TEXT    NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS fake_records (
                        id         INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        batch_id   TEXT    NOT NULL,
                        data       TEXT    NOT NULL,
                        created_at TEXT    NOT NULL
                    );
                    """
                )
                cols = {r[1] for r in conn.execute("PRAGMA table_info(drafts)")}
                for name in ("email", "subject"):
                    if name not in cols:
                        conn.execute(f"ALTER TABLE drafts ADD COLUMN {name} TEXT NOT NULL DEFAULT ''")
        except sqlite3.IntegrityError as exc:
            raise DatabaseError(str(exc)) from exc


    def register_user(self, username: str, password: str) -> User:
        username = username.strip()
        if not USERNAME_RE.match(username):
            raise AuthError("Username must be 3-20 characters: letters, numbers, . _ or -")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")

        pw_hash, salt_hex = hash_password(password)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "INSERT INTO users (username, password_hash, salt, created_at) VALUES (?, ?, ?, ?)",
                    (username, pw_hash, salt_hex, now),
                )
                return User(id=cur.lastrowid, username=username)
        except sqlite3.IntegrityError:
            raise AuthError("That username is already taken.") from None

    def authenticate(self, username: str, password: str) -> User:
        generic = AuthError("Invalid username or password.")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, salt FROM users WHERE username = ?",
                (username.strip(),),
            ).fetchone()

        if row is None:
            hash_password(password)
            raise generic

        candidate, _ = hash_password(password, bytes.fromhex(row["salt"]))
        if not hmac.compare_digest(candidate, row["password_hash"]):
            raise generic
        return User(id=row["id"], username=row["username"])


    def save_draft(self, user_id: int, phone: str, body: str, email: str = "", subject: str = "") -> None:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO drafts (user_id, phone, body, email, subject, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, phone, body, email, subject, now),
            )


    def save_fake_records(self, user_id: int, records: list[dict]) -> int:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        batch_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        rows = [(user_id, batch_id, json.dumps(r, ensure_ascii=False), now) for r in records]
        try:
            with self._connect() as conn:
                conn.executemany(
                    "INSERT INTO fake_records (user_id, batch_id, data, created_at) VALUES (?, ?, ?, ?)",
                    rows,
                )
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc
        return len(rows)

    def count_fake_records(self, user_id: int) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM fake_records WHERE user_id = ?", (user_id,)).fetchone()
        return int(row["n"])

    def latest_draft(self, user_id: int) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT phone, body, email, subject FROM drafts WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None
