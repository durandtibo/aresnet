r"""Consolidated integration tests for all HTTP methods with automatic retry logic.

This module consolidates integration tests for get, post, put, patch, and delete methods
using pytest parameterization to reduce code duplication. These tests make real HTTP
requests to httpbin.org.
"""

from __future__ import annotations

import httpx
import pytest

from aresnet import (
    delete_with_automatic_retry,
    get_with_automatic_retry,
    patch_with_automatic_retry,
    post_with_automatic_retry,
    put_with_automatic_retry,
)

# Use httpbin.org for real HTTP testing
HTTPBIN_URL = "https://httpbin.org"


# Define HTTP methods with their functions and endpoints
HTTP_METHODS_INTEGRATION = [
    ("GET", get_with_automatic_retry, "/get"),
    ("POST", post_with_automatic_retry, "/post"),
    ("PUT", put_with_automatic_retry, "/put"),
    ("PATCH", patch_with_automatic_retry, "/patch"),
    ("DELETE", delete_with_automatic_retry, "/delete"),
]


# Methods that support request body (JSON, form data)
BODY_METHODS = [
    ("POST", post_with_automatic_retry, "/post"),
    ("PUT", put_with_automatic_retry, "/put"),
    ("PATCH", patch_with_automatic_retry, "/patch"),
]


######################################################
#     Consolidated integration tests for all methods #
######################################################


@pytest.mark.parametrize("method_name,retry_func,endpoint", HTTP_METHODS_INTEGRATION)
def test_successful_request_with_client(method_name: str, retry_func: callable, endpoint: str) -> None:
    """Test successful request with provided client."""
    with httpx.Client() as client:
        if method_name in ["POST", "PUT", "PATCH"]:
            response = retry_func(
                url=f"{HTTPBIN_URL}{endpoint}",
                json={"test": "data", "number": 42},
                client=client,
            )
        else:
            response = retry_func(url=f"{HTTPBIN_URL}{endpoint}", client=client)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["url"] == f"https://httpbin.org{endpoint}"


@pytest.mark.parametrize("method_name,retry_func,endpoint", HTTP_METHODS_INTEGRATION)
def test_successful_request_without_client(
    method_name: str, retry_func: callable, endpoint: str
) -> None:
    """Test successful request without providing a client."""
    if method_name in ["POST", "PUT", "PATCH"]:
        response = retry_func(url=f"{HTTPBIN_URL}{endpoint}", json={"test": "data", "number": 42})
    else:
        response = retry_func(url=f"{HTTPBIN_URL}{endpoint}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["url"] == f"https://httpbin.org{endpoint}"


@pytest.mark.parametrize("method_name,retry_func,endpoint", HTTP_METHODS_INTEGRATION)
def test_non_retryable_status_fails_immediately(
    method_name: str, retry_func: callable, endpoint: str
) -> None:
    """Test that 404 (non-retryable) fails immediately without retries."""
    with (
        httpx.Client() as client,
        pytest.raises(httpx.HTTPStatusError, match=r"Client error '404 NOT FOUND'"),
    ):
        retry_func(url=f"{HTTPBIN_URL}/status/404", client=client)


@pytest.mark.parametrize("method_name,retry_func,endpoint", HTTP_METHODS_INTEGRATION)
def test_with_custom_headers(method_name: str, retry_func: callable, endpoint: str) -> None:
    """Test request with custom headers."""
    with httpx.Client() as client:
        if method_name in ["POST", "PUT", "PATCH"]:
            response = retry_func(
                url=f"{HTTPBIN_URL}{endpoint}",
                client=client,
                json={"test": "data"},
                headers={"X-Custom-Header": "test-value"},
            )
        else:
            response = retry_func(
                url=f"{HTTPBIN_URL}{endpoint}",
                client=client,
                headers={"X-Custom-Header": "test-value"},
            )

    assert response.status_code == 200
    response_data = response.json()
    assert "X-Custom-Header" in response_data["headers"]
    assert response_data["headers"]["X-Custom-Header"] == "test-value"


# Tests specific to methods that support request body
@pytest.mark.parametrize("method_name,retry_func,endpoint", BODY_METHODS)
def test_with_large_json_payload(method_name: str, retry_func: callable, endpoint: str) -> None:
    """Test request with large JSON payload."""
    large_data = {"items": [{"id": i, "data": "x" * 100} for i in range(100)]}

    with httpx.Client() as client:
        response = retry_func(url=f"{HTTPBIN_URL}{endpoint}", json=large_data, client=client)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["json"]["items"][0]["id"] == 0
    assert len(response_data["json"]["items"]) == 100


@pytest.mark.parametrize("method_name,retry_func,endpoint", BODY_METHODS)
def test_with_form_data(method_name: str, retry_func: callable, endpoint: str) -> None:
    """Test request with form data."""
    with httpx.Client() as client:
        response = retry_func(
            url=f"{HTTPBIN_URL}{endpoint}",
            data={"field1": "value1", "field2": "value2"},
            client=client,
        )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["form"] == {"field1": "value1", "field2": "value2"}


# Tests specific to GET and DELETE (methods that commonly use query params)
@pytest.mark.parametrize(
    "method_name,retry_func,endpoint",
    [
        ("GET", get_with_automatic_retry, "/get"),
        ("DELETE", delete_with_automatic_retry, "/delete"),
    ],
)
def test_with_query_params(method_name: str, retry_func: callable, endpoint: str) -> None:
    """Test request with query parameters."""
    with httpx.Client() as client:
        response = retry_func(
            url=f"{HTTPBIN_URL}{endpoint}",
            params={"param1": "value1", "param2": "value2"},
            client=client,
        )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["args"] == {"param1": "value1", "param2": "value2"}


# GET-specific tests (features that are primarily used with GET)
def test_get_with_redirect_chain() -> None:
    """Test GET request that follows a redirect chain."""
    # httpbin.org supports redirects: /redirect/n redirects n times
    # Create a client with follow_redirects=True to handle the redirect chain
    with httpx.Client(follow_redirects=True) as client:
        response = get_with_automatic_retry(url=f"{HTTPBIN_URL}/redirect/3", client=client)

    assert response.status_code == 200
    # After redirects, we should end up at /get
    response_data = response.json()
    assert "url" in response_data


def test_get_with_large_response() -> None:
    """Test GET request with large response body."""
    # Request a large amount of bytes (10KB)
    with httpx.Client() as client:
        response = get_with_automatic_retry(url=f"{HTTPBIN_URL}/bytes/10240", client=client)

    assert response.status_code == 200
    assert len(response.content) == 10240
