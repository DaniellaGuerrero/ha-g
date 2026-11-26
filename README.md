# UtilKit - PyQt6 desktop app

Login/registration (SQLite + salted PBKDF2) and three utilities: URL Shortener, SMS & Email, Fake Data Generator.

## Setup

```bash
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

pip install -r requirements.txt     # PyQt6 + requests
python main.py
```

Requires Python 3.10+. The first launch creates `users.db` next to the code. Click **Create an account**, then sign in.

## Project layout

| File | Purpose |
|---|---|
| `main.py` | Entry point, theme, switches login <-> dashboard |
| `config_store.py`, `set_api_key.py` | Find / save the Resend and SimGate credentials (`~/.utilkit/config.json`, outside the project) |
| `database.py` | SQLite users + drafts, `os.urandom` salt, PBKDF2-SHA256 hashing |
| `auth_window.py` | Login / register screen |
| `dashboard.py` | Top nav + Home, Links, SMS & Email, Data pages |
| `api_client.py` | All network calls (TinyURL, SimGate, Resend, randomuser.me), no Qt code |
| `workers.py` | `QThread` helper - every network call runs off the UI thread |
| `widgets.py`, `icons.py`, `styles.py` | Reusable widgets, drawn icons, QSS theme |
| `assets/logo.png`, `assets/logo.ico` | UtilKit logo (window icon and brand tiles) |

## APIs

| Tool | API | Auth |
|---|---|---|
| URL Shortener | `https://tinyurl.com/api-create.php?url=...` | none |
| Fake Data | `https://randomuser.me/api/?results=N` | none |
| SMS | [SimGate](https://www.simgate.app/) (`POST https://api.simgate.app/v1/sms/send`) | `x-api-key` header + your phone's Device ID |
| Email | [Resend](https://resend.com/docs/api-reference/emails/send-email) (`POST https://api.resend.com/emails`) | Resend API key |

**SMS (SimGate):** create a SimGate account, install the SimGate Gateway app on an Android phone with a SIM, pair it with the QR code, then generate an API key.
Messages are sent from that phone's SIM. Enter the API key and the phone's Device ID under **Settings** in the SMS & Email page,
run `python set_api_key.py`, or set `SIMGATE_API_KEY` and `SIMGATE_DEVICE_ID`. If the phone is offline SimGate queues the message and the app shows "Queued".

**Email (Resend):** create an API key at resend.com and enter it under **Settings**, or set `RESEND_API_KEY` and optionally `RESEND_FROM`.
The From address must be on a domain you have verified in Resend. Without one, the app falls back to `onboarding@resend.dev`,
which Resend only allows for sending to your own account email.

**SMS & Email:** tick SMS, Email, or both, fill in the recipient(s), write one message and press *Send now*, *Schedule*
or *Save draft*. The right-hand panel has two live previews: a **Chat preview** that shows your message as you type and keeps a history
of what you send (with a status on each bubble, for example `SMS pending · Email ✓`), and an **Email preview** that shows
the From, To, subject and body as the recipient will see them. Each channel is sent separately and reported separately,
so one can fail without hiding the other. SMS is limited to 320 characters; an email-only message has no limit.
Settings are saved in `~/.utilkit/config.json` (outside the project, owner-only permissions).

## Notes

- randomuser.me has no employer data, so **Company, Job Title, Department and Business Email** are generated locally
  (stable per person). The other 8 fields come straight from the API.
- Each generation produces 10-50 records (`MIN_RECORDS` / `MAX_RECORDS` in `api_client.py`). Every generated record (all 12 fields) is saved to the `fake_records` table in `users.db`, linked to the signed-in user.
- *Schedule* uses an in-app timer, so the app must remain open. *Save draft* stores one draft per user in `users.db` (phone number, email address, subject and message).
- Delete `users.db` to reset all accounts.
