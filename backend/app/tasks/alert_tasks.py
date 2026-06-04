from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict

from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)

CONDITION_OPS = {
    "gt": lambda v, t: v > t,
    "lt": lambda v, t: v < t,
    "gte": lambda v, t: v >= t,
    "lte": lambda v, t: v <= t,
    "eq": lambda v, t: v == t,
}


@celery_app.task(name="app.tasks.alert_tasks.evaluate_all_alerts", bind=True)
def evaluate_all_alerts(self) -> Dict[str, Any]:
    """Celery Beat task: evaluate every active alert."""
    try:
        evaluated = asyncio.run(_run_evaluations())
        logger.info("alerts_evaluated", count=evaluated)
        return {"evaluated": evaluated}
    except Exception as exc:
        logger.error("alert_evaluation_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=30)


async def _run_evaluations() -> int:
    from app.db.session import AsyncSessionLocal
    from app.repositories.alert_repository import (
        AlertRepository,
        AlertHistoryRepository,
    )
    from app.models.alert import AlertHistory
    from app.services.notification_service import send_alert_notification

    async with AsyncSessionLocal() as session:
        alert_repo = AlertRepository(session)
        history_repo = AlertHistoryRepository(session)
        alerts = await alert_repo.get_active_alerts()

        now = datetime.now(timezone.utc)
        count = 0

        for alert in alerts:
            if alert.muted_until and alert.muted_until > now:
                continue

            try:
                value = await _evaluate_metric(alert, session)
                op = CONDITION_OPS.get(alert.condition)
                triggered = op(value, alert.threshold) if op else False

                update_data: Dict[str, Any] = {"last_evaluated_at": now}

                if triggered:
                    update_data["status"] = "triggered"
                    update_data["last_triggered_at"] = now

                    hist = AlertHistory(
                        alert_id=alert.id,
                        triggered_at=now,
                        triggered_value=value,
                        threshold=alert.threshold,
                        message=f"Value {value:.2f} {alert.condition} threshold {alert.threshold:.2f}",
                    )
                    session.add(hist)

                    for ch in alert.notification_channels:
                        await send_alert_notification(
                            channel_type=ch.channel_type,
                            config=ch.config,
                            alert_name=alert.name,
                            triggered_value=value,
                            threshold=alert.threshold,
                            condition=alert.condition,
                        )
                elif alert.status == "triggered":
                    update_data["status"] = "active"

                await alert_repo.update(alert, update_data)
                count += 1
            except Exception as e:
                logger.error("alert_eval_error", alert_id=str(alert.id), error=str(e))

        await session.commit()
        return count


async def _evaluate_metric(alert: Any, session: Any) -> float:
    """Execute the metric query and return the current value."""
    from sqlalchemy import text
    from datetime import timedelta

    query_cfg = alert.metric_query
    event_name = query_cfg.get("event_name", "")
    aggregation = query_cfg.get("aggregation", "count")
    time_window = query_cfg.get("time_window_minutes", 10)
    org_id = str(alert.organization_id)

    now = datetime.now(timezone.utc)
    start = now - timedelta(minutes=time_window)

    agg_map = {
        "count": "COUNT(*)",
        "unique": "COUNT(DISTINCT user_id)",
    }
    agg_expr = agg_map.get(aggregation, "COUNT(*)")

    sql = f"""
        SELECT {agg_expr}
        FROM events
        WHERE organization_id = '{org_id}'
          AND event_name = '{event_name}'
          AND timestamp >= '{start.isoformat()}'
          AND timestamp <= '{now.isoformat()}'
    """
    result = await session.execute(text(sql))
    row = result.fetchone()
    return float(row[0]) if row and row[0] is not None else 0.0


@celery_app.task(name="app.tasks.alert_tasks.send_alert_notification_task", bind=True)
def send_alert_notification_task(
    self,
    channel_type: str,
    config: Dict[str, Any],
    alert_name: str,
    triggered_value: float,
    threshold: float,
    condition: str,
) -> bool:
    from app.services.notification_service import send_alert_notification

    return asyncio.run(
        send_alert_notification(
            channel_type, config, alert_name, triggered_value, threshold, condition
        )
    )
