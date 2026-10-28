"""Email delivery of alerts. Optional: without an email setup alerts are only stored and shown.

Two ways to send, tried in this order: an HTTPS email API (Brevo or Resend, set with
EMAIL_API_KEY; many hosts block SMTP ports, HTTPS always works) and then plain SMTP.

An email is only ever sent to the address of a watch, about the project it watches.
"""

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from email.utils import parseaddr

import httpx

from app.config import Settings
from app.sentinel.models import Alert, Language

logger = logging.getLogger(__name__)
SMTP_TIMEOUT_SECONDS = 20
EMAIL_API_TIMEOUT_SECONDS = 20
BREVO_URL = "https://api.brevo.com/v3/smtp/email"
RESEND_URL = "https://api.resend.com/emails"

SUBJECTS: dict[Language, str] = {
    "en": "NeevCheck: a record changed for {project}",
    "hi": "NeevCheck: {project} का एक रिकॉर्ड बदला है",
}
SECTIONS: dict[Language, dict[str, str]] = {
    "en": {"added": "New", "removed": "No longer found", "changed": "Changed"},
    "hi": {"added": "नया", "removed": "अब नहीं मिला", "changed": "बदला"},
}
SCORE_LINE: dict[Language, str] = {
    "en": "NeevScore: {old} -> {new}",
    "hi": "NeevScore: {old} -> {new}",
}
NOT_RATED = "-"
STOP_LINE: dict[Language, str] = {
    "en": "Stop alerts for this project:",
    "hi": "इस प्रोजेक्ट के अलर्ट बंद करें:",
}
FOOTER: dict[Language, str] = {
    "en": "Public records as read by NeevCheck. Not legal or financial advice.",
    "hi": "NeevCheck द्वारा पढ़े गए सार्वजनिक रिकॉर्ड। यह कानूनी या वित्तीय सलाह नहीं है।",
}


def sender(settings: Settings) -> str:
    return settings.email_from or settings.smtp_from or ""


def api_configured(settings: Settings) -> bool:
    return bool(settings.email_api_key and settings.email_from)


def smtp_configured(settings: Settings) -> bool:
    return bool(settings.smtp_host and sender(settings))


def email_configured(settings: Settings) -> bool:
    """True when an alert can be mailed at all; otherwise it is only shown in the app."""
    return api_configured(settings) or smtp_configured(settings)


def stop_link(settings: Settings, token: str) -> str | None:
    """The page that stops a watch. None until the web app's address is configured."""
    if not settings.site_url:
        return None
    return f"{settings.site_url.rstrip('/')}/alerts/stop?token={token}"


def build_message(
    settings: Settings, to: str, language: Language, alert: Alert, stop_url: str | None = None
) -> EmailMessage:
    project = alert.project_name or alert.rera_id
    old, new = alert.old_display_score, alert.new_display_score
    scores = SCORE_LINE[language].format(
        old=old.value if old and old.value is not None else NOT_RATED,
        new=new.value if new and new.value is not None else NOT_RATED,
    )
    lines = [scores, ""]
    for name, changes in (
        ("added", alert.added),
        ("removed", alert.removed),
        ("changed", alert.changed),
    ):
        if changes:
            lines.append(f"{SECTIONS[language][name]}:")
            lines += [f"- {change.title}" for change in changes]
            lines.append("")
    lines.append(FOOTER[language])
    if stop_url:
        lines += ["", STOP_LINE[language], stop_url]
    message = EmailMessage()
    message["Subject"] = SUBJECTS[language].format(project=project)
    message["From"] = sender(settings)
    message["To"] = to
    message.set_content("\n".join(lines))
    return message


def _send(settings: Settings, message: EmailMessage) -> None:
    with smtplib.SMTP(
        settings.smtp_host or "", settings.smtp_port, timeout=SMTP_TIMEOUT_SECONDS
    ) as server:
        server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password.get_secret_value())
        server.send_message(message)


def _api_request(settings: Settings, message: EmailMessage) -> tuple[str, dict[str, str], object]:
    """The URL, headers and JSON body for the configured provider."""
    assert settings.email_api_key  # callers check api_configured first
    key = settings.email_api_key.get_secret_value()
    subject, text, to = str(message["Subject"]), message.get_content(), str(message["To"])
    if settings.email_provider == "resend":
        body = {"from": sender(settings), "to": [to], "subject": subject, "text": text}
        return RESEND_URL, {"Authorization": f"Bearer {key}"}, body
    name, address = parseaddr(sender(settings))
    from_ = {"email": address, **({"name": name} if name else {})}
    body = {"sender": from_, "to": [{"email": to}], "subject": subject, "textContent": text}
    return BREVO_URL, {"api-key": key}, body


async def _send_through_api(settings: Settings, message: EmailMessage) -> None:
    url, headers, body = _api_request(settings, message)
    async with httpx.AsyncClient(timeout=EMAIL_API_TIMEOUT_SECONDS) as client:
        response = await client.post(url, headers=headers, json=body)
    response.raise_for_status()


async def send_alert(
    settings: Settings, to: str, language: Language, alert: Alert, stop_url: str | None = None
) -> bool:
    """True when the email went out; False when no email is set up or sending failed."""
    if not email_configured(settings):
        return False
    message = build_message(settings, to, language, alert, stop_url)
    # The alert is already stored and shown in the app, so a mail failure loses nothing.
    if api_configured(settings):
        try:
            await _send_through_api(settings, message)
            return True
        except httpx.HTTPError as error:
            # The key is only ever in a header, which httpx does not put in its error text.
            logger.warning("Email API refused the alert for %s (%s)", alert.rera_id, error)
    if smtp_configured(settings):
        try:
            await asyncio.to_thread(_send, settings, message)
            return True
        except (OSError, smtplib.SMTPException):
            logger.warning("Could not email the alert for %s", alert.rera_id)
    return False
