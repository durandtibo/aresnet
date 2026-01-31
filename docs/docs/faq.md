# Frequently Asked Questions (FAQ)

This page answers common questions about using `aresilient`.

## General Questions

### What is aresilient?

`aresilient` is a Python library that provides resilient HTTP request functionality with automatic retry logic and exponential backoff. It's built on top of the modern [httpx](https://www.python-httpx.org/) library and simplifies handling transient failures in HTTP communications.

### Why use aresilient instead of plain httpx or requests?

`aresilient` adds automatic retry logic with exponential backoff on top of httpx, making your applications more resilient to transient failures like:

- Rate limiting (429 Too Many Requests)
- Temporary server errors (500, 502, 503, 504)
- Network timeouts
- Connection issues

Instead of manually implementing retry logic in every request, `aresilient` provides this functionality out of the box with sensible defaults.

### Is aresilient production-ready?

`aresilient` is currently in alpha development (version 0.0.1a0). While it's well-tested and functional, the API is not yet stable and may change before the 1.0.0 release. Use it in production with caution and be prepared for potential breaking changes in future versions.

## Installation Questions

### What Python versions are supported?

`aresilient` supports Python 3.10 and higher (3.10, 3.11, 3.12, 3.13, 3.14).

### How do I install aresilient?

Install using `uv` (recommended):
```bash
uv pip install aresilient
```

Or using `pip`:
```bash
pip install aresilient
```

See the [Get Started](get_started.md) guide for more installation options.

### What are the dependencies?

The only runtime dependency is `httpx` (version >= 0.28, < 1.0). All other dependencies are for development and testing.

## Usage Questions

### When should I use sync vs async functions?

**Use synchronous functions** when:
- Your application is not using asyncio
- You're making single, occasional requests
- You're writing simple scripts or command-line tools

**Use async functions** when:
- Your application already uses asyncio
- You need to make multiple concurrent requests
- You're building a web application (e.g., FastAPI, Sanic)
- Performance and scalability are critical

### What HTTP status codes trigger retries by default?

By default, `aresilient` retries on these status codes:
- **429**: Too Many Requests (rate limiting)
- **500**: Internal Server Error
- **502**: Bad Gateway
- **503**: Service Unavailable
- **504**: Gateway Timeout

You can customize this using the `status_forcelist` parameter.

### How does exponential backoff work?

The wait time between retries is calculated as:
```
wait_time = backoff_factor * (2 ** attempt)
```

With the default `backoff_factor=0.3`:
- 1st retry: 0.3 seconds
- 2nd retry: 0.6 seconds
- 3rd retry: 1.2 seconds

