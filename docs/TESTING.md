# Testing checklist

Automated checks:

```powershell
uv sync --frozen
uv run ruff check .
uv run mypy src
uv run pytest --cov=codex_usage_tray
uv run python scripts/build.py
```

Release candidates must also be tested manually:

- start `CodexUsageTray.exe --demo` and confirm it makes no network request and starts no Codex process;
- confirm large tray digits are legible on light and dark Windows taskbars;
- open and hide the dashboard from the tray;
- change every refresh interval and select a specific window;
- verify notification thresholds once per limit cycle and recovery notification;
- enable and disable autostart, checking only the current-user Run key;
- quit and confirm the child Codex process exits;
- copy the release ZIP to clean Windows 10 x64 and Windows 11 x64 VMs without Python;
- compare the EXE against `SHA256SUMS.txt` before each VM run.

The clean-VM checks are release gates and cannot be replaced by a development-machine smoke test.
