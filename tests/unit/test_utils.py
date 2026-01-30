from __future__ import annotations

import math

import pytest

from aresnet.utils import parse_retry_after, validate_retry_params


def test_validate_retry_params_accepts_valid_values() -> None:
    """Test that validate_retry_params accepts valid parameters."""
    validate_retry_params(3, 0.3)
    validate_retry_params(0, 0.0)
    validate_retry_params(10, 1.5)


def test_validate_retry_params_rejects_negative_max_retries() -> None:
    """Test that validate_retry_params rejects negative max_retries."""
    with pytest.raises(ValueError, match=r"max_retries must be >= 0, got -1"):
        validate_retry_params(-1, 0.3)


def test_validate_retry_params_rejects_negative_backoff_factor() -> None:
    """Test that validate_retry_params rejects negative
    backoff_factor."""
    with pytest.raises(ValueError, match=r"backoff_factor must be >= 0, got -0.5"):
        validate_retry_params(3, -0.5)


def test_validate_retry_params_rejects_both_negative() -> None:
    """Test that validate_retry_params rejects both negative values."""
    with pytest.raises(ValueError, match=r"max_retries must be >= 0"):
        validate_retry_params(-1, -0.5)


def test_validate_retry_params_large_values() -> None:
    """Test that validate_retry_params accepts very large values."""
    validate_retry_params(1000000, 100.0)
    validate_retry_params(999, 999.999)


def test_validate_retry_params_zero_boundary() -> None:
    """Test that validate_retry_params accepts zero as boundary case."""
    validate_retry_params(0, 0.0)


def test_validate_retry_params_rejects_negative_zero_boundary() -> None:
    """Test that validate_retry_params rejects values just below zero."""
    with pytest.raises(ValueError, match=r"max_retries must be >= 0"):
        validate_retry_params(-1, 0.0)
    with pytest.raises(ValueError, match=r"backoff_factor must be >= 0"):
        validate_retry_params(0, -0.0001)


def test_validate_retry_params_infinity_max_retries() -> None:
    """Test that validate_retry_params handles infinity for max_retries."""
    # Python will accept infinity as a valid int comparison
    validate_retry_params(int(1e100), 0.5)


def test_validate_retry_params_infinity_backoff_factor() -> None:
    """Test that validate_retry_params handles infinity for backoff_factor."""
    validate_retry_params(3, math.inf)


##################################################
#     Tests for parse_retry_after               #
##################################################


def test_parse_retry_after_float_string() -> None:
    """Test parsing Retry-After header with float string."""
    assert parse_retry_after("120.5") == 120.5
    assert parse_retry_after("0.5") == 0.5
    assert parse_retry_after("3600.123") == 3600.123


def test_parse_retry_after_empty_string() -> None:
    """Test parsing empty Retry-After header."""
    assert parse_retry_after("") is None


def test_parse_retry_after_whitespace() -> None:
    """Test parsing Retry-After header with whitespace."""
    assert parse_retry_after("   ") is None
    assert parse_retry_after("\t\n") is None


def test_parse_retry_after_scientific_notation() -> None:
    """Test parsing Retry-After header with scientific notation."""
    assert parse_retry_after("1e2") == 100.0
    assert parse_retry_after("1.5e3") == 1500.0


def test_parse_retry_after_very_large_number() -> None:
    """Test parsing Retry-After header with very large number."""
    assert parse_retry_after("999999999") == 999999999.0


def test_parse_retry_after_negative_number() -> None:
    """Test parsing Retry-After header with negative number."""
    # Negative seconds are technically valid input (though unusual)
    assert parse_retry_after("-10") == -10.0


def test_parse_retry_after_past_date() -> None:
    """Test parsing Retry-After header with date in the past."""
    from datetime import datetime, timezone
    from unittest.mock import patch

    # Mock datetime.now to return a fixed time
    fixed_now = datetime(2015, 10, 21, 7, 28, 0, tzinfo=timezone.utc)

    with patch("aresnet.utils.datetime") as mock_datetime:
        # Configure the mock to return our fixed time for now()
        mock_datetime.now.return_value = fixed_now
        # But still allow datetime to be used for other operations
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        # Test with a date 60 seconds in the past
        result = parse_retry_after("Wed, 21 Oct 2015 07:27:00 GMT")

        # Should return 0.0 (max of 0.0 and negative delta)
        assert result == 0.0


def test_parse_retry_after_malformed_http_date() -> None:
    """Test parsing malformed HTTP-date returns None."""
    assert parse_retry_after("Not a valid date") is None
    assert parse_retry_after("2023-13-45 25:99:99") is None


def test_parse_retry_after_zero() -> None:
    """Test parsing Retry-After header with zero."""
    assert parse_retry_after("0") == 0.0
    assert parse_retry_after("0.0") == 0.0
