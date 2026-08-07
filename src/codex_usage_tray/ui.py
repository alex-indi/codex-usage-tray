from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from functools import partial

from PIL import Image, ImageDraw, ImageTk

from . import __version__
from .dpi import center_window, scale_for_window, set_scaled_geometry
from .icons import brand_icon
from .models import UsageSnapshot
from .settings import AppSettings

PAGE = "#ECECEA"
CARD = "#FFFFFF"
INK = "#111111"
MUTED = "#8A8A86"
LINE = "#E2E2DE"
LIME = "#DFFF62"
MINT = "#A9FFD0"


class PillButton(tk.Canvas):
    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        *,
        width: int,
        height: int = 38,
        fill: str = CARD,
        hover: str = "#F8F8F5",
        foreground: str = INK,
    ) -> None:
        scale = scale_for_window(parent.winfo_toplevel())
        pixel_width = _px(scale, width)
        pixel_height = _px(scale, height)
        parent_background = str(parent.cget("background"))
        super().__init__(
            parent,
            width=pixel_width,
            height=pixel_height,
            background=parent_background,
            highlightthickness=0,
            cursor="hand2",
            takefocus=True,
        )
        self._fill = fill
        self._hover = hover
        self._command = command
        edge = _px(scale, 1)
        self._shape = _rounded_rectangle(
            self,
            edge,
            edge,
            pixel_width - edge,
            pixel_height - edge,
            pixel_height / 2,
            fill,
        )
        self.create_text(
            pixel_width / 2,
            pixel_height / 2 - _px(scale, 2),
            text=text,
            fill=foreground,
            font=("Segoe UI Semibold", 10),
        )
        self.bind("<Enter>", lambda _event: self.itemconfigure(self._shape, fill=self._hover))
        self.bind("<Leave>", lambda _event: self.itemconfigure(self._shape, fill=self._fill))
        self.bind("<Button-1>", lambda _event: self._command())
        self.bind("<Return>", lambda _event: self._command())


class SegmentedControl(tk.Canvas):
    def __init__(
        self,
        parent: tk.Misc,
        variable: tk.StringVar,
        options: tuple[tuple[str, str], ...],
        *,
        width: int,
        height: int = 40,
    ) -> None:
        self._scale = scale_for_window(parent.winfo_toplevel())
        self._width = _px(self._scale, width)
        self._height = _px(self._scale, height)
        self._variable = variable
        self._choices = options
        super().__init__(
            parent,
            width=self._width,
            height=self._height,
            background=CARD,
            highlightthickness=0,
            cursor="hand2",
            takefocus=True,
        )
        self.bind("<Button-1>", self._select_from_pointer)
        self.bind("<Left>", lambda _event: self._move(-1))
        self.bind("<Right>", lambda _event: self._move(1))
        self._variable.trace_add("write", lambda *_args: self._draw())
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        _rounded_rectangle(
            self,
            0,
            0,
            self._width,
            self._height,
            self._height / 2,
            "#EFEFEB",
        )
        segment_width = self._width / len(self._choices)
        selected = self._variable.get()
        for index, (label, value) in enumerate(self._choices):
            left = index * segment_width
            if value == selected:
                inset = _px(self._scale, 3)
                _rounded_rectangle(
                    self,
                    left + inset,
                    inset,
                    left + segment_width - inset,
                    self._height - inset,
                    (self._height - inset * 2) / 2,
                    INK,
                )
            self.create_text(
                left + segment_width / 2,
                self._height / 2 - _px(self._scale, 1),
                text=label,
                fill="white" if value == selected else "#6F6F6B",
                font=("Segoe UI Semibold", 9),
            )

    def _select_from_pointer(self, event: tk.Event[tk.Misc]) -> None:
        index = min(len(self._choices) - 1, int(event.x / self._width * len(self._choices)))
        self._variable.set(self._choices[index][1])

    def _move(self, direction: int) -> None:
        values = [value for _label, value in self._choices]
        try:
            index = values.index(self._variable.get())
        except ValueError:
            index = 0
        self._variable.set(values[(index + direction) % len(values)])


