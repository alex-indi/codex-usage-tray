from __future__ import annotations

import argparse

from codex_usage_tray import __version__
from codex_usage_tray.dpi import enable_high_dpi_awareness


def main() -> None:
    enable_high_dpi_awareness()
    parser = argparse.ArgumentParser(description="Monitor Codex usage limits in the system tray.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="show demonstration data without starting Codex or using the network",
    )
    arguments = parser.parse_args()
    from codex_usage_tray.app import Application

    Application(demo=arguments.demo).run()


if __name__ == "__main__":
    main()
