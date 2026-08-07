# Privacy

Codex Usage Tray is designed to keep account access inside the official Codex runtime.

## What the app reads

The app requests rate-limit and account-usage summaries from a locally started `codex app-server --stdio` process. It does not open, copy, log, or transmit Codex tokens, cookies, credential stores, prompts, source code, or conversation content.

## Network access

By default, the app performs one non-blocking request at startup to GitHub's public Releases API for this repository. It sends the normal HTTPS metadata required for that request and a `CodexUsageTray` user-agent. This check can be disabled. The app never downloads or installs an update automatically.

Codex itself may communicate with OpenAI as part of its normal operation; that traffic belongs to the official Codex runtime, not this app.

## Local storage

Preferences are stored in `%LOCALAPPDATA%\CodexUsageTray\settings.json`. A verified copy of an official MSIX `codex.exe` may be stored under the app's user cache because Windows package permissions can prevent direct execution. The copy is verified with SHA-256 before use.

No analytics, telemetry, usage history, or crash reports are collected.
