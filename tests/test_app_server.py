from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from codex_usage_tray.app_server import CodexAppServerClient, CodexClientError
from codex_usage_tray.locator import LocatedCodex


class FakeLocator:
    def locate(self) -> LocatedCodex:
        return LocatedCodex(Path(sys.executable), "fake app server")


def make_factory(script: Path):  # type: ignore[no-untyped-def]
    def factory(_command, **kwargs):  # type: ignore[no-untyped-def]
        kwargs["creationflags"] = 0
        return subprocess.Popen([sys.executable, "-u", str(script)], **kwargs)

    return factory


def test_initialize_reads_data_and_handles_event(tmp_path) -> None:  # type: ignore[no-untyped-def]
    server = tmp_path / "server.py"
    server.write_text(
        """
import json, sys
for line in sys.stdin:
    message = json.loads(line)
    method = message.get("method")
    if "id" not in message:
        continue
    if method == "initialize":
        result = {"server": "fake"}
    elif method == "account/rateLimits/read":
        result = {"rateLimits": {"limitId": "codex", "primary": {"usedPercent": 42}}}
        print(json.dumps({"method": "account/rateLimits/updated", "params": {}}), flush=True)
    elif method == "account/usage/read":
        result = {"summary": {"lifetimeTokens": 99}}
    print(json.dumps({"id": message["id"], "result": result}), flush=True)
""".strip(),
        encoding="utf-8",
    )
    changed: list[bool] = []
    client = CodexAppServerClient(
        FakeLocator(),
        timeout=2,
        process_factory=make_factory(server),  # type: ignore[arg-type]
    )
    client.set_rate_limits_changed(lambda: changed.append(True))
    snapshot = client.read_snapshot()
    client.stop()
    assert snapshot.buckets[0].windows[0].remaining_percent == 58
    assert snapshot.account_usage is not None
    assert snapshot.account_usage.lifetime_tokens == 99
    assert changed


def test_timeout_stops_server_and_allows_future_reconnect(tmp_path) -> None:  # type: ignore[no-untyped-def]
    server = tmp_path / "silent.py"
    server.write_text("import time; time.sleep(5)", encoding="utf-8")
    client = CodexAppServerClient(
        FakeLocator(),
        timeout=0.1,
        process_factory=make_factory(server),  # type: ignore[arg-type]
    )
    with pytest.raises(CodexClientError, match="15 seconds"):
        client.read_snapshot()
    assert client._process is None


def test_crash_is_reported(tmp_path) -> None:  # type: ignore[no-untyped-def]
    server = tmp_path / "crash.py"
    server.write_text("raise SystemExit(2)", encoding="utf-8")
    client = CodexAppServerClient(
        FakeLocator(),
        timeout=1,
        process_factory=make_factory(server),  # type: ignore[arg-type]
    )
    with pytest.raises(CodexClientError, match="exited unexpectedly"):
        client.read_snapshot()


def test_usage_timeout_also_closes_connection(tmp_path) -> None:  # type: ignore[no-untyped-def]
    server = tmp_path / "usage_timeout.py"
    server.write_text(
        """
import json, sys, time
for line in sys.stdin:
    message = json.loads(line)
    method = message.get("method")
    if method == "account/usage/read":
        time.sleep(5)
        continue
    if "id" not in message:
        continue
    result = {} if method == "initialize" else {
        "rateLimits": {"primary": {"usedPercent": 5}}
    }
    print(json.dumps({"id": message["id"], "result": result}), flush=True)
""".strip(),
        encoding="utf-8",
    )
    client = CodexAppServerClient(
        FakeLocator(),
        timeout=0.1,
        process_factory=make_factory(server),  # type: ignore[arg-type]
    )
    with pytest.raises(CodexClientError, match="15 seconds"):
        client.read_snapshot()
    assert client._process is None
