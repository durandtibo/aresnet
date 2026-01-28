from __future__ import annotations

import logging
import sys

import httpx

import aresnet

logger: logging.Logger = logging.getLogger(__name__)

# Use httpbin.org for real HTTP testing
HTTPBIN_URL = "https://httpbin.org"


def check_get_with_automatic_retry() -> None:
    logger.info("Checking get_with_automatic_retry...")
    with httpx.Client() as client:
        response = aresnet.get_with_automatic_retry(url=f"{HTTPBIN_URL}/get", client=client)
    assert response.status_code == 200


def check_post_with_automatic_retry() -> None:
    logger.info("Checking post_with_automatic_retry...")
    with httpx.Client() as client:
        response = aresnet.post_with_automatic_retry(url=f"{HTTPBIN_URL}/post", client=client)
    assert response.status_code == 200


def main() -> None:
    r"""Run all package checks to validate installation and
    functionality."""
    try:
        check_get_with_automatic_retry()
        check_post_with_automatic_retry()

        logger.info("✅ All package checks passed successfully!")
    except Exception:
        logger.exception("❌ Package check failed")
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
