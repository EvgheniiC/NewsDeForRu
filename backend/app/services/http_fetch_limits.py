"""Shared helpers for bounded outbound HTTP body reads."""

from __future__ import annotations

import httpx


class ResponseTooLargeError(RuntimeError):
    """Raised when a response exceeds the configured byte limit."""


def read_http_body_with_limit(response: httpx.Response, max_bytes: int) -> bytes:
    content_length: str | None = response.headers.get("Content-Length")
    if content_length is not None:
        try:
            declared: int = int(content_length)
        except ValueError:
            declared = 0
        if declared > max_bytes:
            response.close()
            raise ResponseTooLargeError(f"Content-Length {declared} exceeds limit {max_bytes}")

    chunks: list[bytes] = []
    total: int = 0
    for chunk in response.iter_bytes():
        total += len(chunk)
        if total > max_bytes:
            response.close()
            raise ResponseTooLargeError(f"Response body {total} exceeds limit {max_bytes}")
        chunks.append(chunk)
    return b"".join(chunks)
