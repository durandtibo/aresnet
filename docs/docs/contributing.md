# Contributing to aresilient

Thank you for your interest in contributing to `aresilient`! This guide will help you get started with contributing to the project.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [`uv`](https://docs.astral.sh/uv/) for dependency management
- Git for version control

### Setting Up Your Development Environment

1. **Fork and clone the repository**:

   ```bash
   git clone https://github.com/YOUR-USERNAME/aresilient.git
   cd aresilient
   ```

2. **Create a virtual environment and install dependencies**:

   Using `uv` (recommended):
   ```bash
   make setup-venv
   ```

   Or manually:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev,docs]"
   ```

3. **Install pre-commit hooks**:

   ```bash
   pre-commit install
   ```

## Development Workflow

### Running Tests

Run the full test suite:

```bash
make unit-test-cov
```

Run specific test files:

```bash
pytest tests/unit/test_get.py -v
```

Run tests with coverage report:

```bash
make unit-test-cov
```

### Code Style and Linting

The project uses several tools to maintain code quality:

- **ruff**: Fast Python linter and formatter
- **black**: Code formatter
- **mypy**: Static type checker
- **pre-commit**: Automated checks before commits

Format your code:

```bash
make format
```

Run linters:

```bash
make lint
```

Check types:

```bash
make type-check
```

### Building Documentation

Build the documentation locally:

```bash
make docs
```

Serve documentation locally (with live reload):

```bash
make docs-serve
```

The documentation will be available at `http://127.0.0.1:8000`.

## Making Changes

### Branching Strategy

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the project's coding standards

3. Write or update tests to cover your changes

4. Update documentation if needed

5. Commit your changes with clear, descriptive messages

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names that explain what is being tested
- Aim for high test coverage
- Test both success and failure scenarios
- Include edge cases

Example test structure:

```python
def test_get_with_automatic_retry_success():
    """Test successful GET request with automatic retry."""
    # Arrange
    url = "https://api.example.com/data"
    
    # Act
    response = get_with_automatic_retry(url)
    
    # Assert
    assert response.status_code == 200
```

### Documentation Guidelines

When updating documentation:

1. **Use clear, concise language**
2. **Include code examples** for new features
3. **Update all relevant sections**:
   - User Guide (`docs/docs/user_guide.md`)
   - API Reference (docstrings in source code)
   - README.md (if adding major features)
4. **Follow Google-style docstrings** for Python code
5. **Test code examples** to ensure they work

### Docstring Format

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int = 0) -> bool:
    """Short description of the function.

    Longer description if needed, explaining the purpose and behavior
    in more detail.

    Args:
        param1: Description of param1.
        param2: Description of param2. Defaults to 0.

    Returns:
        Description of return value.

    Raises:
        ValueError: Description of when this error is raised.

    Example:
        ```pycon
        >>> example_function("test", 42)
        True

        ```
    """
    pass
```

## Pull Request Process

1. **Update your branch** with the latest changes from main:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Ensure all tests pass** and code is properly formatted:
   ```bash
   make lint
   make type-check
   make unit-test-cov
   ```

3. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request** on GitHub:
   - Use a clear, descriptive title
   - Describe what changes you made and why
   - Reference any related issues
   - Ensure all CI checks pass

5. **Address review feedback** if requested

## Code Review Guidelines

When reviewing code:

- Be respectful and constructive
- Focus on code quality, not personal preferences
- Suggest improvements with explanations
- Approve when the code meets project standards

## Reporting Issues

When reporting bugs or requesting features:

1. **Search existing issues** first to avoid duplicates
2. **Use issue templates** if available
3. **Provide detailed information**:
   - For bugs: steps to reproduce, expected vs actual behavior, error messages
   - For features: use case, proposed solution, alternatives considered
4. **Include your environment**: Python version, OS, library version

## Code of Conduct

Be respectful, inclusive, and professional in all interactions. We want to maintain a welcoming community for all contributors.

## Getting Help

- Open an issue for bugs or feature requests
- Check the [User Guide](user_guide.md) for usage questions
- Review the [API Reference](refs/index.md) for detailed documentation

## License

By contributing to aresilient, you agree that your contributions will be licensed under the BSD-3-Clause License.
