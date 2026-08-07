from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BRAND_NAVY = "#101827"
BRAND_BLUE = "#45A3FF"
BRAND_MINT = "#62E6B3"


def brand_icon(size: int = 256) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    pad = size * 0.08
    radius = size * 0.22
    draw.rounded_rectangle((pad, pad, size - pad, size - pad), radius=radius, fill=BRAND_NAVY)
    width = max(2, round(size * 0.085))
    box = (size * 0.27, size * 0.27, size * 0.73, size * 0.73)
    draw.arc(box, 135, 405, fill=BRAND_BLUE, width=width)
    draw.arc(box, 45, 135, fill=BRAND_MINT, width=width)
    return image


def tray_icon(
    percent: int | None,
    size: int = 64,
    *,
    foreground: str | None = None,
) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    text = "--" if percent is None else str(max(0, min(100, percent)))
    draw = ImageDraw.Draw(image)
    font = _font(round(size * (0.73 if len(text) <= 2 else 0.57)))
    box = draw.textbbox((0, 0), text, font=font)
    width, height = box[2] - box[0], box[3] - box[1]
    x = (size - width) / 2 - box[0]
    y = (size - height) / 2 - box[1]
    draw.text((x, y), text, font=font, fill=foreground or _tray_foreground())
    return image


def write_brand_assets(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    image = brand_icon(256)
    image.save(output_dir / "icon.png")
    image.save(
        output_dir / "icon.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _tray_foreground() -> str:
    """Use the Windows taskbar theme so bare digits stay legible without an outline."""
    if sys.platform != "win32":
        return "white"
    try:
        import winreg

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            light, _kind = winreg.QueryValueEx(key, "SystemUsesLightTheme")
        return "#111111" if light else "white"
    except OSError:
        return "white"
