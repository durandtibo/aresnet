# Best Practices and Patterns

This guide provides recommended patterns and best practices for using `aresilient` effectively in your applications.

## Retry Configuration Best Practices

### Choose Appropriate Retry Settings Based on Use Case

Different use cases require different retry strategies. Here are some recommended configurations:

#### User-Facing APIs (Fast Failure)

For user-facing operations where users are waiting for a response, fail fast to provide quick feedback:

```python
from aresilient import get_with_automatic_retry

response = get_with_automatic_retry(
    "https://api.example.com/user-profile",
    max_retries=1,  # Only 1 retry
    backoff_factor=0.2,  # Short wait
    timeout=5.0,  # Quick timeout
)
```

#### Background Jobs (More Resilient)

For background processing where reliability is more important than speed:

```python
from aresilient import post_with_automatic_retry

response = post_with_automatic_retry(
    "https://api.example.com/batch-process",
    max_retries=5,  # More retries
    backoff_factor=1.0,  # Longer waits
    jitter_factor=0.1,  # Add jitter
    timeout=60.0,  # Longer timeout
    json={"data": batch_data},
)
```

#### Rate-Limited APIs

When working with APIs that have strict rate limits:

```python
from aresilient import get_with_automatic_retry

response = get_with_automatic_retry(
    "https://api.example.com/rate-limited",
    max_retries=5,
    backoff_factor=2.0,  # Aggressive backoff
    jitter_factor=0.2,  # 20% jitter to spread load
    status_forcelist=(429,),  # Only retry on rate limit
)
```

#### Critical Operations (Maximum Resilience)

For critical operations where you want maximum retry attempts:

```python
from aresilient import post_with_automatic_retry

response = post_with_automatic_retry(
    "https://api.example.com/critical-transaction",
    max_retries=10,  # Many retries
    backoff_factor=0.5,
    jitter_factor=0.1,
    timeout=30.0,
    json={"transaction": data},
)
```

### Always Enable Jitter in Production

Jitter prevents the "thundering herd" problem where multiple clients retry simultaneously:

```python
# Good: With jitter
response = get_with_automatic_retry(
    "https://api.example.com/data",
    jitter_factor=0.1  # Add 10% jitter
)

# Bad: Without jitter (can cause synchronized retries)
response = get_with_automatic_retry(
    "https://api.example.com/data",
    jitter_factor=0.0  # No jitter
)
```

**Recommended jitter_factor values**:
- `0.1` (10%): Good default for most use cases
- `0.2` (20%): For highly rate-limited APIs
- `0.05` (5%): For less critical endpoints

## Client Reuse Patterns

### Reuse Clients for Multiple Requests

Always reuse httpx clients when making multiple requests to benefit from connection pooling:

```python
import httpx
from aresilient import get_with_automatic_retry, post_with_automatic_retry

# Good: Reuse client
with httpx.Client(timeout=30.0) as client:
    users = get_with_automatic_retry(
        "https://api.example.com/users",
        client=client
    )
    
    for user in users.json():
        profile = get_with_automatic_retry(
            f"https://api.example.com/users/{user['id']}/profile",
            client=client
        )
        process_profile(profile.json())

# Bad: Creates new client for each request
for user_id in user_ids:
    profile = get_with_automatic_retry(
        f"https://api.example.com/users/{user_id}/profile"
    )
    # New connection for each request - slow!
```

### Configure Client Once with Common Settings

Set up a client with common configuration for all requests:

```python
import httpx
from aresilient import get_with_automatic_retry

# Configure client with common settings
client = httpx.Client(
    timeout=30.0,
    headers={
        "User-Agent": "MyApp/1.0",
        "Authorization": f"Bearer {api_token}",
    },
    follow_redirects=True,
)

try:
    # Use configured client for all requests
    response1 = get_with_automatic_retry(
        "https://api.example.com/endpoint1",
        client=client
    )
    
    response2 = get_with_automatic_retry(
        "https://api.example.com/endpoint2",
        client=client
    )
finally:
    client.close()
```

