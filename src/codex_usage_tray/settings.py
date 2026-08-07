from __future__ import annotations

import json
import os
import sys
from contextlib import suppress
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from platformdirs import user_data_path

APP_NAME = "CodexUsageTray"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
ALLOWED_INTERVALS = (30, 60, 300)


@dataclass(slots=True)
class AppSettings:
    refresh_seconds: int = 60
    tray_window: str = "lowest"
    notify_20: bool = True
    notify_10: bool = True
    notify_0: bool = True
    notify_recovery: bool = True
    autostart: bool = False
    check_updates: bool = True

    @classmethod
    def from_dict(cls, value: object) -> AppSettings:
        if not isinstance(value, dict):
            return cls()
        interval = value.get("refresh_seconds", 60)
        if interval not in ALLOWED_INTERVALS:
            interval = 60
        tray_window = value.get("tray_window", "lowest")
        if not isinstance(tray_window, str) or not tray_window:
            tray_window = "lowest"
        return cls(
            refresh_seconds=interval,
            tray_window=tray_window,
            notify_20=_boolean(value, "notify_20", True),
            notify_10=_boolean(value, "notify_10", True),
            notify_0=_boolean(value, "notify_0", True),
            notify_recovery=_boolean(value, "notify_recovery", True),
            autostart=_boolean(value, "autostart", False),
            check_updates=_boolean(value, "check_updates", True),
        )


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or user_data_path(APP_NAME, appauthor=False) / "settings.json"

    def load(self) -> AppSettings:
        try:
            return AppSettings.from_dict(json.loads(self.path.read_text(encoding="utf-8")))
        except FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError:
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(asdict(settings), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)


def set_autostart(enabled: bool) -> None:
    if sys.platform != "win32":
        if enabled:
            raise OSError("Autostart is currently supported on Windows only.")
        return
    import winreg

    command = _autostart_command()
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if enabled:
            winreg.SetValueEx(key, "CodexUsageTray", 0, winreg.REG_SZ, command)
        else:
            with suppress(FileNotFoundError):
                winreg.DeleteValue(key, "CodexUsageTray")


def _autostart_command() -> str:
    executable = Path(sys.executable).resolve()
    if getattr(sys, "frozen", False):
        return f'"{executable}"'
    return f'"{executable}" -m codex_usage_tray'


def _boolean(value: dict[str, Any], key: str, default: bool) -> bool:
    candidate = value.get(key, default)
    return candidate if isinstance(candidate, bool) else default
