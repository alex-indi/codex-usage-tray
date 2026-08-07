from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from .models import (
    AccountUsageSummary,
    DailyUsage,
    RateLimitBucket,
    ResetCredit,
    ResetCreditSummary,
    UsageWindow,
)

JsonObject = dict[str, Any]


def parse_rate_limits(
    result: JsonObject,
) -> tuple[tuple[RateLimitBucket, ...], ResetCreditSummary | None]:
    buckets: list[RateLimitBucket] = []
    by_id = result.get("rateLimitsByLimitId")
    if isinstance(by_id, dict):
        for fallback_id, value in by_id.items():
            if isinstance(fallback_id, str) and isinstance(value, dict):
                buckets.append(_parse_bucket(fallback_id, value))

    single = result.get("rateLimits")
    if not buckets and isinstance(single, dict):
        fallback_id = _string(single.get("limitId")) or "codex"
        buckets.append(_parse_bucket(fallback_id, single))

    return tuple(buckets), _parse_reset_credits(result.get("rateLimitResetCredits"))


def parse_account_usage(result: JsonObject) -> AccountUsageSummary | None:
    summary = result.get("summary")
    if not isinstance(summary, dict):
        return None

    daily: list[DailyUsage] = []
    daily_buckets = result.get("dailyUsageBuckets")
    if isinstance(daily_buckets, list):
        for item in daily_buckets:
            if not isinstance(item, dict):
                continue
            date_text = _string(item.get("startDate"))
            tokens = _integer(item.get("tokens"))
            if date_text is None or tokens is None:
                continue
            try:
                daily.append(DailyUsage(date.fromisoformat(date_text), tokens))
            except ValueError:
                continue

    return AccountUsageSummary(
        lifetime_tokens=_integer(summary.get("lifetimeTokens")),
        peak_daily_tokens=_integer(summary.get("peakDailyTokens")),
        current_streak_days=_integer(summary.get("currentStreakDays")),
        daily_buckets=tuple(daily),
    )


def _parse_bucket(fallback_id: str, value: JsonObject) -> RateLimitBucket:
    bucket_id = _string(value.get("limitId")) or fallback_id
    name = _string(value.get("limitName")) or _humanize_id(bucket_id)
    windows = tuple(
        window
        for kind in ("primary", "secondary")
        if (window := _parse_window(kind, value.get(kind))) is not None
    )
    return RateLimitBucket(
        id=bucket_id,
        display_name=name,
        plan_type=_string(value.get("planType")),
        windows=windows,
    )


def _parse_window(kind: str, value: Any) -> UsageWindow | None:
    if not isinstance(value, dict):
        return None
    used = _integer(value.get("usedPercent"))
    if used is None:
        return None
    return UsageWindow(
        kind=kind,
        used_percent=used,
        duration_minutes=_integer(value.get("windowDurationMins")),
        resets_at=_unix_datetime(value.get("resetsAt")),
    )


def _parse_reset_credits(value: Any) -> ResetCreditSummary | None:
    if not isinstance(value, dict):
        return None
    credits: list[ResetCredit] = []
    items = value.get("credits")
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                credits.append(
                    ResetCredit(
                        id=_string(item.get("id")),
                        status=_string(item.get("status")),
                        expires_at=_unix_datetime(item.get("expiresAt")),
                        title=_string(item.get("title")),
                        description=_string(item.get("description")),
                    )
                )
    available = _integer(value.get("availableCount"))
    if available is None:
        available = sum(1 for item in credits if (item.status or "").lower() == "available")
    return ResetCreditSummary(max(0, available), tuple(credits))


def _unix_datetime(value: Any) -> datetime | None:
    seconds = _integer(value)
    if seconds is None:
        return None
    try:
        return datetime.fromtimestamp(seconds, tz=UTC)
    except OverflowError, OSError, ValueError:
        return None


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _integer(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _humanize_id(value: str) -> str:
    return "Codex" if value.lower() == "codex" else value.replace("_", " ").strip().title()
