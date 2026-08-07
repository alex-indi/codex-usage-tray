from __future__ import annotations

from dataclasses import dataclass, field

from .models import WindowChoice
from .settings import AppSettings


@dataclass(slots=True)
class NotificationTracker:
    _seen: dict[str, set[int]] = field(default_factory=dict)
    _previous: dict[str, int] = field(default_factory=dict)

    def evaluate(self, choice: WindowChoice, settings: AppSettings) -> tuple[str, ...]:
        key = choice.key
        remaining = choice.window.remaining_percent
        cycle = _cycle_key(choice)
        state_key = f"{key}:{cycle}"
        enabled = {
            20: settings.notify_20,
            10: settings.notify_10,
            0: settings.notify_0,
        }
        messages: list[str] = []
        seen = self._seen.setdefault(state_key, set())
        previous = self._previous.get(key)
        recovered = previous is not None and previous <= 20 and remaining > 20
        if recovered:
            seen.clear()
        for threshold in (20, 10, 0):
            if enabled[threshold] and remaining <= threshold and threshold not in seen:
                seen.add(threshold)
                messages.append(f"{choice.label}: {remaining}% remaining (crossed {threshold}%).")
        if settings.notify_recovery and recovered:
            messages.append(f"{choice.label} has reset: {remaining}% remaining.")
        self._previous[key] = remaining
        return tuple(messages)


def _cycle_key(choice: WindowChoice) -> str:
    reset = choice.window.resets_at
    return reset.isoformat() if reset is not None else "unknown"