class ModernDropdown(tk.Canvas):
    def __init__(
        self,
        parent: tk.Misc,
        variable: tk.StringVar,
        options: tuple[tuple[str, str], ...],
        *,
        width: int,
        height: int = 42,
    ) -> None:
        self._scale = scale_for_window(parent.winfo_toplevel())
        self._width = _px(self._scale, width)
        self._height = _px(self._scale, height)
        self._variable = variable
        self._choices = options
        super().__init__(
            parent,
            width=self._width,
            height=self._height,
            background=CARD,
            highlightthickness=0,
            cursor="hand2",
            takefocus=True,
        )
        self._menu = tk.Menu(self, tearoff=False, font=("Segoe UI", 10))
        for label, value in options:
            self._menu.add_command(label=label, command=partial(variable.set, value))
        self.bind("<Button-1>", self._open_menu)
        self.bind("<Return>", self._open_menu)
        self.bind("<space>", self._open_menu)
        self._variable.trace_add("write", lambda *_args: self._draw())
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        _rounded_rectangle(
            self,
            0,
            0,
            self._width,
            self._height,
            _px(self._scale, 13),
            "#F2F2EE",
        )
        current = self._variable.get()
        label = next((text for text, value in self._choices if value == current), current)
        self.create_text(
            _px(self._scale, 16),
            self._height / 2 - _px(self._scale, 1),
            text=label,
            anchor="w",
            fill=INK,
            font=("Segoe UI", 9),
        )
        chevron_x = self._width - _px(self._scale, 18)
        chevron_y = self._height / 2 - _px(self._scale, 1)
        step = _px(self._scale, 4)
        self.create_line(
            [
                chevron_x - step,
                chevron_y - step / 2,
                chevron_x,
                chevron_y + step / 2,
                chevron_x + step,
                chevron_y - step / 2,
            ],
            fill="#777773",
            width=max(1, _px(self._scale, 1)),
        )

    def _open_menu(self, _event: tk.Event[tk.Misc]) -> None:
        try:
            self._menu.tk_popup(self.winfo_rootx(), self.winfo_rooty() + self.winfo_height())
        finally:
            self._menu.grab_release()