## Async Patterns

### Concurrent Requests with Semaphore

Limit the number of concurrent requests to avoid overwhelming the server or exhausting resources:

```python
import asyncio
import httpx
from aresilient import get_with_automatic_retry_async

async def fetch_with_limit(url: str, semaphore: asyncio.Semaphore, client: httpx.AsyncClient):
    """Fetch URL with concurrency limit."""
    async with semaphore:
        return await get_with_automatic_retry_async(url, client=client)

async def fetch_all(urls: list[str], max_concurrent: int = 10):
    """Fetch multiple URLs with limited concurrency."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [fetch_with_limit(url, semaphore, client) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle results and errors
    results = []
    for url, response in zip(urls, responses):
        if isinstance(response, Exception):
            print(f"Failed to fetch {url}: {response}")
        else:
            results.append(response.json())
    
    return results

# Usage
urls = [f"https://api.example.com/item/{i}" for i in range(100)]
results = asyncio.run(fetch_all(urls, max_concurrent=10))
```

### Async Context Manager Pattern

Use async context managers for proper resource cleanup:

```python
import asyncio
import httpx
from aresilient import get_with_automatic_retry_async

class APIClient:
    """API client with automatic retry."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"},
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def get_user(self, user_id: int):
        """Get user by ID."""
        url = f"{self.base_url}/users/{user_id}"
        response = await get_with_automatic_retry_async(url, client=self.client)
        return response.json()
    
    async def get_users(self):
        """Get all users."""
        url = f"{self.base_url}/users"
        response = await get_with_automatic_retry_async(url, client=self.client)
        return response.json()

# Usage
async def main():
    async with APIClient("https://api.example.com", "your-api-key") as client:
        users = await client.get_users()
        user_details = await asyncio.gather(
            *[client.get_user(user['id']) for user in users[:10]]
        )
        return user_details

asyncio.run(main())
```

### Batch Processing Pattern

Process items in batches with async:

```python
import asyncio
from typing import Any
import httpx
from aresilient import post_with_automatic_retry_async

async def process_batch(
    items: list[Any],
    batch_size: int = 100,
    max_concurrent: int = 5,
):
    """Process items in batches with limited concurrency."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_item(item):
            async with semaphore:
                return await post_with_automatic_retry_async(
                    "https://api.example.com/process",
                    client=client,
                    json=item,
                    max_retries=3,
                )
        
        # Process in batches
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[process_item(item) for item in batch],
                return_exceptions=True
            )
            results.extend(batch_results)
            
            # Optional: Add delay between batches
            if i + batch_size < len(items):
                await asyncio.sleep(1.0)
        
        return results

# Usage
items = [{"id": i, "data": f"item_{i}"} for i in range(1000)]
results = asyncio.run(process_batch(items, batch_size=100, max_concurrent=5))
```

## Error Handling Patterns

### Graceful Degradation

Handle errors gracefully and provide fallback behavior:

```python
import logging
from aresilient import get_with_automatic_retry, HttpRequestError

logger = logging.getLogger(__name__)

def get_cached_profile(user_id: int) -> dict | None:
    """Get user profile from cache (implementation depends on your cache system)."""
    # Placeholder - implement based on your caching strategy
    return None

def get_user_profile(user_id: int) -> dict:
    """Get user profile with fallback to cached data."""
    try:
        response = get_with_automatic_retry(
            f"https://api.example.com/users/{user_id}",
            max_retries=2,
            timeout=10.0,
        )
        return response.json()
    
    except HttpRequestError as e:
        # Log the error
        logger.warning(f"Failed to fetch user profile for {user_id}: {e}")
        
        # Return cached data or default
        cached = get_cached_profile(user_id)
        if cached:
            return cached
        
        # Return minimal default data
        return {
            "id": user_id,
            "name": "Unknown",
            "available": False,
        }
```

### Retry with Different Endpoints

