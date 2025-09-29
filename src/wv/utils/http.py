"""HTTP 유틸리티. HTTP utilities."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from wv.providers.base import ProviderError

LOGGER = logging.getLogger(__name__)


def request_json(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 10.0,
    retries: int = 3,
    backoff_factor: float = 1.5,
) -> Any:
    """HTTP JSON 요청. Perform HTTP JSON request."""

    attempt = 0
    delay = 1.0
    while True:
        try:
            response = httpx.request(method, url, params=params, headers=headers, timeout=timeout)
        except httpx.HTTPError as exc:
            attempt += 1
            if attempt > retries:
                raise ProviderError(f"HTTP error for {url}: {exc}") from exc
            time.sleep(delay)
            delay *= backoff_factor
            continue

        if response.status_code == 429:
            attempt += 1
            if attempt > retries:
                raise ProviderError(f"Rate limit hit for {url}")
            sleep_time = delay
            LOGGER.warning("Rate limited: sleeping %.1fs", sleep_time)
            time.sleep(sleep_time)
            delay *= backoff_factor
            continue

        if response.status_code >= 500:
            attempt += 1
            if attempt > retries:
                raise ProviderError(f"Server error {response.status_code} for {url}")
            time.sleep(delay)
            delay *= backoff_factor
            continue

        if response.status_code >= 400:
            raise ProviderError(f"Client error {response.status_code} for {url}: {response.text}")

        try:
            return response.json()
        except ValueError as exc:  # noqa: PERF203
            raise ProviderError(f"Invalid JSON from {url}") from exc


__all__ = ["request_json"]
