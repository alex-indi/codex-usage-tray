from __future__ import annotations

from datetime import UTC

from codex_usage_tray.parser import parse_account_usage, parse_rate_limits


def test_parses_multiple_rate_limit_buckets_and_saved_resets() -> None:
    buckets, credits = parse_rate_limits(
        {
            "rateLimitsByLimitId": {
                "codex": {
                    "limitName": "Codex",
                    "planType": "plus",
                    "primary": {
                        "usedPercent": 25,
                        "windowDurationMins": 180,
                        "resetsAt": 1_800_000_000,
                    },
                    "secondary": {"usedPercent": 70, "windowDurationMins": 10080},
                },
                "other_limit": {"primary": {"usedPercent": 101}},
            },
            "rateLimitResetCredits": {
                "availableCount": 2,
                "credits": [
                    {"id": "a", "status": "available", "expiresAt": 1_900_000_000},
                    {"id": "b", "status": "available"},
                ],
            },
        }
    )
    assert len(buckets) == 2
    assert buckets[0].windows[0].remaining_percent == 75
    assert buckets[0].windows[0].resets_at is not None
    assert buckets[0].windows[0].resets_at.tzinfo == UTC
    assert buckets[1].windows[0].remaining_percent == 0
    assert credits is not None
    assert credits.available_count == 2
    assert len(credits.credits) == 2


def test_parses_single_legacy_bucket_and_counts_available_credits() -> None:
    buckets, credits = parse_rate_limits(
        {
            "rateLimits": {"limitId": "codex", "primary": {"usedPercent": -10}},
            "rateLimitResetCredits": {"credits": [{"status": "available"}, {"status": "used"}]},
        }
    )
    assert buckets[0].display_name == "Codex"
    assert buckets[0].windows[0].remaining_percent == 100
    assert credits is not None and credits.available_count == 1


def test_tolerates_missing_and_invalid_fields() -> None:
    buckets, credits = parse_rate_limits(
        {"rateLimits": {"primary": {"usedPercent": "50"}}, "rateLimitResetCredits": None}
    )
    assert buckets[0].windows == ()
    assert credits is None
    assert parse_account_usage({}) is None


def test_parses_account_token_usage() -> None:
    usage = parse_account_usage(
        {
            "summary": {
                "lifetimeTokens": 1234,
                "peakDailyTokens": 500,
                "currentStreakDays": 4,
            },
            "dailyUsageBuckets": [
                {"startDate": "2026-08-07", "tokens": 42},
                {"startDate": "invalid", "tokens": 5},
                {"tokens": 9},
            ],
        }
    )
    assert usage is not None
    assert usage.lifetime_tokens == 1234
    assert len(usage.daily_buckets) == 1
