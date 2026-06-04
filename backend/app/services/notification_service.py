from __future__ import annotations

from typing import Any, Dict, List, Optional

import aiohttp
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def send_email(
    to: List[str],
    subject: str,
    html_body: str,
    from_addr: Optional[str] = None,
) -> bool:
    if not settings.SMTP_USER:
        logger.warning("email_skipped_no_smtp_config")
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = from_addr or settings.SMTP_FROM
    message["To"] = ", ".join(to)
    message.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_TLS,
        )
        logger.info("email_sent", recipients=to, subject=subject)
        return True
    except Exception as e:
        logger.error("email_send_failed", error=str(e), recipients=to)
        return False


async def send_webhook(
    url: str,
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers=headers or {"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                success = response.status < 400
                if not success:
                    logger.warning(
                        "webhook_delivery_failed",
                        url=url,
                        status=response.status,
                    )
                return success
    except Exception as e:
        logger.error("webhook_delivery_error", url=url, error=str(e))
        return False


async def send_alert_notification(
    channel_type: str,
    config: Dict[str, Any],
    alert_name: str,
    triggered_value: float,
    threshold: float,
    condition: str,
) -> bool:
    message_text = (
        f"Alert '{alert_name}' triggered: value {triggered_value:.2f} "
        f"{condition} threshold {threshold:.2f}"
    )

    if channel_type == "email":
        recipients = config.get("to", [])
        if not recipients:
            return False
        html = f"<p>{message_text}</p>"
        return await send_email(recipients, f"[WexaAI Alert] {alert_name}", html)

    elif channel_type == "webhook":
        url = config.get("url")
        if not url:
            return False
        payload = {
            "text": message_text,  # Slack-compatible
            "alert_name": alert_name,
            "triggered_value": triggered_value,
            "threshold": threshold,
            "condition": condition,
        }
        return await send_webhook(url, payload, config.get("headers"))

    # in_app notifications are handled via WebSocket push
    return True
