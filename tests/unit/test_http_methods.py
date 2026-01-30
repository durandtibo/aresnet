r"""Consolidated unit tests for all HTTP methods with automatic retry logic.

This module consolidates tests for get, post, put, patch, and delete methods
using pytest parameterization to reduce code duplication while maintaining
full test coverage.
"""

from __future__ import annotations

from unittest.mock import Mock, call, patch

import httpx
import pytest

from aresnet import (
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_MAX_RETRIES,
    RETRY_STATUS_CODES,
    HttpRequestError,
    delete_with_automatic_retry,
    get_with_automatic_retry,
    patch_with_automatic_retry,
    post_with_automatic_retry,
    put_with_automatic_retry,
)

TEST_URL = "https://api.example.com/data"


# Map of method names to their functions and client method names
HTTP_METHODS = [
    ("GET", get_with_automatic_retry, "get"),
    ("POST", post_with_automatic_retry, "post"),
    ("PUT", put_with_automatic_retry, "put"),
    ("PATCH", patch_with_automatic_retry, "patch"),
    ("DELETE", delete_with_automatic_retry, "delete"),
]


@pytest.fixture
def mock_response() -> httpx.Response:
    """Create a mock successful HTTP response."""
    return Mock(spec=httpx.Response, status_code=200)


def create_mock_client(mock_response: httpx.Response, client_method: str) -> httpx.Client:
    """Create a mock client with the specified method."""
    return Mock(spec=httpx.Client, **{client_method: Mock(return_value=mock_response)})


