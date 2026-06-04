from __future__ import annotations

import asyncio
import io
import os
from datetime import datetime, timezone
from typing import Any, Dict

from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)

CRON_MAP = {
    "daily": "0 8 * * *",
    "weekly": "0 8 * * 1",
    "monthly": "0 8 1 * *",
}


@celery_app.task(name="app.tasks.report_tasks.run_scheduled_reports", bind=True)
def run_scheduled_reports(self) -> Dict[str, Any]:
    """Celery Beat task: trigger any scheduled reports due to run."""
    try:
        triggered = asyncio.run(_check_and_trigger_reports())
        return {"triggered": triggered}
    except Exception as exc:
        logger.error("scheduled_reports_check_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)


async def _check_and_trigger_reports() -> int:
    from app.db.session import AsyncSessionLocal
    from app.models.report import ReportSchedule, Report
    from sqlalchemy import select

    now = datetime.now(timezone.utc)
    count = 0

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ReportSchedule).where(
                ReportSchedule.is_active.is_(True),
                ReportSchedule.deleted_at.is_(None),
                ReportSchedule.next_run_at <= now,
            )
        )
        schedules = list(result.scalars().all())

        for sched in schedules:
            report = Report(
                organization_id=sched.organization_id,
                schedule_id=sched.id,
                dashboard_id=sched.dashboard_id,
                status="pending",
                format=sched.format,
            )
            session.add(report)
            await session.flush()

            # Update next run
            sched.last_run_at = now
            sched.next_run_at = _compute_next_run(sched.frequency)
            count += 1

            # Dispatch generation task
            generate_report.delay(str(report.id))

        await session.commit()

    return count


def _compute_next_run(frequency: str) -> datetime:
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    if frequency == "daily":
        return now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(
            days=1
        )
    elif frequency == "weekly":
        days_until_monday = (7 - now.weekday()) % 7 or 7
        return now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(
            days=days_until_monday
        )
    else:  # monthly
        import calendar

        year = now.year + (1 if now.month == 12 else 0)
        month = 1 if now.month == 12 else now.month + 1
        return now.replace(
            year=year, month=month, day=1, hour=8, minute=0, second=0, microsecond=0
        )


@celery_app.task(
    name="app.tasks.report_tasks.generate_report",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def generate_report(self, report_id: str) -> Dict[str, Any]:
    """Generate a PDF/PNG report for a dashboard."""
    try:
        result = asyncio.run(_generate_report_async(report_id))
        return result
    except Exception as exc:
        logger.error("report_generation_failed", report_id=report_id, error=str(exc))
        asyncio.run(_mark_report_failed(report_id, str(exc)))
        raise self.retry(exc=exc)


async def _generate_report_async(report_id: str) -> Dict[str, Any]:
    from app.db.session import AsyncSessionLocal
    from app.models.report import Report
    from app.services.notification_service import send_email
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    import uuid

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            __import__("sqlalchemy", fromlist=["select"])
            .select(Report)
            .where(Report.id == uuid.UUID(report_id))
        )
        report = result.scalar_one_or_none()
        if not report:
            return {"error": "Report not found"}

        await session.execute(
            __import__("sqlalchemy", fromlist=["update"])
            .update(Report)
            .where(Report.id == report.id)
            .values(status="processing")
        )
        await session.commit()

    # Generate simple PDF
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setTitle("WexaAI Dashboard Report")
    c.drawString(72, 750, "WexaAI Analytics Report")
    c.drawString(72, 730, f"Generated: {datetime.now(timezone.utc).isoformat()}")
    c.drawString(72, 710, f"Dashboard ID: {report.dashboard_id}")
    c.save()

    file_content = buf.getvalue()
    reports_dir = "/tmp/reports"
    os.makedirs(reports_dir, exist_ok=True)
    file_path = f"{reports_dir}/{report_id}.pdf"

    with open(file_path, "wb") as f:
        f.write(file_content)

    async with AsyncSessionLocal() as session:
        await session.execute(
            __import__("sqlalchemy", fromlist=["update"])
            .update(Report)
            .where(Report.id == uuid.UUID(report_id))
            .values(
                status="completed",
                file_path=file_path,
                file_size_bytes=len(file_content),
                generated_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

    logger.info("report_generated", report_id=report_id)
    return {"report_id": report_id, "file_path": file_path}


async def _mark_report_failed(report_id: str, error: str) -> None:
    from app.db.session import AsyncSessionLocal
    from app.models.report import Report
    import uuid

    async with AsyncSessionLocal() as session:
        await session.execute(
            __import__("sqlalchemy", fromlist=["update"])
            .update(Report)
            .where(Report.id == uuid.UUID(report_id))
            .values(status="failed", error_message=error)
        )
        await session.commit()
