from __future__ import annotations

import json

from codex_usage_tray.settings import AppSettings, SettingsStore


def test_settings_round_trip_is_atomic(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    expected = AppSettings(refresh_seconds=30, tray_window="codex:primary", autostart=True)
    store.save(expected)
    assert store.load() == expected
    assert not path.with_suffix(".json.tmp").exists()
    assert json.loads(path.read_text(encoding="utf-8"))["refresh_seconds"] == 30


def test_corrupt_settings_return_defaults(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")
    assert SettingsStore(path).load() == AppSettings()


def test_invalid_values_are_sanitized() -> None:
    settings = AppSettings.from_dict({"refresh_seconds": 7, "tray_window": 123, "notify_20": "yes"})
    assert settings.refresh_seconds == 60
    assert settings.tray_window == "lowest"
    assert settings.notify_20 is True
