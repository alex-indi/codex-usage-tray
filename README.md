# Codex Usage Tray

[![CI](https://github.com/alex-indi/codex-usage-tray/actions/workflows/ci.yml/badge.svg)](https://github.com/alex-indi/codex-usage-tray/actions/workflows/ci.yml)
[![CodeQL](https://github.com/alex-indi/codex-usage-tray/actions/workflows/codeql.yml/badge.svg)](https://github.com/alex-indi/codex-usage-tray/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**A privacy-first Windows tray app for monitoring OpenAI Codex usage limits, reset times, and saved resets.**

![Codex Usage Tray demo](assets/demo-screenshot.png)

Codex Usage Tray keeps the lowest remaining percentage visible as large, transparent tray digits. Open the compact dashboard to inspect every dynamic limit window, its reset time, token activity when available, and the number of saved resets.

![Codex Usage Tray settings](assets/settings-screenshot.png)

> This independent open-source project is not affiliated with or endorsed by OpenAI.

## Why this app

- **Codex-only:** no provider setup or account mapping.
- **Privacy-first:** talks only to your locally installed official Codex runtime. It does not collect credentials, telemetry, or usage history.
- **Dynamic windows:** does not assume a fixed “five-hour limit”; it renders what Codex reports.
- **Saved resets:** displays available reset credits but never applies them.
- **Windows-native behavior:** portable EXE, optional per-user startup, no administrator rights.

## Install

Download the latest portable ZIP from the [Releases page](https://github.com/alex-indi/codex-usage-tray/releases). Extract it and start `CodexUsageTray.exe`. Codex Desktop or the official Codex CLI must already be installed and signed in.

Windows SmartScreen may warn about an unsigned early release. Verify `SHA256SUMS.txt`, inspect the source, or build it yourself. Code signing is planned when the project has a suitable certificate.

## Run from source

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/):

```powershell
git clone https://github.com/alex-indi/codex-usage-tray.git
cd codex-usage-tray
uv sync --frozen
uv run python -m codex_usage_tray
```

Safe demonstration mode (no Codex process and no network):

```powershell
uv run python -m codex_usage_tray --demo
```

## Data access and network behavior

The app starts `codex app-server --stdio` and invokes only:

- `account/rateLimits/read`
- `account/usage/read`
- the `account/rateLimits/updated` event

It never reads Codex credential files itself. The only direct network request is an optional startup check of the latest GitHub release; disable it in Settings. Updates are never downloaded automatically. See [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md).

Settings are stored atomically in `%LOCALAPPDATA%\CodexUsageTray\settings.json`. Optional startup uses only `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` and never requests elevation.

## Comparison

| Project | Focus | Windows | Saved resets | Credentials handled by monitor |
|---|---|---:|---:|---:|
| **Codex Usage Tray** | Codex-only, minimal local monitor | First-class | Yes | No |
| [CodexBar](https://codexbar.app/) | Codex menu bar experience | No (macOS) | Varies | See project docs |
| Multi-provider quota monitors | Many AI providers | Varies | Usually no | Often provider-specific |

Codex Usage Tray deliberately does less: no history, graphs, forecasting, or other providers. That smaller scope keeps setup and data exposure minimal.

## Development

```powershell
uv sync --frozen
uv run ruff check .
uv run mypy src
uv run pytest
uv run python scripts/build.py
```

Python 3.14 is intentional: it is the current stable language baseline for the first release. Runtime dependencies are pinned exactly in `uv.lock`.

## Status

Version 0.1 is Windows 10/11 x64 only. Platform boundaries are isolated for future macOS/Linux adapters, but those systems are not supported yet. The interface is English; [Russian documentation](README.ru.md) is also available.

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).
