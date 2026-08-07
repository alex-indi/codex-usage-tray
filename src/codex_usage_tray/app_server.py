from __future__ import annotations

import json
import queue
import subprocess
import threading
from collections.abc import Callable
from contextlib import suppress

from . import __version__
from .locator import CodexLocator
from .models import UsageSnapshot
from .parser import JsonObject, parse_account_usage, parse_rate_limits


class CodexClientError(RuntimeError):
    pass


class CodexTimeoutError(CodexClientError):
    pass


class CodexAppServerClient:
    def __init__(
        self,
        locator: CodexLocator | None = None,
        *,
        timeout: float = 15.0,
        process_factory: Callable[..., subprocess.Popen[str]] = subprocess.Popen,
    ) -> None:
        self.locator = locator or CodexLocator()
        self.timeout = timeout
        self.process_factory = process_factory
        self.runtime_description: str | None = None
        self._process: subprocess.Popen[str] | None = None
        self._pending: dict[int, queue.Queue[JsonObject]] = {}
        self._pending_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._lifecycle_lock = threading.Lock()
        self._request_id = 0
        self._initialized = False
        self._stopping = threading.Event()
        self._rate_limits_changed: Callable[[], None] | None = None

    def set_rate_limits_changed(self, callback: Callable[[], None]) -> None:
        self._rate_limits_changed = callback

    def read_snapshot(self) -> UsageSnapshot:
        try:
            self._ensure_started()
            rate_result = self._request("account/rateLimits/read", {})
            buckets, credits = parse_rate_limits(rate_result)
            usage = None
            try:
                usage = parse_account_usage(self._request("account/usage/read", {}))
            except CodexTimeoutError:
                raise
            except CodexClientError:
                pass
            return UsageSnapshot(buckets, credits, usage)
        except Exception:
            self.stop()
            raise

    def stop(self) -> None:
        with self._lifecycle_lock:
            self._stop_locked()

    def _ensure_started(self) -> None:
        with self._lifecycle_lock:
            if self._initialized and self._process is not None and self._process.poll() is None:
                return
            self._stop_locked()
            located = self.locator.locate()
            self.runtime_description = located.source
            creationflags = (
                subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            )
            try:
                self._process = self.process_factory(
                    [str(located.executable), "app-server", "--stdio"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    creationflags=creationflags,
                )
            except OSError as error:
                raise CodexClientError("Could not start the official Codex executable.") from error
            if self._process.stdin is None or self._process.stdout is None:
                self._stop_locked()
                raise CodexClientError("Codex App Server did not expose its stdio connection.")
            self._stopping.clear()
            threading.Thread(target=self._read_stdout, daemon=True, name="codex-stdout").start()
            if self._process.stderr is not None:
                threading.Thread(
                    target=self._drain_stderr, daemon=True, name="codex-stderr"
                ).start()
            self._request(
                "initialize",
                {
                    "clientInfo": {
                        "name": "codex_usage_tray",
                        "title": "Codex Usage Tray",
                        "version": __version__,
                    },
                    "capabilities": {"experimentalApi": True},
                },
            )
            self._send({"method": "initialized", "params": {}})
            self._initialized = True

    def _request(self, method: str, parameters: JsonObject) -> JsonObject:
        self._request_id += 1
        request_id = self._request_id
        response_queue: queue.Queue[JsonObject] = queue.Queue(maxsize=1)
        with self._pending_lock:
            self._pending[request_id] = response_queue
        try:
            self._send({"id": request_id, "method": method, "params": parameters})
            try:
                response = response_queue.get(timeout=self.timeout)
            except queue.Empty as error:
                raise CodexTimeoutError("Codex did not respond within 15 seconds.") from error
            if "error" in response:
                error_value = response["error"]
                message = error_value.get("message") if isinstance(error_value, dict) else None
                detail = message if isinstance(message, str) else "Codex returned an error."
                raise CodexClientError(detail)
            result = response.get("result")
            return result if isinstance(result, dict) else {}
        finally:
            with self._pending_lock:
                self._pending.pop(request_id, None)

    def _send(self, message: JsonObject) -> None:
        process = self._process
        if process is None or process.poll() is not None or process.stdin is None:
            raise CodexClientError("Codex App Server is not running.")
        payload = json.dumps(message, separators=(",", ":"), ensure_ascii=False)
        try:
            with self._write_lock:
                process.stdin.write(payload + "\n")
                process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError) as error:
            raise CodexClientError("The Codex App Server connection was interrupted.") from error

    def _read_stdout(self) -> None:
        process = self._process
        if process is None or process.stdout is None:
            return
        try:
            for line in process.stdout:
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(message, dict):
                    continue
                if message.get("method") == "account/rateLimits/updated":
                    callback = self._rate_limits_changed
                    if callback is not None:
                        callback()
                request_id = message.get("id")
                if isinstance(request_id, int):
                    with self._pending_lock:
                        target = self._pending.get(request_id)
                    if target is not None:
                        target.put(message)
        finally:
            if not self._stopping.is_set():
                self._fail_pending("Codex App Server exited unexpectedly.")

    def _drain_stderr(self) -> None:
        process = self._process
        if process is not None and process.stderr is not None:
            for _line in process.stderr:
                if self._stopping.is_set():
                    break

    def _fail_pending(self, message: str) -> None:
        with self._pending_lock:
            targets = tuple(self._pending.values())
        for target in targets:
            with suppress(queue.Full):
                target.put_nowait({"error": {"message": message}})

    def _stop_locked(self) -> None:
        self._initialized = False
        self._stopping.set()
        self._fail_pending("Codex App Server stopped.")
        process, self._process = self._process, None
        if process is None:
            return
        try:
            if process.stdin is not None:
                process.stdin.close()
        except OSError:
            pass
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                stream.close()
