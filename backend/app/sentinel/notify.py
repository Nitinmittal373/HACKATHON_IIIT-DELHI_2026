"""Email delivery of alerts. Optional: without SMTP settings alerts are only stored and shown.

An email is only ever sent to the address of a watch, about the project it watches.
"""

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.config import Settings
from app.sentinel.models import Alert, Language

logger = logging.getLogger(__name__)
SMTP_TIMEOUT_SECONDS = 20

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
FOOTER: dict[Language, str] = {
    "en": "Public records as read by NeevCheck. Not legal or financial advice.",
    "hi": "NeevCheck द्वारा पढ़े गए सार्वजनिक रिकॉर्ड। यह कानूनी या वित्तीय सलाह नहीं है।",
}


def smtp_configured(settings: Settings) -> bool:
    return bool(settings.smtp_host and settings.smtp_from)


def build_message(settings: Settings, to: str, language: Language, alert: Alert) -> EmailMessage:
    project = alert.project_name or alert.rera_id
    old, new = alert.old_display_score, alert.new_display_score
    scores = SCORE_LINE[language].format(
        old=old.value if old else NOT_RATED, new=new.value if new else NOT_RATED
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
    message = EmailMessage()
    message["Subject"] = SUBJECTS[language].format(project=project)
    message["From"] = settings.smtp_from or ""
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


async def send_alert(settings: Settings, to: str, language: Language, alert: Alert) -> bool:
    """True when the email went out; False when SMTP is not set up or sending failed."""
    if not smtp_configured(settings):
        return False
    try:
        await asyncio.to_thread(_send, settings, build_message(settings, to, language, alert))
    except (OSError, smtplib.SMTPException):
        # The alert is already stored and shown in the app, so a mail failure loses nothing.
        logger.warning("Could not email the alert for %s", alert.rera_id)
        return False
    return True
