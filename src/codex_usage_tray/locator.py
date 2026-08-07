from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_cache_path

OVERRIDE_ENV = "CODEX_USAGE_TRAY_CODEX_PATH"


class CodexNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LocatedCodex:
    executable: Path
    source: str


class CodexLocator:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or user_cache_path("CodexUsageTray", appauthor=False)

    def locate(self) -> LocatedCodex:
        override = os.environ.get(OVERRIDE_ENV)
        if override:
            path = _validate_executable(Path(override), trusted_msix=False)
            return LocatedCodex(path, "environment override")
        if sys.platform == "win32":
            msix = self._locate_msix()
            if msix is not None:
                return LocatedCodex(self._cache_verified(msix), "official Codex Desktop MSIX")
        found = shutil.which("codex.exe" if sys.platform == "win32" else "codex")
        if found:
            return LocatedCodex(_validate_executable(Path(found), trusted_msix=False), "PATH")
        raise CodexNotFoundError(
            f"Codex was not found. Install the official Codex app/CLI or set {OVERRIDE_ENV}."
        )

    def _locate_msix(self) -> Path | None:
        script = (
            "Get-AppxPackage -Name 'OpenAI.Codex' | "
            "Sort-Object Version -Descending | Select-Object -First 1 "
            "-ExpandProperty InstallLocation"
        )
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
                startupinfo=startup,
            )
        except OSError, subprocess.TimeoutExpired:
            return None
        if result.returncode != 0 or not result.stdout.strip():
            return None
        candidate = Path(result.stdout.strip().splitlines()[-1]) / "app" / "resources" / "codex.exe"
        try:
            return _validate_executable(candidate, trusted_msix=True)
        except OSError, ValueError:
            return None

    def _cache_verified(self, source: Path) -> Path:
        digest = _sha256(source)
        destination_dir = self.cache_dir / "runtime" / digest
        destination = destination_dir / "codex.exe"
        destination_dir.mkdir(parents=True, exist_ok=True)
        if not destination.exists() or _sha256(destination) != digest:
            temporary = destination.with_suffix(".tmp")
            shutil.copyfile(source, temporary)
            if _sha256(temporary) != digest:
                temporary.unlink(missing_ok=True)
                raise OSError("The cached Codex runtime failed SHA-256 verification.")
            os.replace(temporary, destination)
        return destination


def _validate_executable(path: Path, *, trusted_msix: bool) -> Path:
    resolved = path.expanduser().resolve(strict=True)
    if not resolved.is_file() or resolved.suffix.lower() != ".exe":
        raise ValueError("The configured Codex path must be an existing .exe file.")
    if trusted_msix:
        parts = tuple(part.lower() for part in resolved.parts)
        official_package = any(part.startswith("openai.codex_") for part in parts)
        expected_suffix = ("app", "resources", "codex.exe")
        if "windowsapps" not in parts or not official_package or parts[-3:] != expected_suffix:
            raise ValueError("The Codex MSIX runtime is outside the trusted package path.")
    return resolved


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
