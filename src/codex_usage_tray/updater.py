from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen

from . import __version__

LATEST_RELEASE_URL = "https://api.github.com/repos/alex-indi/codex-usage-tray/releases/latest"


@dataclass(frozen=True, slots=True)
class UpdateInfo:
    version: str
    page_url: str


def check_for_update(
    opener: Any = urlopen,
    *,
    current_version: str = __version__,
    timeout: float = 5.0,
) -> UpdateInfo | None:
    request = Request(
        LATEST_RELEASE_URL,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "CodexUsageTray"},
    )
    with opener(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict):
        return None
    tag = data.get("tag_name")
    page = data.get("html_url")
    if not isinstance(tag, str) or not isinstance(page, str):
        return None
    remote = tag.removeprefix("v")
    if _version_tuple(remote) <= _version_tuple(current_version):
        return None
    return UpdateInfo(remote, page)


def _version_tuple(version: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return ()
