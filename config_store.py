from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("UTILKIT_CONFIG_DIR", Path.home() / ".utilkit"))
CONFIG_PATH = CONFIG_DIR / "config.json"
SMS_KEY = "simgate"
EMAIL_KEY = "resend"
SMS_ENV = {
    "api_key": "SIMGATE_API_KEY",
    "device_id": "SIMGATE_DEVICE_ID",
}
EMAIL_ENV = {
    "api_key": "RESEND_API_KEY",
    "sender": "RESEND_FROM",
}


def _read() -> dict:
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, CONFIG_PATH)


def _load(key: str, env_map: dict) -> dict:
    saved = _read().get(key)
    saved = saved if isinstance(saved, dict) else {}
    return {field: str(os.environ.get(env) or saved.get(field) or "").strip() for field, env in env_map.items()}


def _save(key: str, env_map: dict, settings: dict) -> None:
    data = _read()
    data[key] = {field: str(settings.get(field, "")).strip() for field in env_map}
    _write(data)


def get_sms_settings() -> dict:
    return _load(SMS_KEY, SMS_ENV)


def save_sms_settings(settings: dict) -> None:
    _save(SMS_KEY, SMS_ENV, settings)


def get_email_settings() -> dict:
    return _load(EMAIL_KEY, EMAIL_ENV)


def save_email_settings(settings: dict) -> None:
    _save(EMAIL_KEY, EMAIL_ENV, settings)