Try multiple endpoints with fallback:

```python
import logging
from aresilient import get_with_automatic_retry, HttpRequestError

logger = logging.getLogger(__name__)

def fetch_data_with_fallback(resource_id: str) -> dict:
    """Fetch data from primary endpoint with fallback to secondary."""
    endpoints = [
        f"https://primary-api.example.com/data/{resource_id}",
        f"https://secondary-api.example.com/data/{resource_id}",
        f"https://tertiary-api.example.com/data/{resource_id}",
    ]
    
    last_error = None
    for endpoint in endpoints:
        try:
            response = get_with_automatic_retry(
                endpoint,
                max_retries=2,
                timeout=10.0,
            )
            return response.json()
        
        except HttpRequestError as e:
            logger.warning(f"Failed to fetch from {endpoint}: {e}")
            last_error = e
            continue
    
    # All endpoints failed
    raise RuntimeError(
        f"Failed to fetch data from all endpoints: {last_error}"
    ) from last_error
```

### Error Classification

Handle different error types appropriately:

```python
from aresilient import get_with_automatic_retry, HttpRequestError

def fetch_data(url: str) -> dict:
    """Fetch data with appropriate error handling."""
    try:
        response = get_with_automatic_retry(url, max_retries=3)
        return response.json()
    
    except HttpRequestError as e:
        if e.status_code is None:
            # Network error or timeout
            logger.error(f"Network error fetching {url}: {e}")
            raise RuntimeError("Service unavailable") from e
        
        elif e.status_code == 404:
            # Not found - don't retry, return None
            logger.info(f"Resource not found: {url}")
            return None
        
        elif e.status_code == 401 or e.status_code == 403:
            # Auth error - don't retry, raise immediately
            logger.error(f"Authentication failed for {url}")
            raise PermissionError("Access denied") from e
        
        elif e.status_code >= 500:
            # Server error - was already retried
            logger.error(f"Server error from {url}: {e}")
            raise RuntimeError("Server error") from e
        
        else:
            # Other client error
            logger.error(f"Client error from {url}: {e}")
            raise ValueError(f"Bad request: {e}") from e
```

## Testing Patterns

### Mocking HTTP Requests in Tests

Use `respx` or similar libraries to mock HTTP requests in tests:

```python
import pytest
import httpx
import respx
from aresilient import get_with_automatic_retry, HttpRequestError

@respx.mock
def test_successful_request():
    """Test successful request."""
    respx.get("https://api.example.com/data").mock(
        return_value=httpx.Response(200, json={"result": "success"})
    )
    
    response = get_with_automatic_retry("https://api.example.com/data")
    assert response.status_code == 200
    assert response.json() == {"result": "success"}

@respx.mock
def test_retry_on_server_error():
    """Test retry behavior on server errors."""
    # First two attempts fail, third succeeds
    respx.get("https://api.example.com/data").mock(
        side_effect=[
            httpx.Response(503, text="Service Unavailable"),
            httpx.Response(503, text="Service Unavailable"),
            httpx.Response(200, json={"result": "success"}),
        ]
    )
    
    response = get_with_automatic_retry(
        "https://api.example.com/data",
        max_retries=3,
        backoff_factor=0.1,  # Short backoff for tests
    )
    
    assert response.status_code == 200
    assert response.json() == {"result": "success"}

@respx.mock
def test_failure_after_retries():
    """Test that error is raised after all retries."""
    # All attempts fail
    respx.get("https://api.example.com/data").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    
    with pytest.raises(HttpRequestError) as exc_info:
        get_with_automatic_retry(
            "https://api.example.com/data",
            max_retries=2,
            backoff_factor=0.1,
        )
    
    assert exc_info.value.status_code == 500
```

## Configuration Management

### Environment-Based Configuration

Configure retry behavior based on environment:

