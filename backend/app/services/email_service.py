"""Sending email. Auth and notification code only call send(); the provider behind it can be swapped.

- ResendProvider: real delivery through the Resend REST API (needs RESEND_API_KEY).
- ConsoleProvider: used when there is no key (local dev, tests). Logs the message and keeps it in `sent`.
"""

import json
import logging
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from html import escape
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger("app.email")
APP_NAME = "Tasklane"


@dataclass
class Email:
    to: str
    subject: str
    html: str


class EmailProvider(Protocol):
    def send(self, email: Email) -> None: ...


class ResendProvider:
    def __init__(self, api_key: str, sender: str):
        self._api_key, self._sender = api_key, sender

    def send(self, email: Email) -> None:
        body = json.dumps({"from": self._sender, "to": [email.to], "subject": email.subject, "html": email.html})
        request = urllib.request.Request(
            "https://api.resend.com/emails",
            data=body.encode(),
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json", "User-Agent": "tasklane/1.0"},
            method="POST",
        )
        try:
            urllib.request.urlopen(request, timeout=10).read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Resend rejected the email ({exc.code}): {exc.read().decode()[:200]}") from exc


class ConsoleProvider:
    def __init__(self) -> None:
        self.sent: list[Email] = []

    def send(self, email: Email) -> None:
        self.sent.append(email)
        logger.warning("EMAIL (not sent, no RESEND_API_KEY) to=%s subject=%s\n%s", email.to, email.subject, email.html)


_provider: EmailProvider | None = None
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="email")


def get_provider() -> EmailProvider:
    global _provider
    if _provider is None:
        _provider = (
            ResendProvider(settings.RESEND_API_KEY, settings.EMAIL_FROM) if settings.RESEND_API_KEY else ConsoleProvider()
        )
    return _provider


def _deliver(email: Email) -> None:
    # An email problem must never break the request that triggered it.
    try:
        get_provider().send(email)
    except Exception as exc:
        logger.warning("Could not send email to %s: %s", email.to, exc)


def send(email: Email) -> None:
    if settings.EMAIL_ASYNC:
        _pool.submit(_deliver, email)
    else:
        _deliver(email)


def _layout(title: str, body_html: str, button: tuple[str, str] | None = None, footer: str = "") -> str:
    cta = (
        f'<p style="margin:24px 0"><a href="{escape(button[1])}" style="background:#0d9488;color:#fff;'
        f'padding:12px 22px;border-radius:8px;text-decoration:none;font-weight:600">{escape(button[0])}</a></p>'
        f'<p style="font-size:12px;color:#64748b">If the button does not work, copy this link:<br>{escape(button[1])}</p>'
        if button
        else ""
    )
    return (
        '<div style="font-family:Segoe UI,Arial,sans-serif;max-width:520px;margin:auto;padding:24px;color:#0f172a">'
        f'<h2 style="color:#0f766e;margin:0 0 16px">{APP_NAME}</h2><h3>{escape(title)}</h3>{body_html}{cta}'
        f'<p style="font-size:12px;color:#94a3b8;margin-top:28px">{footer}</p></div>'
    )


def verification_email(to: str, name: str, token: str) -> Email:
    link = f"{settings.APP_URL}/verify-email?token={token}"
    html = _layout(
        "Confirm your email address",
        f"<p>Hi {escape(name)}, welcome to {APP_NAME}. Please confirm your email to activate your account.</p>"
        f"<p>This link expires in {settings.VERIFY_TOKEN_HOURS} hours.</p>",
        ("Verify email", link),
        "If you did not create this account, you can ignore this email.",
    )
    return Email(to, f"Verify your email for {APP_NAME}", html)


def password_reset_email(to: str, name: str, token: str) -> Email:
    link = f"{settings.APP_URL}/reset-password?token={token}"
    html = _layout(
        "Reset your password",
        f"<p>Hi {escape(name)}, we received a request to reset your {APP_NAME} password.</p>"
        f"<p>This link works once and expires in {settings.RESET_TOKEN_MINUTES} minutes.</p>",
        ("Reset password", link),
        "Security warning: if you did not request this, ignore this email. Your password will not change "
        "and nobody can use the link without access to this inbox.",
    )
    return Email(to, f"Reset your {APP_NAME} password", html)


def notification_email(to: str, name: str, headline: str, detail: str, project_id: int) -> Email:
    link = f"{settings.APP_URL}/projects/{project_id}"
    html = _layout(
        headline,
        f"<p>Hi {escape(name)},</p><p>{escape(detail)}</p>",
        ("Open project", link),
        "You get this because you are involved in this project.",
    )
    return Email(to, f"[{APP_NAME}] {headline}", html)
