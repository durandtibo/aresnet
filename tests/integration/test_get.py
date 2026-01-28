from __future__ import annotations

import httpx
import pytest

from aresnet import get_with_automatic_retry

# Use httpbin.org for real HTTP testing
HTTPBIN_URL = "https://httpbin.org"


##############################################
#     Tests for get_with_automatic_retry     #
##############################################


def test_get_with_automatic_retry_successful_request() -> None:
    """Test successful GET request without retries."""
    response = get_with_automatic_retry(url=f"{HTTPBIN_URL}/get")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["url"] == "https://httpbin.org/get"


def test_get_with_automatic_retry_successful_request_with_client() -> None:
    """Test successful GET request without retries."""
    with httpx.Client() as client:
        response = get_with_automatic_retry(url=f"{HTTPBIN_URL}/get", client=client)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["url"] == "https://httpbin.org/get"


def test_get_with_non_retryable_status_fails_immediately() -> None:
    """Test that 404 (non-retryable) fails immediately without
    retries."""
    with pytest.raises(httpx.HTTPStatusError):
        get_with_automatic_retry(url=f"{HTTPBIN_URL}/status/404")
