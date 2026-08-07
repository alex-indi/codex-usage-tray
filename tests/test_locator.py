from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from codex_usage_tray.locator import CodexLocator, _validate_executable


def test_environment_override_has_priority(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    executable = tmp_path / "codex.exe"
    executable.write_bytes(b"MZ")
    monkeypatch.setenv("CODEX_USAGE_TRAY_CODEX_PATH", str(executable))
    located = CodexLocator(tmp_path / "cache").locate()
    assert located.executable == executable.resolve()
    assert located.source == "environment override"


def test_override_rejects_non_executable(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    file = tmp_path / "codex.txt"
    file.write_text("no", encoding="utf-8")
    monkeypatch.setenv("CODEX_USAGE_TRAY_CODEX_PATH", str(file))
    with pytest.raises(ValueError, match=r"\.exe"):
        CodexLocator().locate()


def test_msix_path_must_be_under_official_package(tmp_path) -> None:  # type: ignore[no-untyped-def]
    executable = tmp_path / "codex.exe"
    executable.write_bytes(b"MZ")
    with pytest.raises(ValueError, match="trusted"):
        _validate_executable(Path(executable), trusted_msix=True)


def test_cached_runtime_is_hash_verified(tmp_path) -> None:  # type: ignore[no-untyped-def]
    source = tmp_path / "source" / "codex.exe"
    source.parent.mkdir()
    source.write_bytes(b"official runtime")
    locator = CodexLocator(tmp_path / "cache")
    cached = locator._cache_verified(source)
    assert cached.read_bytes() == source.read_bytes()
    cached.write_bytes(b"tampered")
    assert locator._cache_verified(source).read_bytes() == source.read_bytes()


def test_msix_discovery_accepts_only_expected_runtime(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    package = tmp_path / "WindowsApps" / "OpenAI.Codex_1.2.3_x64"
    executable = package / "app" / "resources" / "codex.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"MZ")
    monkeypatch.setattr(
        "codex_usage_tray.locator.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout=str(package)),
    )
    assert CodexLocator()._locate_msix() == executable.resolve()


def test_path_fallback_is_used(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    executable = tmp_path / "codex.exe"
    executable.write_bytes(b"MZ")
    monkeypatch.delenv("CODEX_USAGE_TRAY_CODEX_PATH", raising=False)
    monkeypatch.setattr(CodexLocator, "_locate_msix", lambda _self: None)
    monkeypatch.setattr("codex_usage_tray.locator.shutil.which", lambda _name: str(executable))
    located = CodexLocator().locate()
    assert located.source == "PATH"
