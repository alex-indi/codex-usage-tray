from __future__ import annotations

import io

from codex_usage_tray.updater import check_for_update


class Response(io.BytesIO):
    def __enter__(self) -> Response:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def opener(payload: bytes):  # type: ignore[no-untyped-def]
    def open_response(_request, *, timeout):  # type: ignore[no-untyped-def]
        assert timeout == 5.0
        return Response(payload)

    return open_response


def test_update_is_reported_without_download() -> None:
    result = check_for_update(
        opener(b'{"tag_name":"v0.2.0","html_url":"https://example.test/release"}'),
        current_version="0.1.0",
    )
    assert result is not None and result.version == "0.2.0"


def test_current_release_is_ignored() -> None:
    result = check_for_update(
        opener(b'{"tag_name":"v0.1.0","html_url":"https://example.test/release"}'),
        current_version="0.1.0",
    )
    assert result is None
