from __future__ import annotations

import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError

from .app_server import CodexAppServerClient
from .demo import demo_snapshot
from .dpi import center_window, configure_tk_scaling
from .models import UsageSnapshot
from .notifications import NotificationTracker
from .settings import AppSettings, SettingsStore, set_autostart
from .tray import TrayController
from .ui import MainWindow, SettingsDialog
from .updater import UpdateInfo, check_for_update


@dataclass(frozen=True, slots=True)
class WorkerResult:
    kind: str
    value: Any


class Application:
    def __init__(self, *, demo: bool = False) -> None:
        self.demo = demo
        self.root = tk.Tk()
        self.root.withdraw()
        configure_tk_scaling(self.root)
        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()
        self.client = CodexAppServerClient()
        self.client.set_rate_limits_changed(self.request_refresh)
        self.results: queue.Queue[WorkerResult] = queue.Queue()
        self.stop_event = threading.Event()
        self.refresh_lock = threading.Lock()
        self.snapshot: UsageSnapshot | None = None
        self._refresh_after_id: str | None = None
        self.notifier = NotificationTracker()
        self.window = MainWindow(self.root, self._start_refresh, self.open_settings, self.hide)
        self.tray = TrayController(self.show, self.request_refresh, self.open_settings, self.quit)

    def run(self) -> None:
        self.tray.start()
        self.root.after(100, self._process_results)
        self._start_refresh()
        if self.settings.check_updates and not self.demo:
            threading.Thread(target=self._check_update, daemon=True, name="update-check").start()
        self.root.mainloop()

    def request_refresh(self) -> None:
        self.results.put(WorkerResult("refresh", None))

    def _start_refresh(self) -> None:
        if self.stop_event.is_set() or not self.refresh_lock.acquire(blocking=False):
            return
        if self._refresh_after_id is not None:
            self.root.after_cancel(self._refresh_after_id)
            self._refresh_after_id = None
        threading.Thread(target=self._load_snapshot, daemon=True, name="usage-refresh").start()

    def _load_snapshot(self) -> None:
        try:
            snapshot = demo_snapshot() if self.demo else self.client.read_snapshot()
            runtime = "demo data" if self.demo else (self.client.runtime_description or "Codex")
            self.results.put(WorkerResult("snapshot", (snapshot, runtime)))
        except Exception as error:
            self.results.put(WorkerResult("error", str(error)))
        finally:
            self.refresh_lock.release()

    def _process_results(self) -> None:
        while True:
            try:
                result = self.results.get_nowait()
            except queue.Empty:
                break
            if result.kind == "snapshot":
                snapshot, runtime = result.value
                self._apply_snapshot(snapshot, runtime)
            elif result.kind == "error":
                self.window.show_error(f"Could not refresh: {result.value}")
                self.tray.update(None, f"Codex Usage Tray — {result.value}")
                self._schedule_refresh()
            elif result.kind == "update":
                update: UpdateInfo = result.value
                self.tray.notify(
                    f"Version {update.version} is available. Open the app to learn more."
                )
            elif result.kind == "refresh":
                self._start_refresh()
            elif result.kind == "show":
                self._show_on_main_thread()
            elif result.kind == "settings":
                self._open_settings_on_main_thread()
            elif result.kind == "quit":
                self._quit_on_main_thread()
        if not self.stop_event.is_set():
            self.root.after(250, self._process_results)

    def _apply_snapshot(self, snapshot: UsageSnapshot, runtime: str) -> None:
        self.snapshot = snapshot
        self.window.render(snapshot, runtime)
        selected = snapshot.tray_window(self.settings.tray_window)
        if selected is None:
            self.tray.update(None, "Codex Usage Tray — no limits available")
        else:
            remaining = selected.window.remaining_percent
            self.tray.update(remaining, f"{selected.label}: {remaining}% remaining")
            for message in self.notifier.evaluate(selected, self.settings):
                self.tray.notify(message)
        self._schedule_refresh()

    def _schedule_refresh(self) -> None:
        if self._refresh_after_id is not None:
            self.root.after_cancel(self._refresh_after_id)
        self._refresh_after_id = self.root.after(
            self.settings.refresh_seconds * 1000, self._start_refresh
        )

    def _check_update(self) -> None:
        try:
            update = check_for_update()
        except OSError, URLError, ValueError:
            return
        if update is not None:
            self.results.put(WorkerResult("update", update))

    def show(self) -> None:
        self.results.put(WorkerResult("show", None))

    def _show_on_main_thread(self) -> None:
        self.root.deiconify()
        self.root.update_idletasks()
        center_window(self.root)
        self.root.lift()
        self.root.focus_force()

    def hide(self) -> None:
        self.root.withdraw()

    def open_settings(self) -> None:
        self.results.put(WorkerResult("settings", None))

    def _open_settings_on_main_thread(self) -> None:
        choices: tuple[tuple[str, str], ...] = ()
        if self.snapshot is not None:
            choices = tuple((item.key, item.label) for item in self.snapshot.window_choices())
        SettingsDialog(self.root, self.settings, choices, self._save_settings)

    def _save_settings(self, settings: AppSettings) -> None:
        previous_autostart = self.settings.autostart
        try:
            if previous_autostart != settings.autostart:
                set_autostart(settings.autostart)
            self.settings_store.save(settings)
            self.settings = settings
            if self.snapshot is not None:
                runtime = "demo data" if self.demo else (self.client.runtime_description or "Codex")
                self._apply_snapshot(self.snapshot, runtime)
        except OSError as error:
            self.window.show_error(f"Could not save settings: {error}")

    def quit(self) -> None:
        self.results.put(WorkerResult("quit", None))

    def _quit_on_main_thread(self) -> None:
        if self.stop_event.is_set():
            return
        self.stop_event.set()
        if self._refresh_after_id is not None:
            self.root.after_cancel(self._refresh_after_id)
        self.tray.stop()
        self.client.stop()
        self.root.destroy()