See the [User Guide](user_guide.md#understanding-exponential-backoff) for more details.

### What is jitter and when should I use it?

Jitter adds random variation to retry delays to prevent multiple clients from retrying simultaneously (the "thundering herd" problem). 

Enable jitter by setting `jitter_factor` (e.g., 0.1 for 10% jitter):

```python
response = get_with_automatic_retry(
    "https://api.example.com/data",
    jitter_factor=0.1  # Add 10% random jitter
)
```

**Use jitter when**:
- You have multiple clients accessing the same API
- You're dealing with rate-limited endpoints
- You want to avoid synchronized retry storms

### How does Retry-After header support work?

When a server returns a `Retry-After` header (commonly with 429 or 503 status codes), `aresilient` automatically uses the server's suggested wait time instead of exponential backoff.

The header can be in two formats:
- Integer seconds: `Retry-After: 120`
- HTTP-date: `Retry-After: Wed, 21 Oct 2015 07:28:00 GMT`

This is handled automatically - you don't need to configure anything.

### How do I disable retries?

Set `max_retries=0`:

```python
response = get_with_automatic_retry(
    "https://api.example.com/data",
    max_retries=0  # No retries
)
```

### Can I use custom headers with aresilient?

Yes, you can pass custom headers in two ways:

1. **Using a custom client**:
   ```python
   import httpx
   from aresilient import get_with_automatic_retry
   
   with httpx.Client(headers={"Authorization": "Bearer token"}) as client:
       response = get_with_automatic_retry(
           "https://api.example.com/data",
           client=client
       )
   ```

2. **Passing headers as kwargs**:
   ```python
   response = get_with_automatic_retry(
       "https://api.example.com/data",
       headers={"Authorization": "Bearer token"}
   )
   ```

### How do I handle authentication?

For simple authentication, pass headers:

```python
response = get_with_automatic_retry(
    "https://api.example.com/data",
    headers={"Authorization": "Bearer your-token"}
)
```

For more complex authentication (e.g., OAuth), create a custom httpx client:

```python
import httpx
from aresilient import get_with_automatic_retry

# Custom auth handler
auth = httpx.DigestAuth("username", "password")

with httpx.Client(auth=auth) as client:
    response = get_with_automatic_retry(
        "https://api.example.com/data",
        client=client
    )
```

### Can I upload files using aresilient?

Yes, use `post_with_automatic_retry` with the `files` parameter:

```python
from aresilient import post_with_automatic_retry

with open("document.pdf", "rb") as f:
    response = post_with_automatic_retry(
        "https://api.example.com/upload",
        files={"file": f}
    )
```

### How do I make requests with query parameters?

Pass query parameters using the `params` argument:

```python
from aresilient import get_with_automatic_retry

response = get_with_automatic_retry(
    "https://api.example.com/search",
    params={"q": "python", "page": 1, "limit": 10}
)
```

### What timeout should I use?

Choose a timeout based on your expected response time:

- **Quick endpoints** (health checks, simple queries): 5-10 seconds
- **Normal API calls**: 10-30 seconds (default is 10)
- **Large data transfers**: 60-120 seconds
- **Long-running operations**: Consider using async or a different approach

Example:
```python
# Health check with short timeout
response = get_with_automatic_retry(
    "https://api.example.com/health",
    timeout=5.0
)

# Large data download with long timeout
response = get_with_automatic_retry(
    "https://api.example.com/large-file",
    timeout=120.0
)
```

## Error Handling Questions

### What exceptions can aresilient raise?

`aresilient` can raise:

1. **`HttpRequestError`**: When an HTTP request fails after all retries
   - Includes method, URL, status code, and response object
2. **`ValueError`**: When invalid parameters are provided (e.g., negative timeouts)

### How do I access the response body when a request fails?

Use the `response` attribute of `HttpRequestError`:

```python
from aresilient import get_with_automatic_retry, HttpRequestError

try:
    response = get_with_automatic_retry("https://api.example.com/data")
except HttpRequestError as e:
    if e.response:
        print(f"Response body: {e.response.text}")
        print(f"Response headers: {e.response.headers}")
```

### How do I distinguish between different types of failures?

Check the `status_code` attribute:

```python
try:
    response = get_with_automatic_retry("https://api.example.com/data")
except HttpRequestError as e:
    if e.status_code is None:
        print("Network error or timeout")
    elif e.status_code == 404:
        print("Resource not found")
    elif e.status_code >= 500:
        print("Server error")
```

## Performance Questions

### How can I improve performance when making many requests?

1. **Use async functions** for concurrent requests:
   ```python
   import asyncio
   from aresilient import get_with_automatic_retry_async
   
   async def fetch_all(urls):
       tasks = [get_with_automatic_retry_async(url) for url in urls]
       return await asyncio.gather(*tasks)
   ```

2. **Reuse httpx clients** to benefit from connection pooling:
   ```python
   import httpx
   from aresilient import get_with_automatic_retry
   
   with httpx.Client() as client:
       for url in urls:
           response = get_with_automatic_retry(url, client=client)
   ```

### Does aresilient support connection pooling?

Yes, when you reuse an httpx client, it automatically uses connection pooling. This is handled by httpx itself.

### How do I control the number of concurrent requests?

Use `asyncio.Semaphore` to limit concurrency:

```python
import asyncio
from aresilient import get_with_automatic_retry_async

async def fetch_with_limit(url, semaphore):
    async with semaphore:
        return await get_with_automatic_retry_async(url)

async def fetch_all(urls, max_concurrent=10):
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = [fetch_with_limit(url, semaphore) for url in urls]
    return await asyncio.gather(*tasks)
```

## Troubleshooting

### My requests are taking too long. What should I do?

1. Check your timeout settings - reduce if needed
2. Reduce `max_retries` for faster failures
3. Check if you're hitting rate limits (enable debug logging)
4. Consider if the server is actually slow

### How do I enable debug logging to see what's happening?

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Now all retry attempts will be logged
from aresilient import get_with_automatic_retry
response = get_with_automatic_retry("https://api.example.com/data")
```

### I'm getting rate limited. How can I handle this better?

1. **Increase backoff factor** for longer waits:
   ```python
   response = get_with_automatic_retry(
       "https://api.example.com/data",
       backoff_factor=2.0  # Longer waits
   )
   ```

2. **Enable jitter** to avoid synchronized retries:
   ```python
   response = get_with_automatic_retry(
       "https://api.example.com/data",
       jitter_factor=0.1
   )
   ```

3. **The server's `Retry-After` header will be respected automatically** if present

### SSL/TLS certificate verification is failing. What should I do?

For testing only, you can disable SSL verification (not recommended for production):

```python
import httpx
from aresilient import get_with_automatic_retry

with httpx.Client(verify=False) as client:
    response = get_with_automatic_retry(
        "https://api.example.com/data",
        client=client
    )
```

For production, fix the certificate issue or provide a custom CA bundle:

```python
import httpx
from aresilient import get_with_automatic_retry

with httpx.Client(verify="/path/to/ca-bundle.crt") as client:
    response = get_with_automatic_retry(
        "https://api.example.com/data",
        client=client
    )
```

## Contributing Questions

### How can I contribute to aresilient?

See the [Contributing Guide](contributing.md) for detailed instructions on:
- Setting up your development environment
- Running tests
- Code style guidelines
- Pull request process

### How do I report a bug?

Open an issue on [GitHub](https://github.com/durandtibo/aresilient/issues) with:
- A clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Your environment (Python version, OS, library version)

### How do I request a new feature?

Open an issue on [GitHub](https://github.com/durandtibo/aresilient/issues) describing:
- The use case for the feature
- Your proposed solution
- Any alternatives you've considered

## Additional Resources

- [User Guide](user_guide.md) - Comprehensive usage guide
- [API Reference](refs/index.md) - Detailed API documentation
- [Get Started](get_started.md) - Installation and setup
- [GitHub Repository](https://github.com/durandtibo/aresilient) - Source code and issues
