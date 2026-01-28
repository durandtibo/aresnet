r"""Root package."""

from __future__ import annotations

__all__ = [
    "DEFAULT_BACKOFF_FACTOR",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_TIMEOUT",
    "RETRY_STATUS_CODES",
    "HttpRequestError",
    "get_with_automatic_retry",
    "post_with_automatic_retry",
]

from aresnet.config import (
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    RETRY_STATUS_CODES,
)
from aresnet.exception import HttpRequestError
from aresnet.get import get_with_automatic_retry
from aresnet.post import post_with_automatic_retry
