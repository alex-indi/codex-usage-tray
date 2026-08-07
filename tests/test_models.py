from __future__ import annotations

from codex_usage_tray.models import RateLimitBucket, UsageSnapshot, UsageWindow


def test_tray_metric_uses_selected_window_then_falls_back_to_lowest() -> None:
    snapshot = UsageSnapshot(
        (
            RateLimitBucket("codex", "Codex", None, (UsageWindow("primary", 10),)),
            RateLimitBucket("weekly", "Weekly", None, (UsageWindow("secondary", 80),)),
        ),
        None,
        None,
    )
    assert snapshot.tray_window("codex:primary").window.remaining_percent == 90  # type: ignore[union-attr]
    assert snapshot.tray_window("missing").window.remaining_percent == 20  # type: ignore[union-attr]
    assert snapshot.tray_window().window.remaining_percent == 20  # type: ignore[union-attr]


def test_duration_labels() -> None:
    assert UsageWindow("primary", 0, 30).duration_label == "30-minute window"
    assert UsageWindow("primary", 0, 180).duration_label == "3-hour window"
    assert UsageWindow("secondary", 0, 1440).duration_label == "1-day window"
    assert UsageWindow("secondary", 0, 10080).duration_label == "1-week window"