###################################################
#     Tests for all HTTP methods (consolidated)   #
###################################################


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_successful_request_with_custom_client(
    mock_response: httpx.Response,
    mock_sleep: Mock,
    method_name: str,
    retry_func: callable,
    client_method: str,
) -> None:
    """Test successful request with custom client."""
    mock_client = create_mock_client(mock_response, client_method)
    response = retry_func(TEST_URL, client=mock_client)

    assert response.status_code == 200
    getattr(mock_client, client_method).assert_called_once_with(url=TEST_URL)
    mock_sleep.assert_not_called()


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_successful_request_with_default_client(
    mock_response: httpx.Response, mock_sleep: Mock, method_name: str, retry_func: callable, client_method: str
) -> None:
    """Test successful request with default client."""
    with patch(f"httpx.Client.{client_method}", return_value=mock_response):
        response = retry_func(TEST_URL)

    assert response.status_code == 200
    mock_sleep.assert_not_called()


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_request_with_json_payload(
    mock_response: httpx.Response,
    mock_sleep: Mock,
    method_name: str,
    retry_func: callable,
    client_method: str,
) -> None:
    """Test request with JSON data."""
    mock_client = create_mock_client(mock_response, client_method)
    response = retry_func(TEST_URL, json={"key": "value"}, client=mock_client)

    assert response.status_code == 200
    getattr(mock_client, client_method).assert_called_once_with(url=TEST_URL, json={"key": "value"})
    mock_sleep.assert_not_called()


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_retry_on_500_status(
    mock_response: httpx.Response,
    mock_sleep: Mock,
    method_name: str,
    retry_func: callable,
    client_method: str,
) -> None:
    """Test retry logic for 500 status code."""
    mock_response_fail = Mock(spec=httpx.Response, status_code=500)
    mock_client = create_mock_client(mock_response, client_method)
    getattr(mock_client, client_method).side_effect = [mock_response_fail, mock_response]

    response = retry_func(TEST_URL, client=mock_client)

    assert response.status_code == 200
    mock_sleep.assert_called_once_with(0.3)


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_retry_on_503_status(
    mock_response: httpx.Response,
    mock_sleep: Mock,
    method_name: str,
    retry_func: callable,
    client_method: str,
) -> None:
    """Test retry logic for 503 status code."""
    mock_response_fail = Mock(spec=httpx.Response, status_code=503)
    mock_client = create_mock_client(mock_response, client_method)
    getattr(mock_client, client_method).side_effect = [mock_response_fail, mock_response]

    response = retry_func(TEST_URL, client=mock_client)

    assert response.status_code == 200
    mock_sleep.assert_called_once_with(0.3)


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_max_retries_exceeded(
    mock_sleep: Mock, method_name: str, retry_func: callable, client_method: str
) -> None:
    """Test that HttpRequestError is raised when max retries exceeded."""
    mock_response = Mock(spec=httpx.Response, status_code=503)
    mock_client = Mock(spec=httpx.Client, **{client_method: Mock(return_value=mock_response)})

    with pytest.raises(HttpRequestError) as exc_info:
        retry_func(TEST_URL, client=mock_client, max_retries=2)

    assert exc_info.value.status_code == 503
    assert "failed with status 503 after 3 attempts" in str(exc_info.value)
    assert mock_sleep.call_args_list == [call(0.3), call(0.6)]


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_non_retryable_status_code(
    mock_sleep: Mock, method_name: str, retry_func: callable, client_method: str
) -> None:
    """Test that 404 status code is not retried."""
    mock_response = Mock(spec=httpx.Response, status_code=404)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=Mock(), response=mock_response
    )
    mock_client = Mock(spec=httpx.Client, **{client_method: Mock(return_value=mock_response)})

    with pytest.raises(httpx.HTTPStatusError, match=r"Not Found"):
        retry_func(TEST_URL, client=mock_client)

    mock_sleep.assert_not_called()


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_exponential_backoff(
    mock_response: httpx.Response,
    mock_sleep: Mock,
    method_name: str,
    retry_func: callable,
    client_method: str,
) -> None:
    """Test exponential backoff timing."""
    mock_response_fail = Mock(spec=httpx.Response, status_code=503)
    mock_client = create_mock_client(mock_response, client_method)
    getattr(mock_client, client_method).side_effect = [
        mock_response_fail,
        mock_response_fail,
        mock_response,
    ]

    retry_func(TEST_URL, client=mock_client, backoff_factor=2.0)

    # Should have slept twice (after 1st and 2nd failures)
    assert mock_sleep.call_args_list == [call(2.0), call(4.0)]


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_timeout_exception(
    mock_sleep: Mock, method_name: str, retry_func: callable, client_method: str
) -> None:
    """Test handling of timeout exception."""
    mock_client = Mock(
        spec=httpx.Client,
        **{client_method: Mock(side_effect=httpx.TimeoutException("Request timeout"))},
    )

    with pytest.raises(
        HttpRequestError,
        match=rf"{method_name} request to {TEST_URL} timed out \(1 attempts\)",
    ):
        retry_func(TEST_URL, client=mock_client, max_retries=0)

    mock_sleep.assert_not_called()


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_timeout_exception_with_retries(
    mock_sleep: Mock, method_name: str, retry_func: callable, client_method: str
) -> None:
    """Test timeout exception with retries."""
    mock_client = Mock(
        spec=httpx.Client,
        **{client_method: Mock(side_effect=httpx.TimeoutException("Request timeout"))},
    )

    with pytest.raises(
        HttpRequestError,
        match=rf"{method_name} request to {TEST_URL} timed out \(3 attempts\)",
    ):
        retry_func(TEST_URL, client=mock_client, max_retries=2)

    assert mock_sleep.call_args_list == [call(0.3), call(0.6)]


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_request_error(mock_sleep: Mock, method_name: str, retry_func: callable, client_method: str) -> None:
    """Test handling of general request errors."""
    mock_client = Mock(
        spec=httpx.Client, **{client_method: Mock(side_effect=httpx.RequestError("Connection failed"))}
    )

    with pytest.raises(
        HttpRequestError,
        match=rf"{method_name} request to {TEST_URL} failed after 1 attempts: Connection failed",
    ):
        retry_func(TEST_URL, client=mock_client, max_retries=0)

    mock_sleep.assert_not_called()


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_request_error_with_retries(
    mock_sleep: Mock, method_name: str, retry_func: callable, client_method: str
) -> None:
    """Test handling of general request errors with retries."""
    mock_client = Mock(
        spec=httpx.Client, **{client_method: Mock(side_effect=httpx.RequestError("Connection failed"))}
    )

    with pytest.raises(HttpRequestError, match=r"failed after 3 attempts"):
        retry_func(TEST_URL, client=mock_client, max_retries=2)

    assert mock_sleep.call_args_list == [call(0.3), call(0.6)]


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_negative_max_retries(method_name: str, retry_func: callable, client_method: str) -> None:
    """Test that negative max_retries raises ValueError."""
    with pytest.raises(ValueError, match=r"max_retries must be >= 0"):
        retry_func(TEST_URL, max_retries=-1)


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_negative_backoff_factor(method_name: str, retry_func: callable, client_method: str) -> None:
    """Test that negative backoff_factor raises ValueError."""
    with pytest.raises(ValueError, match=r"backoff_factor must be >= 0"):
        retry_func(TEST_URL, backoff_factor=-1.0)


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_zero_max_retries(mock_sleep: Mock, method_name: str, retry_func: callable, client_method: str) -> None:
    """Test with zero retries - should only try once."""
    mock_client = Mock(
        spec=httpx.Client, **{client_method: Mock(return_value=Mock(spec=httpx.Response, status_code=503))}
    )

    with pytest.raises(
        HttpRequestError,
        match=rf"{method_name} request to {TEST_URL} failed with status 503 after 1 attempts",
    ):
        retry_func(TEST_URL, client=mock_client, max_retries=0)

    mock_sleep.assert_not_called()


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_custom_status_forcelist(
    mock_response: httpx.Response,
    mock_sleep: Mock,
    method_name: str,
    retry_func: callable,
    client_method: str,
) -> None:
    """Test custom status codes for retry."""
    mock_response_fail = Mock(spec=httpx.Response, status_code=404)
    mock_client = create_mock_client(mock_response, client_method)
    getattr(mock_client, client_method).side_effect = [mock_response_fail, mock_response]

    response = retry_func(TEST_URL, client=mock_client, status_forcelist=(404,))

    assert response.status_code == 200
    mock_sleep.assert_called_once_with(0.3)


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
@pytest.mark.parametrize("status_code", RETRY_STATUS_CODES)
def test_default_retry_status_codes(
    mock_response: httpx.Response,
    mock_sleep: Mock,
    method_name: str,
    retry_func: callable,
    client_method: str,
    status_code: int,
) -> None:
    """Test all default retry status codes."""
    mock_response_fail = Mock(spec=httpx.Response, status_code=status_code)
    mock_client = create_mock_client(mock_response, client_method)
    getattr(mock_client, client_method).side_effect = [mock_response_fail, mock_response]

    response = retry_func(TEST_URL, client=mock_client)

    assert response.status_code == 200
    mock_sleep.assert_called_once_with(0.3)


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_client_close_when_owns_client(method_name: str, retry_func: callable, client_method: str) -> None:
    """Test that client is closed when created internally."""
    mock_client = Mock(spec=httpx.Client, **{client_method: Mock(return_value=Mock(spec=httpx.Response, status_code=200))})
    with patch("httpx.Client", return_value=mock_client):
        retry_func(TEST_URL)
    mock_client.close.assert_called_once()


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_client_not_closed_when_provided(
    mock_response: httpx.Response, method_name: str, retry_func: callable, client_method: str
) -> None:
    """Test that external client is not closed."""
    mock_client = create_mock_client(mock_response, client_method)
    retry_func(TEST_URL, client=mock_client)
    mock_client.close.assert_not_called()


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_custom_timeout(
    mock_response: httpx.Response,
    mock_sleep: Mock,
    method_name: str,
    retry_func: callable,
    client_method: str,
) -> None:
    """Test custom timeout parameter."""
    mock_client = create_mock_client(mock_response, client_method)
    with patch("httpx.Client") as mock_client_class:
        mock_client_class.return_value = mock_client
        retry_func(TEST_URL, timeout=30.0)

    mock_client_class.assert_called_once_with(timeout=30.0)
    mock_sleep.assert_not_called()


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_all_retries_with_429(
    mock_sleep: Mock, method_name: str, retry_func: callable, client_method: str
) -> None:
    """Test retry behavior with 429 Too Many Requests."""
    mock_response = Mock(spec=httpx.Response, status_code=429)
    mock_client = Mock(spec=httpx.Client, **{client_method: Mock(return_value=mock_response)})

    with pytest.raises(HttpRequestError) as exc_info:
        retry_func(TEST_URL, client=mock_client, max_retries=1)

    assert exc_info.value.status_code == 429
    assert "failed with status 429 after 2 attempts" in str(exc_info.value)
    assert mock_sleep.call_args_list == [call(0.3)]


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_with_httpx_timeout_object(
    mock_response: httpx.Response,
    mock_sleep: Mock,
    method_name: str,
    retry_func: callable,
    client_method: str,
) -> None:
    """Test request with httpx.Timeout object."""
    timeout_config = httpx.Timeout(10.0, connect=5.0)

    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()
        setattr(mock_client_instance, client_method, Mock(return_value=mock_response))
        mock_client_instance.close = Mock()
        mock_client_class.return_value = mock_client_instance

        retry_func(TEST_URL, timeout=timeout_config)

        mock_client_class.assert_called_once_with(timeout=timeout_config)
        mock_sleep.assert_not_called()


@pytest.mark.parametrize("method_name,retry_func,client_method", HTTP_METHODS)
def test_kwargs_passed_to_client_method(
    mock_response: httpx.Response,
    mock_sleep: Mock,
    method_name: str,
    retry_func: callable,
    client_method: str,
) -> None:
    """Test that arbitrary kwargs are passed to client method."""
    mock_client = create_mock_client(mock_response, client_method)

    retry_func(
        TEST_URL,
        client=mock_client,
        headers={"Authorization": "Bearer token"},
        params={"key": "value"},
    )

    getattr(mock_client, client_method).assert_called_once_with(
        url=TEST_URL,
        headers={"Authorization": "Bearer token"},
        params={"key": "value"},
    )
    mock_sleep.assert_not_called()