```python
import os
from aresilient import get_with_automatic_retry

def get_retry_config():
    """Get retry configuration based on environment."""
    env = os.getenv("ENV", "production")
    
    if env == "development":
        return {
            "max_retries": 1,
            "backoff_factor": 0.1,
            "timeout": 5.0,
            "jitter_factor": 0.0,
        }
    elif env == "staging":
        return {
            "max_retries": 3,
            "backoff_factor": 0.5,
            "timeout": 15.0,
            "jitter_factor": 0.1,
        }
    else:  # production
        return {
            "max_retries": 5,
            "backoff_factor": 1.0,
            "timeout": 30.0,
            "jitter_factor": 0.1,
        }

# Usage
config = get_retry_config()
response = get_with_automatic_retry(
    "https://api.example.com/data",
    **config
)
```

### Configuration Class Pattern

Use a configuration class for better organization:

```python
from dataclasses import dataclass
from aresilient import get_with_automatic_retry

@dataclass
class RetryConfig:
    """Retry configuration."""
    max_retries: int = 3
    backoff_factor: float = 0.5
    timeout: float = 30.0
    jitter_factor: float = 0.1
    status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504)

# Define configurations for different use cases
FAST_CONFIG = RetryConfig(max_retries=1, backoff_factor=0.2, timeout=5.0)
STANDARD_CONFIG = RetryConfig(max_retries=3, backoff_factor=0.5, timeout=30.0)
RESILIENT_CONFIG = RetryConfig(max_retries=5, backoff_factor=1.0, timeout=60.0)

# Usage
def fetch_user_data(user_id: int, config: RetryConfig = STANDARD_CONFIG):
    """Fetch user data with configurable retry."""
    response = get_with_automatic_retry(
        f"https://api.example.com/users/{user_id}",
        max_retries=config.max_retries,
        backoff_factor=config.backoff_factor,
        timeout=config.timeout,
        jitter_factor=config.jitter_factor,
        status_forcelist=config.status_forcelist,
    )
    return response.json()

# Use different configs for different scenarios
user = fetch_user_data(123, config=FAST_CONFIG)
batch = fetch_user_data(456, config=RESILIENT_CONFIG)
```

## Monitoring and Logging

### Structured Logging

Use structured logging to track retry behavior:

```python
import logging
from aresilient import get_with_automatic_retry, HttpRequestError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_with_logging(url: str, operation: str):
    """Fetch with detailed logging."""
    logger.info(f"Starting {operation} for {url}")
    
    try:
        response = get_with_automatic_retry(url, max_retries=3)
        logger.info(
            f"Success: {operation} completed",
            extra={
                "url": url,
                "status_code": response.status_code,
                "operation": operation,
            }
        )
        return response.json()
    
    except HttpRequestError as e:
        logger.error(
            f"Failed: {operation} failed after retries",
            extra={
                "url": url,
                "status_code": e.status_code,
                "operation": operation,
                "error": str(e),
            }
        )
        raise
```

## Security Best Practices

### Never Log Sensitive Data

Avoid logging sensitive information like API keys, tokens, or user data:

```python
import logging
from aresilient import get_with_automatic_retry

logger = logging.getLogger(__name__)

# Bad: Logs sensitive headers
def bad_fetch(api_key: str):
    response = get_with_automatic_retry(
        "https://api.example.com/data",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    logger.info(f"Response: {response.headers}")  # May contain sensitive data
    return response

# Good: Sanitize logs
def good_fetch(api_key: str):
    response = get_with_automatic_retry(
        "https://api.example.com/data",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    logger.info(f"Request completed with status {response.status_code}")
    return response
```

### Use HTTPS

Always use HTTPS for sensitive data:

```python
# Good: HTTPS
response = get_with_automatic_retry("https://api.example.com/data")

# Bad: HTTP (unencrypted)
response = get_with_automatic_retry("http://api.example.com/data")
```

## Additional Resources

- [User Guide](user_guide.md) - Comprehensive usage guide
- [API Reference](refs/index.md) - Detailed API documentation
- [FAQ](faq.md) - Frequently asked questions
