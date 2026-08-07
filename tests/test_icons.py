from __future__ import annotations

from codex_usage_tray.icons import tray_icon


def test_tray_digits_are_transparent_and_have_no_outline() -> None:
    image = tray_icon(68, foreground="#111111")
    colors = set(image.get_flattened_data())
    assert (0, 0, 0, 0) in colors
    assert any(alpha > 0 and red < 40 for red, _green, _blue, alpha in colors)
    assert not any(alpha > 0 and red > 220 for red, _green, _blue, alpha in colors)


def test_tray_value_is_clamped_and_supports_three_digits() -> None:
    assert tray_icon(150, foreground="white").getbbox() is not None
    assert tray_icon(-10, foreground="white").getbbox() is not None
