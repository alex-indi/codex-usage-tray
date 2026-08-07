# Contributing

Thank you for helping improve Codex Usage Tray.

## Before opening an issue

- Search existing issues.
- Confirm that the official Codex Desktop app is installed and signed in.
- Try the latest release.
- Do not attach credentials, tokens, cookies, `.codex/auth.json`, or unredacted diagnostic output.

Bug reports should include the Windows version, Codex Desktop version, application version, expected behavior, actual behavior, and minimal reproduction steps.

## Development setup

Requirements:

- Windows 10/11 x64;
- Python 3.14 and `uv`;
- official Codex Desktop for optional live testing.

Run the local checks:

```powershell
uv sync --frozen
uv run ruff check .
uv run mypy src
uv run pytest
```

Run the application:

```powershell
uv run python -m codex_usage_tray --demo
```

## Pull requests

1. Keep each pull request focused on one change.
2. Add or update tests for parsing, security boundaries, and behavior changes.
3. Keep Ruff, mypy, and pytest clean.
4. Update the README or changelog when behavior visible to users changes.
5. Do not add telemetry, credential collection, update execution, or elevated operations without prior discussion and an explicit threat-model update.
6. Confirm that all commands above pass before submitting.

By contributing, you agree that your changes are licensed under the repository's MIT License.
