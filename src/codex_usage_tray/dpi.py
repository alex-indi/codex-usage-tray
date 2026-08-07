from __future__ import annotations

import sys
import tkinter as tk


def enable_high_dpi_awareness() -> None:
    """Opt out of Windows bitmap scaling before the first window is created."""
    if sys.platform != "win32":
        return
    import ctypes

    try:
        per_monitor_v2 = ctypes.c_void_p(-4)
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(per_monitor_v2):
            return
    except AttributeError, OSError:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except AttributeError, OSError:
        ctypes.windll.user32.SetProcessDPIAware()


def configure_tk_scaling(root: tk.Tk) -> None:
    """Render point-sized fonts at the monitor's real DPI instead of a bitmap-scaled DPI."""
    pixels_per_inch = float(root.winfo_fpixels("1i"))
    scaling = max(1.0, min(4.0, pixels_per_inch / 72.0))
    root.tk.call("tk", "scaling", scaling)


def scale_for_window(window: tk.Misc) -> float:
    if sys.platform != "win32":
        return 1.0
    import ctypes

    try:
        dpi = int(ctypes.windll.user32.GetDpiForWindow(window.winfo_id()))
    except AttributeError, OSError:
        return 1.0
    return max(1.0, min(4.0, dpi / 96.0)) if dpi else 1.0


def set_scaled_geometry(
    window: tk.Tk | tk.Toplevel,
    width: int,
    height: int,
    *,
    minimum: tuple[int, int] | None = None,
) -> None:
    scale = scale_for_window(window)
    window.geometry(f"{round(width * scale)}x{round(height * scale)}")
    if minimum is not None:
        window.minsize(round(minimum[0] * scale), round(minimum[1] * scale))


def center_window(
    window: tk.Tk | tk.Toplevel,
    parent: tk.Tk | tk.Toplevel | None = None,
) -> None:
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    if parent is None:
        border = max(0, window.winfo_rootx() - window.winfo_x())
        title_bar = max(border, window.winfo_rooty() - window.winfo_y())
        outer_width = width + border * 2
        outer_height = height + title_bar + border
        x = max(0, (window.winfo_screenwidth() - outer_width) // 2)
        y = max(0, (window.winfo_screenheight() - outer_height) // 2)
    else:
        parent.update_idletasks()
        # For a top-level parent, winfo_x/y are the outer-frame coordinates.
        # winfo_rootx/y point to the client area and would shift a child by the
        # title-bar and border thickness.
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
    window.geometry(f"+{x}+{y}")
