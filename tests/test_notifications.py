from __future__ import annotations

from datetime import UTC, datetime, timedelta

from codex_usage_tray.models import RateLimitBucket, UsageWindow, WindowChoice
from codex_usage_tray.notifications import NotificationTracker
from codex_usage_tray.settings import AppSettings


def choice(remaining: int, reset_offset: int = 0) -> WindowChoice:
    reset = datetime(2030, 1, 1, tzinfo=UTC) + timedelta(days=reset_offset)
    bucket = RateLimitBucket("codex", "Codex", None)
    window = UsageWindow("primary", 100 - remaining, 180, reset)
    return WindowChoice("codex:primary", bucket, window)


def test_threshold_is_not_repeated_in_same_cycle() -> None:
    tracker = NotificationTracker()
    settings = AppSettings()
    assert len(tracker.evaluate(choice(19), settings)) == 1
    assert tracker.evaluate(choice(18), settings) == ()
    assert len(tracker.evaluate(choice(9), settings)) == 1
    assert len(tracker.evaluate(choice(0), settings)) == 1


def test_new_cycle_and_recovery_notify_again() -> None:
    tracker = NotificationTracker()
    settings = AppSettings()
    tracker.evaluate(choice(10), settings)
    recovered = tracker.evaluate(choice(100, 1), settings)
    assert any("reset" in message for message in recovered)
    assert len(tracker.evaluate(choice(19, 1), settings)) == 1
