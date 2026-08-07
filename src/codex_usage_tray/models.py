from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class UsageWindow:
    kind: str
    used_percent: int
    duration_minutes: int | None = None
    resets_at: datetime | None = None

    @property
    def remaining_percent(self) -> int:
        return max(0, min(100, 100 - self.used_percent))

    @property
    def duration_label(self) -> str:
        minutes = self.duration_minutes
        if minutes is None:
            return "Primary limit" if self.kind.lower() == "primary" else "Additional limit"
        if minutes < 60:
            return f"{minutes}-minute window"
        if minutes % 10_080 == 0:
            weeks = minutes // 10_080
            return f"{weeks}-week window"
        if minutes % 1_440 == 0:
            days = minutes // 1_440
            return f"{days}-day window"
        if minutes % 60 == 0:
            hours = minutes // 60
            return f"{hours}-hour window"
        return f"{minutes}-minute window"


@dataclass(frozen=True, slots=True)
class RateLimitBucket:
    id: str
    display_name: str
    plan_type: str | None
    windows: tuple[UsageWindow, ...] = ()


@dataclass(frozen=True, slots=True)
class ResetCredit:
    id: str | None = None
    status: str | None = None
    expires_at: datetime | None = None
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ResetCreditSummary:
    available_count: int
    credits: tuple[ResetCredit, ...] = ()


@dataclass(frozen=True, slots=True)
class DailyUsage:
    start_date: date
    tokens: int


@dataclass(frozen=True, slots=True)
class AccountUsageSummary:
    lifetime_tokens: int | None = None
    peak_daily_tokens: int | None = None
    current_streak_days: int | None = None
    daily_buckets: tuple[DailyUsage, ...] = ()

    @property
    def today_tokens(self) -> int | None:
        matches = [item.tokens for item in self.daily_buckets if item.start_date == date.today()]
        return sum(matches) if matches else None


@dataclass(frozen=True, slots=True)
class WindowChoice:
    key: str
    bucket: RateLimitBucket
    window: UsageWindow

    @property
    def label(self) -> str:
        return f"{self.bucket.display_name} — {self.window.duration_label}"


@dataclass(frozen=True, slots=True)
class UsageSnapshot:
    buckets: tuple[RateLimitBucket, ...]
    reset_credits: ResetCreditSummary | None
    account_usage: AccountUsageSummary | None
    fetched_at: datetime = field(default_factory=lambda: datetime.now().astimezone())

    def window_choices(self) -> tuple[WindowChoice, ...]:
        choices: list[WindowChoice] = []
        for bucket in self.buckets:
            for window in bucket.windows:
                choices.append(WindowChoice(f"{bucket.id}:{window.kind}", bucket, window))
        return tuple(choices)

    def tray_window(self, selected_key: str = "lowest") -> WindowChoice | None:
        choices = self.window_choices()
        if not choices:
            return None
        if selected_key != "lowest":
            selected = next((item for item in choices if item.key == selected_key), None)
            if selected is not None:
                return selected
        return min(choices, key=lambda item: item.window.remaining_percent)
