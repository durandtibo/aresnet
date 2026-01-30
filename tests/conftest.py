from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def mock_sleep() -> Generator[Mock, None, None]:
    """Patch time.sleep to make tests run faster."""
    with patch("time.sleep", return_value=None) as mock:
        yield mock


@pytest.fixture
def mock_asleep() -> Generator[Mock, None, None]:
    """Patch asyncio.sleep to make tests run faster."""
    with patch("asyncio.sleep", return_value=None) as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_random() -> Generator[Mock, None, None]:
    """Patch random.uniform to make jitter deterministic in tests.
    
    This fixture is auto-used to ensure all tests have deterministic
    behavior when jitter is applied to retry backoff. Patches both
    sync and async module versions.
    """
    with patch("aresnet.request.random.uniform", return_value=0.0) as mock1, \
         patch("aresnet.request_async.random.uniform", return_value=0.0) as mock2:
        yield mock1
