from __future__ import annotations

from datetime import datetime, timedelta

from .models import (
    AccountUsageSummary,
    DailyUsage,
    RateLimitBucket,
    ResetCredit,
    ResetCreditSummary,
    UsageSnapshot,
    UsageWindow,
)


def demo_snapshot() -> UsageSnapshot:
    now = datetime.now().astimezone()
    return UsageSnapshot(
        buckets=(
            RateLimitBucket(
                "codex",
                "Codex",
                "plus",
                (
                    UsageWindow("primary", 32, 180, now + timedelta(hours=2, minutes=4)),
                    UsageWindow("secondary", 59, 10_080, now + timedelta(days=4, hours=7)),
                ),
            ),
        ),
        reset_credits=ResetCreditSummary(
            2,
            (
                ResetCredit("demo-1", "available", now + timedelta(days=14)),
                ResetCredit("demo-2", "available", now + timedelta(days=21)),
            ),
        ),
        account_usage=AccountUsageSummary(
            lifetime_tokens=12_486_200,
            peak_daily_tokens=842_100,
            current_streak_days=11,
            daily_buckets=(DailyUsage(now.date(), 384_200),),
        ),
        fetched_at=now,
    )
