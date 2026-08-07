from __future__ import annotations

from collections.abc import Callable

import pystray

from .icons import tray_icon


class TrayController:
    def __init__(
        self,
        show_window: Callable[[], None],
        refresh: Callable[[], None],
        settings: Callable[[], None],
        quit_app: Callable[[], None],
    ) -> None:
        self.icon = pystray.Icon(
            "CodexUsageTray",
            tray_icon(None),
            "Codex Usage Tray — connecting",
            menu=pystray.Menu(
                pystray.MenuItem("Open", lambda: show_window(), default=True),
                pystray.MenuItem("Refresh now", lambda: refresh()),
                pystray.MenuItem("Settings", lambda: settings()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", lambda: quit_app()),
            ),
        )

    def start(self) -> None:
        self.icon.run_detached()

    def update(self, percent: int | None, label: str) -> None:
        self.icon.icon = tray_icon(percent)
        self.icon.title = label[:127]

    def notify(self, message: str) -> None:
        self.icon.notify(message, "Codex Usage Tray")

    def stop(self) -> None:
        self.icon.stop()
