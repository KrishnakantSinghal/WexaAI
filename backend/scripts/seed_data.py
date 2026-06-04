"""Seed temporary demo data: event source, ~2k events, saved query, dashboard, widgets.

Run inside the api container:
    docker compose exec api python -m scripts.seed_data
"""

from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db import base as _models_import  # noqa: F401 — register all mappers
from app.db.session import AsyncSessionLocal
from app.models.dashboard import Dashboard, SavedQuery
from app.models.event import Event, EventSource
from app.models.organization import Organization
from app.models.widget import Widget
from app.models.user import User

EVENT_NAMES = [
    "page_view",
    "signup",
    "login",
    "purchase",
    "add_to_cart",
    "checkout_started",
    "checkout_completed",
    "video_play",
    "search",
    "share",
]

PAGES = ["/", "/pricing", "/features", "/docs", "/blog", "/about", "/contact"]
COUNTRIES = ["US", "GB", "IN", "DE", "FR", "JP", "BR", "CA", "AU"]
DEVICES = ["desktop", "mobile", "tablet"]
BROWSERS = ["chrome", "safari", "firefox", "edge"]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # 1. find existing org + user (created via signup)
        org = (await db.execute(select(Organization).limit(1))).scalar_one_or_none()
        user = (await db.execute(select(User).limit(1))).scalar_one_or_none()
        if not org or not user:
            print("ERROR: no organization/user found. Sign up first.")
            return

        print(f"Seeding for org={org.name} ({org.id}), user={user.email}")

        # 2. event source
        existing_src = (
            await db.execute(
                select(EventSource).where(EventSource.organization_id == org.id)
            )
        ).scalar_one_or_none()
        if existing_src:
            source = existing_src
            print(f"  Using existing source: {source.name}")
        else:
            source = EventSource(
                organization_id=org.id,
                name="Web Tracker",
                source_type="api",
                description="Auto-seeded demo event source",
                config={"version": "1.0", "sdk": "web-js"},
                is_active=True,
            )
            db.add(source)
            await db.flush()
            print(f"  Created source: {source.name}")

        # 3. events — last 14 days, ~150 per day
        now = datetime.now(timezone.utc)
        existing_count = (
            await db.execute(
                select(Event).where(Event.organization_id == org.id).limit(1)
            )
        ).scalar_one_or_none()
        if existing_count:
            print("  Events already exist — skipping event seed.")
        else:
            batch = []
            total = 0
            for days_ago in range(14, -1, -1):
                day_count = random.randint(80, 220)
                for _ in range(day_count):
                    ts = now - timedelta(
                        days=days_ago,
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59),
                        seconds=random.randint(0, 59),
                    )
                    event_name = random.choices(
                        EVENT_NAMES,
                        weights=[40, 5, 15, 3, 10, 5, 4, 8, 6, 4],
                        k=1,
                    )[0]
                    props: dict = {
                        "page": random.choice(PAGES),
                        "country": random.choice(COUNTRIES),
                        "device": random.choice(DEVICES),
                        "browser": random.choice(BROWSERS),
                    }
                    if event_name == "purchase":
                        props["amount"] = round(random.uniform(9.99, 499.99), 2)
                        props["currency"] = "USD"
                    elif event_name == "search":
                        props["query"] = random.choice(
                            ["pricing", "docs", "api", "tutorial", "login help"]
                        )

                    batch.append(
                        Event(
                            organization_id=org.id,
                            source_id=source.id,
                            event_name=event_name,
                            timestamp=ts,
                            properties=props,
                            user_id=f"user_{random.randint(1, 250)}",
                            session_id=f"sess_{uuid.uuid4().hex[:12]}",
                            ip_address=f"192.0.2.{random.randint(1, 254)}",
                            user_agent="Mozilla/5.0 (DemoSeed)",
                            created_at=ts,
                        )
                    )
                    total += 1
                    if len(batch) >= 500:
                        db.add_all(batch)
                        await db.flush()
                        batch = []
            if batch:
                db.add_all(batch)
                await db.flush()
            print(f"  Inserted {total} events across 15 days")

        # 4. saved queries
        sq_pageviews = SavedQuery(
            organization_id=org.id,
            created_by_id=user.id,
            name="Daily Page Views",
            description="Count of page_view events per day",
            query_config={
                "event_name": "page_view",
                "aggregation": "count",
                "group_by": "day",
                "time_range": "14d",
                "filters": [],
            },
        )
        sq_revenue = SavedQuery(
            organization_id=org.id,
            created_by_id=user.id,
            name="Daily Revenue",
            description="Sum of purchase amounts per day",
            query_config={
                "event_name": "purchase",
                "aggregation": "sum",
                "aggregation_field": "amount",
                "group_by": "day",
                "time_range": "14d",
                "filters": [],
            },
        )
        sq_country = SavedQuery(
            organization_id=org.id,
            created_by_id=user.id,
            name="Events by Country",
            description="Top countries by event volume",
            query_config={
                "event_name": "*",
                "aggregation": "count",
                "group_by": "properties.country",
                "time_range": "7d",
                "filters": [],
            },
        )
        sq_event_mix = SavedQuery(
            organization_id=org.id,
            created_by_id=user.id,
            name="Event Type Mix",
            description="Breakdown of event types",
            query_config={
                "event_name": "*",
                "aggregation": "count",
                "group_by": "event_name",
                "time_range": "7d",
                "filters": [],
            },
        )
        db.add_all([sq_pageviews, sq_revenue, sq_country, sq_event_mix])
        await db.flush()

        # 5. dashboard
        dashboard = Dashboard(
            organization_id=org.id,
            created_by_id=user.id,
            name="Demo Overview",
            description="Auto-seeded analytics dashboard with sample widgets",
            is_public=False,
            layout={"cols": 12, "row_height": 80},
            refresh_interval=60,
            template_type="web_analytics",
            tags=["demo", "overview"],
        )
        db.add(dashboard)
        await db.flush()

        # 6. widgets
        widgets = [
            Widget(
                dashboard_id=dashboard.id,
                saved_query_id=sq_pageviews.id,
                title="Page Views (14d)",
                widget_type="line_chart",
                config={"color": "#3b82f6", "show_legend": True},
                position={"x": 0, "y": 0, "w": 8, "h": 4},
            ),
            Widget(
                dashboard_id=dashboard.id,
                saved_query_id=sq_revenue.id,
                title="Total Revenue",
                widget_type="kpi_card",
                config={"format": "currency", "currency": "USD"},
                position={"x": 8, "y": 0, "w": 4, "h": 2},
            ),
            Widget(
                dashboard_id=dashboard.id,
                saved_query_id=sq_event_mix.id,
                title="Event Mix",
                widget_type="pie_chart",
                config={"show_legend": True},
                position={"x": 8, "y": 2, "w": 4, "h": 2},
            ),
            Widget(
                dashboard_id=dashboard.id,
                saved_query_id=sq_country.id,
                title="Events by Country",
                widget_type="bar_chart",
                config={"orientation": "horizontal", "limit": 10},
                position={"x": 0, "y": 4, "w": 12, "h": 4},
            ),
        ]
        db.add_all(widgets)

        await db.commit()
        print(f"  Created dashboard '{dashboard.name}' with {len(widgets)} widgets")
        print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
