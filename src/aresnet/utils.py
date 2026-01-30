r"""Contain utility functions for HTTP requests."""

from __future__ import annotations

__all__ = ["parse_retry_after", "validate_retry_params"]

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

logger: logging.Logger = logging.getLogger(__name__)


def validate_retry_params(max_retries: int, backoff_factor: float) -> None:
    """Validate retry parameters.

    Args:
        max_retries: Maximum number of retry attempts for failed requests.
            Must be >= 0.
        backoff_factor: Factor for exponential backoff between retries.
            Must be >= 0.

    Raises:
        ValueError: If max_retries or backoff_factor are negative.

    Example:
        ```pycon
        >>> from aresnet.utils import validate_retry_params
        >>> validate_retry_params(max_retries=3, backoff_factor=0.5)
        >>> validate_retry_params(max_retries=-1, backoff_factor=0.5)  # doctest: +SKIP

        ```
    """
    if max_retries < 0:
        msg = f"max_retries must be >= 0, got {max_retries}"
        raise ValueError(msg)
    if backoff_factor < 0:
        msg = f"backoff_factor must be >= 0, got {backoff_factor}"
        raise ValueError(msg)


def parse_retry_after(retry_after_header: str | None) -> float | None:
    """Parse the Retry-After header value from an HTTP response.

    The Retry-After header can be specified in two formats:
    1. An integer representing the number of seconds to wait
    2. An HTTP-date in RFC 5322 format

    Args:
        retry_after_header: The value of the Retry-After header, or None
            if the header is not present.

    Returns:
        The number of seconds to wait before retrying, or None if the
        header is absent or cannot be parsed.

    Example:
        ```pycon
        >>> from aresnet.utils import parse_retry_after
        >>> parse_retry_after("120")
        120.0
        >>> parse_retry_after("0")
        0.0
        >>> parse_retry_after(None)
        >>> parse_retry_after("invalid")

        ```
    """
    if retry_after_header is None:
        return None

    # Try parsing as an integer (seconds)
    try:
        return float(retry_after_header)
    except ValueError:
        pass

    # Try parsing as HTTP-date (RFC 5322 format)
    try:
        retry_date: datetime = parsedate_to_datetime(retry_after_header)
        now = datetime.now(timezone.utc)
        delta_seconds = (retry_date - now).total_seconds()
        # Ensure we don't return negative values
        return max(0.0, delta_seconds)
    except (ValueError, TypeError, OverflowError):
        logger.debug(f"Failed to parse Retry-After header: {retry_after_header!r}")
        return None
