from __future__ import annotations

import random
import re
import time
import unicodedata
import uuid
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

TINYURL_ENDPOINT = "https://tinyurl.com/api-create.php"
RANDOMUSER_ENDPOINT = "https://randomuser.me/api/"
TIMEOUT = (5, 15)
MIN_RECORDS = 10
MAX_RECORDS = 50


class ApiError(Exception):
    pass


def normalize_url(raw: str) -> str:
    url = raw.strip()
    if not url:
        raise ApiError("Please paste a URL first.")
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "https://" + url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or "." not in parsed.netloc:
        raise ApiError("That doesn't look like a valid web address.")
    return url


def shorten_url(long_url: str) -> str:
    url = normalize_url(long_url)
    try:
        resp = requests.get(TINYURL_ENDPOINT, params={"url": url}, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise ApiError(f"Could not reach TinyURL: {exc}") from exc
    short = resp.text.strip()
    if not short.startswith("http"):
        raise ApiError(f"TinyURL returned an unexpected response: {short[:120]}")
    return short


SIMGATE_URL = "https://api.simgate.app"
SMS_TIMEOUT = (5, 30)


@dataclass
class SmsConfig:
    api_key: str = ""
    device_id: str = ""

    @property
    def ready(self) -> bool:
        return bool(self.api_key.strip() and self.device_id.strip())

    @classmethod
    def from_settings(cls, settings: dict) -> "SmsConfig":
        return cls(
            api_key=str(settings.get("api_key", "")).strip(),
            device_id=str(settings.get("device_id", "")).strip(),
        )


def send_sms(config: SmsConfig, to_number: str, body: str) -> dict:
    if not body.strip():
        raise ApiError("The message is empty.")
    if not config.ready:
        raise ApiError("SimGate isn't set up yet. Open Settings and enter your API key and device ID.")
    if not re.match(r"^\+\d{8,15}$", to_number):
        raise ApiError("Enter the phone number in international format, e.g. +639171234567.")

    try:
        resp = requests.post(
            f"{SIMGATE_URL}/v1/sms/send",
            headers={"x-api-key": config.api_key.strip(), "Content-Type": "application/json"},
            json={"deviceId": config.device_id.strip(), "phoneNumber": to_number, "message": body},
            timeout=SMS_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ApiError(f"Could not reach SimGate: {exc}") from exc

    try:
        payload = resp.json()
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    detail = payload.get("message") or payload.get("error") or resp.text[:200]
    if resp.status_code == 401:
        raise ApiError(f"SimGate rejected the API key: {detail}")
    if resp.status_code == 404:
        raise ApiError(f"SimGate doesn't know that device ID: {detail}")
    if resp.status_code == 403:
        raise ApiError(f"SimGate refused the message (plan quota exceeded?): {detail}")
    if resp.status_code >= 400 or payload.get("success") is False:
        raise ApiError(f"SimGate rejected the message ({resp.status_code}): {detail}")

    queued = resp.status_code == 202 or bool(payload.get("queued"))
    return {
        "sid": str(payload.get("messageId") or ""),
        "status": "Queued" if queued else "Sent",
        "detail": str(payload.get("connectionStatus") or ""),
    }


RESEND_ENDPOINT = "https://api.resend.com/emails"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EMAIL_TIMEOUT = (5, 20)
DEFAULT_SENDER = "onboarding@resend.dev"


@dataclass
class EmailConfig:
    api_key: str = ""
    sender: str = ""

    @classmethod
    def from_settings(cls, settings: dict) -> "EmailConfig":
        return cls(
            api_key=str(settings.get("api_key", "")).strip(),
            sender=str(settings.get("sender", "")).strip(),
        )

    @property
    def ready(self) -> bool:
        return bool(self.api_key)

    @property
    def from_address(self) -> str:
        return self.sender or DEFAULT_SENDER


def is_valid_email(address: str) -> bool:
    return bool(EMAIL_RE.match(address.strip()))


def _sender_address(sender: str) -> str:
    match = re.search(r"<([^>]+)>", sender)
    return (match.group(1) if match else sender).strip()


def send_email(config: EmailConfig, to_address: str, subject: str, body: str) -> dict:
    to_address = to_address.strip()
    if not body.strip():
        raise ApiError("The message is empty.")
    if not is_valid_email(to_address):
        raise ApiError("Please enter a valid email address.")
    if not config.ready:
        raise ApiError("Email isn't set up yet. Open Settings and enter your Resend API key.")
    if not is_valid_email(_sender_address(config.from_address)):
        raise ApiError("Set a valid From address in Settings.")

    subject = subject.strip() or "(no subject)"
    try:
        resp = requests.post(
            RESEND_ENDPOINT,
            headers={"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"},
            json={"from": config.from_address, "to": [to_address], "subject": subject, "text": body},
            timeout=EMAIL_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ApiError(f"Could not reach Resend: {exc}") from exc

    try:
        payload = resp.json()
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    if resp.status_code >= 400:
        detail = payload.get("message") or payload.get("error") or resp.text[:200]
        raise ApiError(f"Resend rejected the email ({resp.status_code}): {detail}")
    return {"to": to_address, "subject": subject, "id": str(payload.get("id") or "")}


DATA_FIELDS: list[tuple[str, str, str]] = [
    ("full_name", "Full Name", "First name / Last name"),
    ("gender", "Gender", ""),
    ("dob", "Date of Birth & Age", ""),
    ("email", "Email Address", ""),
    ("phone", "Phone Number", "Country / local format"),
    ("street", "Street Address", "House, street, apartment / suite"),
    ("city", "City, State / Province", ""),
    ("postal", "Postal / ZIP Code", ""),
    ("company", "Company Name", ""),
    ("job", "Job Title", ""),
    ("department", "Department", ""),
    ("biz_email", "Business Email", ""),
]
FIELD_LABELS = {key: label for key, label, _ in DATA_FIELDS}

_JOBS = {
    "Engineering": ["Software Engineer", "QA Analyst", "DevOps Engineer", "Data Engineer"],
    "Marketing": ["Marketing Manager", "Content Strategist", "SEO Specialist"],
    "Sales": ["Account Executive", "Sales Representative", "Business Developer"],
    "Finance": ["Financial Analyst", "Accountant", "Controller"],
    "Human Resources": ["HR Generalist", "Recruiter", "People Partner"],
    "Operations": ["Operations Manager", "Logistics Coordinator", "Project Manager"],
    "Design": ["Product Designer", "UX Researcher", "Graphic Designer"],
}
_COMPANY_A = ["Northwind", "Bluepeak", "Evergreen", "Lumina", "Ironclad", "Harbor", "Quanta", "Brightside"]
_COMPANY_B = ["Systems", "Labs", "Logistics", "Partners", "Holdings", "Digital", "Group", "Works"]


def _ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def _company_profile(user: dict) -> tuple[str, str, str]:
    rnd = random.Random(user.get("email", ""))
    department = rnd.choice(list(_JOBS))
    job = rnd.choice(_JOBS[department])
    company = f"{rnd.choice(_COMPANY_A)} {rnd.choice(_COMPANY_B)}"
    return company, job, department


def _full_name(u: dict) -> str:
    n = u.get("name", {})
    return f"{n.get('first', '')} {n.get('last', '')}".strip()


def _dob(u: dict) -> str:
    d = u.get("dob", {})
    return f"{str(d.get('date', ''))[:10]}  (age {d.get('age', '?')})"


def _street(u: dict) -> str:
    s = u.get("location", {}).get("street", {})
    return f"{s.get('number', '')} {s.get('name', '')}".strip()


def _city(u: dict) -> str:
    loc = u.get("location", {})
    return f"{loc.get('city', '')}, {loc.get('state', '')}".strip(", ")


def _biz_email(u: dict) -> str:
    n = u.get("name", {})
    company = _company_profile(u)[0]
    domain = re.sub(r"[^a-z0-9]", "", _ascii(company).lower()) + ".com"
    local = re.sub(r"[^a-z0-9.]", "", _ascii(f"{n.get('first', '')}.{n.get('last', '')}").lower())
    return f"{local}@{domain}"


_EXTRACTORS = {
    "full_name": _full_name,
    "gender": lambda u: str(u.get("gender", "")).capitalize(),
    "dob": _dob,
    "email": lambda u: u.get("email", ""),
    "phone": lambda u: u.get("phone", ""),
    "street": _street,
    "city": _city,
    "postal": lambda u: str(u.get("location", {}).get("postcode", "")),
    "company": lambda u: _company_profile(u)[0],
    "job": lambda u: _company_profile(u)[1],
    "department": lambda u: _company_profile(u)[2],
    "biz_email": _biz_email,
}


def fetch_random_users(count: int) -> list[dict]:
    count = max(MIN_RECORDS, min(MAX_RECORDS, int(count)))
    params = {
        "results": count,
        "nat": "us,gb,ca,au",
        "inc": "gender,name,location,email,dob,phone",
    }
    try:
        resp = requests.get(RANDOMUSER_ENDPOINT, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as exc:
        raise ApiError(f"Could not reach randomuser.me: {exc}") from exc
    except ValueError as exc:
        raise ApiError("randomuser.me returned invalid JSON.") from exc

    results = payload.get("results")
    if not isinstance(results, list) or not results:
        raise ApiError(f"randomuser.me returned no data: {payload.get('error', 'unknown error')}")
    return results


def build_table(users: list[dict], keys: list[str]) -> tuple[list[str], list[list[str]]]:
    ordered = [k for k, _, _ in DATA_FIELDS if k in keys]
    headers = [FIELD_LABELS[k] for k in ordered]
    rows = [[str(_EXTRACTORS[k](u)) for k in ordered] for u in users]
    return headers, rows
