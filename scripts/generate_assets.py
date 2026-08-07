from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from codex_usage_tray.icons import (  # noqa: E402
    BRAND_BLUE,
    BRAND_MINT,
    BRAND_NAVY,
    brand_icon,
    tray_icon,
    write_brand_assets,
)


def font(size: int, bold: bool = False):  # type: ignore[no-untyped-def]
    names = ("segoeuib.ttf", "arialbd.ttf") if bold else ("segoeui.ttf", "arial.ttf")
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def social_preview() -> Image.Image:
    image = Image.new("RGB", (1280, 640), BRAND_NAVY)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((65, 70, 575, 570), radius=32, fill="#18253A")
    image.alpha_composite(brand_icon(96), (104, 105)) if image.mode == "RGBA" else image.paste(
        brand_icon(96), (104, 105), brand_icon(96)
    )
    draw.text((220, 111), "Codex Usage Tray", font=font(34, True), fill="white")
    draw.text((105, 230), "Codex — 3-hour window", font=font(24, True), fill="#D7E1EE")
    draw.text((105, 275), "68%", font=font(78, True), fill="white")
    draw.text((280, 315), "remaining", font=font(24), fill="#9FB1C8")
    draw.rounded_rectangle((105, 390, 535, 412), radius=11, fill="#2B3A50")
    draw.rounded_rectangle((105, 390, 397, 412), radius=11, fill=BRAND_BLUE)
    draw.text((105, 450), "Saved resets", font=font(22), fill="#9FB1C8")
    draw.text((500, 445), "2", font=font(30, True), fill=BRAND_MINT, anchor="ra")
    draw.text((650, 145), "Your Codex limits,", font=font(49, True), fill="white")
    draw.text((650, 210), "always visible.", font=font(49, True), fill=BRAND_MINT)
    draw.text((650, 315), "Windows-first · privacy-first", font=font(28), fill="#C0CCDA")
    draw.text((650, 365), "No credential collection", font=font(25), fill="#9FB1C8")
    draw.text((650, 407), "Dynamic limit windows", font=font(25), fill="#9FB1C8")
    draw.text((650, 449), "Saved reset visibility", font=font(25), fill="#9FB1C8")
    return image


def tray_contrast_preview() -> Image.Image:
    image = Image.new("RGB", (560, 220), "#E9E9E9")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((24, 24, 268, 196), radius=28, fill="#F6F6F6")
    draw.rounded_rectangle((292, 24, 536, 196), radius=28, fill="#202124")
    light_icon = tray_icon(68, 96, foreground="#111111")
    dark_icon = tray_icon(68, 96, foreground="white")
    image.paste(light_icon, (98, 52), light_icon)
    image.paste(dark_icon, (366, 52), dark_icon)
    draw.text((146, 164), "LIGHT", font=font(14, True), fill="#858585", anchor="mm")
    draw.text((414, 164), "DARK", font=font(14, True), fill="#BDBDBD", anchor="mm")
    return image


def main() -> None:
    assets = ROOT / "assets"
    write_brand_assets(assets)
    preview = social_preview()
    preview.save(assets / "social-preview.png", optimize=True)
    tray_contrast_preview().save(assets / "tray-contrast-preview.png", optimize=True)
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    preview.save(docs / "social-preview.png", optimize=True)
    brand_icon(256).save(docs / "icon.png", optimize=True)


if __name__ == "__main__":
    main()
