r"""Unit tests for package initialization and metadata."""

from __future__ import annotations

from unittest.mock import patch

import pytest

import aresnet


def test_package_version_is_string() -> None:
    """Test that __version__ is a string."""
    assert isinstance(aresnet.__version__, str)


def test_package_version_not_empty() -> None:
    """Test that __version__ is not empty."""
    assert len(aresnet.__version__) > 0


def test_package_version_format() -> None:
    """Test that __version__ follows semantic versioning."""
    # Should have at least one dot (e.g., "0.0.0" or "0.0.1a0")
    assert "." in aresnet.__version__


def test_package_version_fallback_on_not_installed() -> None:
    """Test that __version__ falls back to '0.0.0' when package is not
    installed."""
    from importlib.metadata import PackageNotFoundError

    with patch("importlib.metadata.version", side_effect=PackageNotFoundError):
        # We need to reload the module to trigger the fallback
        import importlib

        importlib.reload(aresnet)
        # After reload with mock, version should be the fallback
        assert aresnet.__version__ == "0.0.0"

        # Reload again to restore normal state
        importlib.reload(aresnet)


def test_all_exports_defined() -> None:
    """Test that all items in __all__ are defined in the module."""
    for name in aresnet.__all__:
        assert hasattr(aresnet, name), f"{name} is in __all__ but not defined in module"


def test_all_exports_importable() -> None:
    """Test that all items in __all__ can be imported."""
    # Try to access each export to ensure it's importable
    exports = {
        "DEFAULT_BACKOFF_FACTOR": aresnet.DEFAULT_BACKOFF_FACTOR,
        "DEFAULT_MAX_RETRIES": aresnet.DEFAULT_MAX_RETRIES,
        "DEFAULT_TIMEOUT": aresnet.DEFAULT_TIMEOUT,
        "RETRY_STATUS_CODES": aresnet.RETRY_STATUS_CODES,
        "HttpRequestError": aresnet.HttpRequestError,
        "__version__": aresnet.__version__,
        "delete_with_automatic_retry": aresnet.delete_with_automatic_retry,
        "delete_with_automatic_retry_async": aresnet.delete_with_automatic_retry_async,
        "get_with_automatic_retry": aresnet.get_with_automatic_retry,
        "get_with_automatic_retry_async": aresnet.get_with_automatic_retry_async,
        "patch_with_automatic_retry": aresnet.patch_with_automatic_retry,
        "patch_with_automatic_retry_async": aresnet.patch_with_automatic_retry_async,
        "post_with_automatic_retry": aresnet.post_with_automatic_retry,
        "post_with_automatic_retry_async": aresnet.post_with_automatic_retry_async,
        "put_with_automatic_retry": aresnet.put_with_automatic_retry,
        "put_with_automatic_retry_async": aresnet.put_with_automatic_retry_async,
        "request_with_automatic_retry": aresnet.request_with_automatic_retry,
        "request_with_automatic_retry_async": aresnet.request_with_automatic_retry_async,
    }

    for name in aresnet.__all__:
        assert name in exports, f"{name} in __all__ but not tested"
        assert exports[name] is not None


def test_all_exports_count() -> None:
    """Test that __all__ has the expected number of exports."""
    # 4 config constants + 1 exception + 1 version + 10 HTTP methods (sync+async) = 18
    assert len(aresnet.__all__) == 18


def test_constants_are_immutable_types() -> None:
    """Test that configuration constants are immutable types."""
    # These should be int, float, or tuple (immutable)
    assert isinstance(aresnet.DEFAULT_MAX_RETRIES, int)
    assert isinstance(aresnet.DEFAULT_BACKOFF_FACTOR, float)
    assert isinstance(aresnet.DEFAULT_TIMEOUT, float)
    assert isinstance(aresnet.RETRY_STATUS_CODES, tuple)


def test_exception_class_is_callable() -> None:
    """Test that HttpRequestError is a callable exception class."""
    assert callable(aresnet.HttpRequestError)
    # Test that it can be instantiated
    exc = aresnet.HttpRequestError(method="GET", url="http://test.com", message="test")
    assert isinstance(exc, Exception)


def test_all_request_functions_are_callable() -> None:
    """Test that all request functions are callable."""
    request_funcs = [
        aresnet.delete_with_automatic_retry,
        aresnet.delete_with_automatic_retry_async,
        aresnet.get_with_automatic_retry,
        aresnet.get_with_automatic_retry_async,
        aresnet.patch_with_automatic_retry,
        aresnet.patch_with_automatic_retry_async,
        aresnet.post_with_automatic_retry,
        aresnet.post_with_automatic_retry_async,
        aresnet.put_with_automatic_retry,
        aresnet.put_with_automatic_retry_async,
        aresnet.request_with_automatic_retry,
        aresnet.request_with_automatic_retry_async,
    ]

    for func in request_funcs:
        assert callable(func), f"{func.__name__} is not callable"
