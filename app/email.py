import json
import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Optional
from urllib.request import Request, urlopen

from app.config import get_settings
from app.letters import is_chinese_text

logger = logging.getLogger(__name__)

OUTCOME_LABELS = {
    "happened": "它后来真的发生了",
    "partially_happened": "它有一部分成为了现实",
    "did_not_happen": "它并没有像担心的那样发生",
    "uncertain": "未来暂时还没有说清楚",
}


@dataclass(frozen=True)
class DeliveryResult:
    status: str
    error: Optional[str] = None


def send_result_email(
    *,
    recipient: str,
    question: str,
    outcome: str,
    summary: str,
    letter: str,
    public_url: Optional[str],
) -> DeliveryResult:
    settings = get_settings()
    if not settings.mail_enabled:
        return DeliveryResult(status="skipped")
    if not settings.mail_from:
        return DeliveryResult(status="failed", error="MAIL_FROM is required")

    subject = "🐌 DearFuture：一封来自未来的慢递到了"
    salutation = "亲爱的过去的你：" if is_chinese_text(question) else "Dear past you,"
    body = (
        f"你曾经把这件心事交给未来：\n{question}\n\n"
        f"小蜗牛从未来捎回一句话：\n"
        f"{OUTCOME_LABELS.get(outcome, '未来带回了一些新的线索')}\n\n"
        f"后来发生的故事：\n{summary}\n\n"
        f"{salutation}\n{letter}\n"
    )
    if public_url:
        body += f"\n查看公开页面：{public_url}\n"

    try:
        if settings.resend_api_key:
            return _send_with_resend(
                api_key=settings.resend_api_key,
                sender=settings.mail_from,
                recipient=recipient,
                subject=subject,
                body=body,
            )
        if not settings.smtp_host:
            return DeliveryResult(status="failed", error="RESEND_API_KEY or SMTP_HOST is required")
        return _send_with_smtp(
            sender=settings.mail_from,
            recipient=recipient,
            subject=subject,
            body=body,
        )
    except Exception as exc:
        logger.exception("Email delivery failed")
        return DeliveryResult(status="failed", error=str(exc)[:500])


def _send_with_resend(
    *, api_key: str, sender: str, recipient: str, subject: str, body: str
) -> DeliveryResult:
    payload = json.dumps(
        {
            "from": sender,
            "to": [recipient],
            "subject": subject,
            "text": body,
        }
    ).encode("utf-8")
    request = Request(
        "https://api.resend.com/emails",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "DearFuture/1.0",
        },
    )
    with urlopen(request, timeout=20) as response:
        if not 200 <= response.status < 300:
            return DeliveryResult(status="failed", error=f"Resend returned {response.status}")
    return DeliveryResult(status="sent")


def _send_with_smtp(*, sender: str, recipient: str, subject: str, body: str) -> DeliveryResult:
    settings = get_settings()
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        return DeliveryResult(status="sent")
    except Exception as exc:
        logger.exception("SMTP delivery failed")
        return DeliveryResult(status="failed", error=str(exc)[:500])