class ToggleSwitch(tk.Canvas):
    def __init__(self, parent: tk.Misc, variable: tk.BooleanVar) -> None:
        self._scale = scale_for_window(parent.winfo_toplevel())
        self._width = _px(self._scale, 46)
        self._height = _px(self._scale, 26)
        self._variable = variable
        self._photo: ImageTk.PhotoImage | None = None
        super().__init__(
            parent,
            width=self._width,
            height=self._height,
            background=CARD,
            highlightthickness=0,
            cursor="hand2",
            takefocus=True,
        )
        self.bind("<Button-1>", lambda _event: self._toggle())
        self.bind("<Return>", lambda _event: self._toggle())
        self.bind("<space>", lambda _event: self._toggle())
        self._variable.trace_add("write", lambda *_args: self._draw())
        self._draw()

    def _toggle(self) -> None:
        self._variable.set(not self._variable.get())

    def _draw(self) -> None:
        self.delete("all")
        enabled = self._variable.get()
        supersampling = 4
        width = self._width * supersampling
        height = self._height * supersampling
        image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle(
            (0, 0, width - 1, height - 1),
            radius=height // 2,
            fill=LIME if enabled else "#DEDEDA",
        )
        margin = _px(self._scale, 4) * supersampling
        diameter = height - margin * 2
        left = width - margin - diameter if enabled else margin
        draw.ellipse(
            (left, margin, left + diameter, margin + diameter),
            fill=INK if enabled else "white",
        )
        image = image.resize((self._width, self._height), Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(image)
        self.create_image(0, 0, image=self._photo, anchor="nw")


class MainWindow:
    def __init__(
        self,
        root: tk.Tk,
        on_refresh: Callable[[], None],
        on_settings: Callable[[], None],
        on_hide: Callable[[], None],
    ) -> None:
        self.root = root
        self._scale = scale_for_window(root)
        self._photo = ImageTk.PhotoImage(brand_icon(_px(self._scale, 64)))
        self._snapshot: UsageSnapshot | None = None
        self._gradient_images: list[ImageTk.PhotoImage] = []

        root.title("Codex Usage Tray")
        set_scaled_geometry(root, 620, 650, minimum=(540, 570))
        root.configure(background=PAGE)
        root.iconphoto(True, self._photo)  # type: ignore[arg-type]
        root.protocol("WM_DELETE_WINDOW", on_hide)

        shell = tk.Frame(
            root,
            background=PAGE,
            padx=_px(self._scale, 28),
            pady=_px(self._scale, 24),
        )
        shell.pack(fill="both", expand=True)

        header = tk.Frame(shell, background=PAGE)
        header.pack(fill="x")
        tk.Label(header, image=self._photo, background=PAGE).pack(
            side="left", padx=(0, _px(self._scale, 14))
        )
        titles = tk.Frame(header, background=PAGE)
        titles.pack(side="left", fill="x", expand=True)
        tk.Label(
            titles,
            text="Codex Usage Tray",
            background=PAGE,
            foreground=INK,
            font=("Segoe UI Semibold", 19),
        ).pack(anchor="w")
        tk.Label(
            titles,
            text="Your Codex limits, always visible",
            background=PAGE,
            foreground=MUTED,
            font=("Segoe UI", 10),
        ).pack(
            anchor="w",
            padx=(_px(self._scale, 2), 0),
            pady=(_px(self._scale, 2), 0),
        )
        PillButton(header, "Settings", on_settings, width=96).pack(side="right")

        status_row = tk.Frame(shell, background=PAGE)
        status_row.pack(fill="x", pady=(_px(self._scale, 22), _px(self._scale, 10)))
        self.status_dot = tk.Label(
            status_row,
            text="●",
            background=PAGE,
            foreground="#58CB88",
            font=("Segoe UI", 9),
        )
        self.status_dot.pack(side="left", padx=(_px(self._scale, 1), _px(self._scale, 7)))
        self.status = tk.StringVar(value="Connecting to Codex…")
        tk.Label(
            status_row,
            textvariable=self.status,
            background=PAGE,
            foreground="#676763",
            font=("Segoe UI", 10),
        ).pack(side="left")

        content_holder = tk.Frame(shell, background=PAGE)
        content_holder.pack(fill="both", expand=True)
        self.content = tk.Canvas(
            content_holder,
            background=PAGE,
            highlightthickness=0,
            borderwidth=0,
        )
        self.content.pack(side="left", fill="both", expand=True)
        self.content.bind("<Configure>", lambda _event: self._redraw())
        self.content.bind(
            "<MouseWheel>",
            lambda event: self.content.yview_scroll(int(-event.delta / 120), "units"),
        )

        footer = tk.Frame(shell, background=PAGE)
        footer.pack(fill="x", pady=(_px(self._scale, 12), 0))
        self.updated = tk.StringVar(value="Not updated yet")
        tk.Label(
            footer,
            textvariable=self.updated,
            background=PAGE,
            foreground=MUTED,
            font=("Segoe UI", 9),
        ).pack(side="left")
        PillButton(
            footer,
            "Refresh now",
            on_refresh,
            width=116,
            fill=INK,
            hover="#292929",
            foreground="white",
        ).pack(side="right")
        center_window(root)
        root.deiconify()
        root.update_idletasks()
        center_window(root)

    def render(self, snapshot: UsageSnapshot, runtime: str) -> None:
        self._snapshot = snapshot
        self.status_dot.configure(foreground="#58CB88")
        self.status.set(f"Connected via {runtime}")
        self.updated.set(f"Updated {snapshot.fetched_at:%H:%M:%S}")
        self._redraw()

    def _redraw(self) -> None:
        snapshot = self._snapshot
        if snapshot is None:
            return
        canvas = self.content
        canvas.delete("all")
        self._gradient_images.clear()
        scale = scale_for_window(self.root)
        width = max(_px(scale, 460), canvas.winfo_width())
        x = _px(scale, 1)
        card_width = width - _px(scale, 8)
        y = _px(scale, 2)

        for index, choice in enumerate(snapshot.window_choices()):
            height = _px(scale, 116)
            if index == 0:
                gradient = ImageTk.PhotoImage(_gradient_card(card_width, height, _px(scale, 25)))
                self._gradient_images.append(gradient)
                canvas.create_image(x, y, image=gradient, anchor="nw")
            else:
                _rounded_rectangle(
                    canvas,
                    x,
                    y,
                    x + card_width,
                    y + height,
                    _px(scale, 25),
                    CARD,
                )

            canvas.create_text(
                x + _px(scale, 22),
                y + _px(scale, 23),
                text=choice.label,
                anchor="nw",
                fill=INK,
                font=("Segoe UI Semibold", 11),
            )
            canvas.create_text(
                x + card_width - _px(scale, 22),
                y + _px(scale, 17),
                text=f"{choice.window.remaining_percent}%",
                anchor="ne",
                fill=INK,
                font=("Segoe UI Semibold", 23),
            )
            canvas.create_text(
                x + _px(scale, 22),
                y + _px(scale, 54),
                text=_format_reset(choice.window.resets_at),
                anchor="nw",
                fill="#6E6E69",
                font=("Segoe UI", 9),
            )
            bar_left = x + _px(scale, 22)
            bar_right = x + card_width - _px(scale, 22)
            bar_top = y + _px(scale, 87)
            bar_height = _px(scale, 8)
            _rounded_rectangle(
                canvas,
                bar_left,
                bar_top,
                bar_right,
                bar_top + bar_height,
                bar_height / 2,
                "#E4E4DE",
            )
            progress = (bar_right - bar_left) * choice.window.remaining_percent / 100
            if progress > 0:
                _rounded_rectangle(
                    canvas,
                    bar_left,
                    bar_top,
                    bar_left + max(bar_height, progress),
                    bar_top + bar_height,
                    bar_height / 2,
                    INK if index == 0 else "#65D99B",
                )
            y += height + _px(scale, 12)

        credits = snapshot.reset_credits
        credit_text = "—" if credits is None else str(credits.available_count)
        credit_height = _px(scale, 72)
        _rounded_rectangle(
            canvas,
            x,
            y,
            x + card_width,
            y + credit_height,
            _px(scale, 23),
            CARD,
        )
        canvas.create_text(
            x + _px(scale, 22),
            y + _px(scale, 26),
            text="Saved resets",
            anchor="nw",
            fill=MUTED,
            font=("Segoe UI Semibold", 10),
        )
        canvas.create_text(
            x + card_width - _px(scale, 23),
            y + _px(scale, 18),
            text=credit_text,
            anchor="ne",
            fill=INK,
            font=("Segoe UI Semibold", 22),
        )
        y += _px(scale, 84)

        usage = snapshot.account_usage
        if usage is not None:
            gap = _px(scale, 12)
            mini_width = (card_width - gap) / 2
            today = "—" if usage.today_tokens is None else _compact_number(usage.today_tokens)
            lifetime = (
                "—" if usage.lifetime_tokens is None else _compact_number(usage.lifetime_tokens)
            )
            _metric_card(canvas, x, y, mini_width, "Tokens today", today, scale)
            _metric_card(
                canvas,
                x + mini_width + gap,
                y,
                mini_width,
                "Lifetime",
                lifetime,
                scale,
            )
            y += _px(scale, 92)

        canvas.configure(scrollregion=(0, 0, width, y + _px(scale, 4)))

    def show_error(self, message: str) -> None:
        self.status_dot.configure(foreground="#F05B5B")
        self.status.set(message)
        self.updated.set("Will retry on the next refresh")


class SettingsDialog:
    def __init__(
        self,
        parent: tk.Tk,
        settings: AppSettings,
        choices: tuple[tuple[str, str], ...],
        save: Callable[[AppSettings], None],
    ) -> None:
        window = tk.Toplevel(parent, background=PAGE)
        window.withdraw()
        window.title("Settings — Codex Usage Tray")
        set_scaled_geometry(window, 520, 680)
        window.resizable(False, False)
        if parent.state() != "withdrawn":
            window.transient(parent)
        scale = scale_for_window(window)
        interval = tk.StringVar(value=str(settings.refresh_seconds))
        tray_metric = tk.StringVar(value=settings.tray_window)
        notify_20 = tk.BooleanVar(value=settings.notify_20)
        notify_10 = tk.BooleanVar(value=settings.notify_10)
        notify_0 = tk.BooleanVar(value=settings.notify_0)
        recovery = tk.BooleanVar(value=settings.notify_recovery)
        autostart = tk.BooleanVar(value=settings.autostart)
        updates = tk.BooleanVar(value=settings.check_updates)

        canvas = tk.Canvas(
            window,
            background=PAGE,
            highlightthickness=0,
            borderwidth=0,
        )
        canvas.pack(fill="both", expand=True)

        def text(
            x: int,
            y: int,
            value: str,
            *,
            fill: str,
            font: tuple[str, int],
        ) -> int:
            return canvas.create_text(
                _px(scale, x),
                _px(scale, y),
                text=value,
                anchor="nw",
                fill=fill,
                font=font,
            )

        text(30, 26, "Settings", fill=INK, font=("Segoe UI Semibold", 22))
        text(
            30,
            66,
            "Choose what appears in the tray and when to notify you.",
            fill=MUTED,
            font=("Segoe UI", 10),
        )

        card_left = _px(scale, 28)
        card_right = _px(scale, 492)
        radius = _px(scale, 22)

        _rounded_rectangle(
            canvas,
            card_left,
            _px(scale, 100),
            card_right,
            _px(scale, 224),
            radius,
            CARD,
        )
        text(50, 122, "Refresh interval", fill=INK, font=("Segoe UI Semibold", 10))
        interval_control = SegmentedControl(
            canvas,
            interval,
            (("30 sec", "30"), ("1 min", "60"), ("5 min", "300")),
            width=236,
        )
        canvas.create_window(
            _px(scale, 470),
            _px(scale, 118),
            window=interval_control,
            anchor="ne",
        )
        canvas.create_line(
            _px(scale, 50),
            _px(scale, 166),
            _px(scale, 470),
            _px(scale, 166),
            fill=LINE,
            width=max(1, _px(scale, 1)),
        )
        text(50, 187, "Tray value", fill=INK, font=("Segoe UI Semibold", 10))
        tray_choices = (
            ("Lowest remaining percentage", "lowest"),
            *((label, key) for key, label in choices),
        )
        tray_control = ModernDropdown(
            canvas,
            tray_metric,
            tray_choices,
            width=236,
        )
        canvas.create_window(
            _px(scale, 470),
            _px(scale, 177),
            window=tray_control,
            anchor="ne",
        )

        _rounded_rectangle(
            canvas,
            card_left,
            _px(scale, 240),
            card_right,
            _px(scale, 456),
            radius,
            CARD,
        )
        text(50, 258, "NOTIFICATIONS", fill=MUTED, font=("Segoe UI Semibold", 8))
        notification_rows = (
            ("Notify at 20% remaining", notify_20),
            ("Notify at 10% remaining", notify_10),
            ("Notify when the limit is reached", notify_0),
            ("Notify when a limit resets", recovery),
        )
        for index, (label, variable) in enumerate(notification_rows):
            row_y = 295 + index * 40
            text(50, row_y, label, fill=INK, font=("Segoe UI", 10))
            toggle = ToggleSwitch(canvas, variable)
            canvas.create_window(
                _px(scale, 470),
                _px(scale, row_y - 4),
                window=toggle,
                anchor="ne",
            )
            if index < len(notification_rows) - 1:
                canvas.create_line(
                    _px(scale, 50),
                    _px(scale, row_y + 30),
                    _px(scale, 470),
                    _px(scale, row_y + 30),
                    fill=LINE,
                    width=max(1, _px(scale, 1)),
                )

        _rounded_rectangle(
            canvas,
            card_left,
            _px(scale, 472),
            card_right,
            _px(scale, 604),
            radius,
            CARD,
        )
        text(50, 490, "SYSTEM", fill=MUTED, font=("Segoe UI Semibold", 8))
        system_rows = (
            ("Start with Windows", autostart),
            ("Check for updates at startup", updates),
        )
        for index, (label, variable) in enumerate(system_rows):
            row_y = 522 + index * 41
            text(50, row_y, label, fill=INK, font=("Segoe UI", 10))
            toggle = ToggleSwitch(canvas, variable)
            canvas.create_window(
                _px(scale, 470),
                _px(scale, row_y - 4),
                window=toggle,
                anchor="ne",
            )
        canvas.create_line(
            _px(scale, 50),
            _px(scale, 553),
            _px(scale, 470),
            _px(scale, 553),
            fill=LINE,
            width=max(1, _px(scale, 1)),
        )

        def commit() -> None:
            save(
                AppSettings(
                    refresh_seconds=int(interval.get()),
                    tray_window=tray_metric.get(),
                    notify_20=notify_20.get(),
                    notify_10=notify_10.get(),
                    notify_0=notify_0.get(),
                    notify_recovery=recovery.get(),
                    autostart=autostart.get(),
                    check_updates=updates.get(),
                )
            )
            window.destroy()

        cancel = PillButton(canvas, "Cancel", window.destroy, width=100)
        canvas.create_window(
            _px(scale, 354),
            _px(scale, 616),
            window=cancel,
            anchor="nw",
        )
        save_button = PillButton(
            canvas,
            "Save changes",
            commit,
            width=132,
            fill=LIME,
            hover="#D5F54F",
        )
        canvas.create_window(
            _px(scale, 214),
            _px(scale, 616),
            window=save_button,
            anchor="nw",
        )
        text(
            30,
            650,
            f"Codex Usage Tray {__version__}",
            fill=MUTED,
            font=("Segoe UI", 9),
        )
        window.protocol("WM_DELETE_WINDOW", window.destroy)
        center_window(window, parent)
        window.deiconify()
        window.update_idletasks()
        center_window(window, parent)
        window.lift()
        window.focus_force()
        window.grab_set()


def _metric_card(
    canvas: tk.Canvas,
    x: float,
    y: float,
    width: float,
    label: str,
    value: str,
    scale: float,
) -> None:
    _rounded_rectangle(
        canvas,
        x,
        y,
        x + width,
        y + _px(scale, 80),
        _px(scale, 23),
        CARD,
    )
    canvas.create_text(
        x + _px(scale, 20),
        y + _px(scale, 18),
        text=label,
        anchor="nw",
        fill=MUTED,
        font=("Segoe UI Semibold", 9),
    )
    canvas.create_text(
        x + _px(scale, 20),
        y + _px(scale, 42),
        text=value,
        anchor="nw",
        fill=INK,
        font=("Segoe UI Semibold", 16),
    )


def _px(scale: float, value: int) -> int:
    return max(1, round(value * scale))


def _gradient_card(width: int, height: int, radius: int) -> Image.Image:
    image = Image.new("RGBA", (width, height))
    pixels = image.load()
    assert pixels is not None
    left = (224, 255, 98)
    middle = (255, 244, 119)
    right = (183, 255, 222)
    for x in range(width):
        ratio = x / max(1, width - 1)
        if ratio < 0.52:
            color = _blend(left, middle, ratio / 0.52)
        else:
            color = _blend(middle, right, (ratio - 0.52) / 0.48)
        for y in range(height):
            pixels[x, y] = (*color, 255)
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1), radius, fill=255)
    image.putalpha(mask)
    return image


def _blend(
    start: tuple[int, int, int], end: tuple[int, int, int], amount: float
) -> tuple[int, int, int]:
    return tuple(round(a + (b - a) * amount) for a, b in zip(start, end, strict=True))  # type: ignore[return-value]


def _rounded_rectangle(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float,
    fill: str,
) -> int:
    points = (
        x1 + radius,
        y1,
        x2 - radius,
        y1,
        x2,
        y1,
        x2,
        y1 + radius,
        x2,
        y2 - radius,
        x2,
        y2,
        x2 - radius,
        y2,
        x1 + radius,
        y2,
        x1,
        y2,
        x1,
        y2 - radius,
        x1,
        y1 + radius,
        x1,
        y1,
    )
    return canvas.create_polygon(points, smooth=True, splinesteps=24, fill=fill, outline="")


def _compact_number(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def _format_reset(value: datetime | None) -> str:
    if value is None:
        return "Reset time unavailable"
    return f"Resets {value.astimezone():%a, %b %d at %H:%M}"
