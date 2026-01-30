r"""Consolidated integration tests for all async HTTP methods with automatic retry logic.

This module consolidates integration tests for async get, post, put, patch, and delete methods
using pytest parameterization to reduce code duplication. These tests make real HTTP
requests to httpbin.org.
"""

from __future__ import annotations

import httpx
import pytest

from aresnet import (
    delete_with_automatic_retry_async,
    get_with_automatic_retry_async,
    patch_with_automatic_retry_async,
    post_with_automatic_retry_async,
    put_with_automatic_retry_async,
)

# Use httpbin.org for real HTTP testing
HTTPBIN_URL = "https://httpbin.org"


# Define async HTTP methods with their functions and endpoints
HTTP_METHODS_ASYNC_INTEGRATION = [
    ("GET", get_with_automatic_retry_async, "/get"),
    ("POST", post_with_automatic_retry_async, "/post"),
    ("PUT", put_with_automatic_retry_async, "/put"),
    ("PATCH", patch_with_automatic_retry_async, "/patch"),
    ("DELETE", delete_with_automatic_retry_async, "/delete"),
]


# Async methods that support request body (JSON, form data)
BODY_METHODS_ASYNC = [
    ("POST", post_with_automatic_retry_async, "/post"),
    ("PUT", put_with_automatic_retry_async, "/put"),
    ("PATCH", patch_with_automatic_retry_async, "/patch"),
]


##############################################################
#     Consolidated async integration tests for all methods   #
##############################################################


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name,retry_func,endpoint", HTTP_METHODS_ASYNC_INTEGRATION)
async def test_async_successful_request_with_client(
    method_name: str, retry_func: callable, endpoint: str
) -> None:
    """Test successful async request with provided client."""
    async with httpx.AsyncClient() as client:
        if method_name in ["POST", "PUT", "PATCH"]:
            response = await retry_func(
                url=f"{HTTPBIN_URL}{endpoint}",
                json={"test": "data", "number": 42},
                client=client,
            )
        else:
            response = await retry_func(url=f"{HTTPBIN_URL}{endpoint}", client=client)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["url"] == f"https://httpbin.org{endpoint}"


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name,retry_func,endpoint", HTTP_METHODS_ASYNC_INTEGRATION)
async def test_async_successful_request_without_client(
    method_name: str, retry_func: callable, endpoint: str
) -> None:
    """Test successful async request without providing a client."""
    if method_name in ["POST", "PUT", "PATCH"]:
        response = await retry_func(url=f"{HTTPBIN_URL}{endpoint}", json={"test": "data", "number": 42})
    else:
        response = await retry_func(url=f"{HTTPBIN_URL}{endpoint}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["url"] == f"https://httpbin.org{endpoint}"


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name,retry_func,endpoint", HTTP_METHODS_ASYNC_INTEGRATION)
async def test_async_non_retryable_status_fails_immediately(
    method_name: str, retry_func: callable, endpoint: str
) -> None:
    """Test that 404 (non-retryable) fails immediately without retries."""
    async with httpx.AsyncClient() as client:
        with pytest.raises(httpx.HTTPStatusError, match=r"Client error '404 NOT FOUND'"):
            await retry_func(url=f"{HTTPBIN_URL}/status/404", client=client)


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name,retry_func,endpoint", HTTP_METHODS_ASYNC_INTEGRATION)
async def test_async_with_custom_headers(
    method_name: str, retry_func: callable, endpoint: str
) -> None:
    """Test async request with custom headers."""
    async with httpx.AsyncClient() as client:
        if method_name in ["POST", "PUT", "PATCH"]:
            response = await retry_func(
                url=f"{HTTPBIN_URL}{endpoint}",
                client=client,
                json={"test": "data"},
                headers={"X-Custom-Header": "test-value"},
            )
        else:
            response = await retry_func(
                url=f"{HTTPBIN_URL}{endpoint}",
                client=client,
                headers={"X-Custom-Header": "test-value"},
            )

    assert response.status_code == 200
    response_data = response.json()
    assert "X-Custom-Header" in response_data["headers"]
    assert response_data["headers"]["X-Custom-Header"] == "test-value"


# Tests specific to async methods that support request body
@pytest.mark.asyncio
@pytest.mark.parametrize("method_name,retry_func,endpoint", BODY_METHODS_ASYNC)
async def test_async_with_large_json_payload(
    method_name: str, retry_func: callable, endpoint: str
) -> None:
    """Test async request with large JSON payload."""
    large_data = {"items": [{"id": i, "data": "x" * 100} for i in range(100)]}

    async with httpx.AsyncClient() as client:
        response = await retry_func(url=f"{HTTPBIN_URL}{endpoint}", json=large_data, client=client)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["json"]["items"][0]["id"] == 0
    assert len(response_data["json"]["items"]) == 100


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name,retry_func,endpoint", BODY_METHODS_ASYNC)
async def test_async_with_form_data(method_name: str, retry_func: callable, endpoint: str) -> None:
    """Test async request with form data."""
    async with httpx.AsyncClient() as client:
        response = await retry_func(
            url=f"{HTTPBIN_URL}{endpoint}",
            data={"field1": "value1", "field2": "value2"},
            client=client,
        )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["form"] == {"field1": "value1", "field2": "value2"}


# Tests specific to async GET and DELETE (methods that commonly use query params)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method_name,retry_func,endpoint",
    [
        ("GET", get_with_automatic_retry_async, "/get"),
        ("DELETE", delete_with_automatic_retry_async, "/delete"),
    ],
)
async def test_async_with_query_params(
    method_name: str, retry_func: callable, endpoint: str
) -> None:
    """Test async request with query parameters."""
    async with httpx.AsyncClient() as client:
        response = await retry_func(
            url=f"{HTTPBIN_URL}{endpoint}",
            params={"param1": "value1", "param2": "value2"},
            client=client,
        )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["args"] == {"param1": "value1", "param2": "value2"}


# Async GET-specific tests
@pytest.mark.asyncio
async def test_async_get_with_redirect_chain() -> None:
    """Test async GET request that follows a redirect chain."""
    # httpbin.org supports redirects: /redirect/n redirects n times
    # Create a client with follow_redirects=True to handle the redirect chain
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await get_with_automatic_retry_async(
            url=f"{HTTPBIN_URL}/redirect/3", client=client
        )

    assert response.status_code == 200
    # After redirects, we should end up at /get
    response_data = response.json()
    assert "url" in response_data


@pytest.mark.asyncio
async def test_async_get_with_large_response() -> None:
    """Test async GET request with large response body."""
    # Request a large amount of bytes (10KB)
    async with httpx.AsyncClient() as client:
        response = await get_with_automatic_retry_async(
            url=f"{HTTPBIN_URL}/bytes/10240", client=client
        )

    assert response.status_code == 200
    assert len(response.content) == 10240
