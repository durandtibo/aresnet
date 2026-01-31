# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial implementation of resilient HTTP request functionality
- Automatic retry logic with exponential backoff
- Support for all common HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Full async support for high-performance applications
- Retry-After header support (both integer seconds and HTTP-date formats)
- Optional jitter to prevent thundering herd problems
- Comprehensive error handling with `HttpRequestError`
- Type-safe implementation with full type hints
- Extensive test coverage

### Documentation
- User guide with comprehensive examples
- API reference with detailed docstrings
- Get started guide with installation instructions
- Contributing guide for developers

## Version History

### [0.0.1a0] - Development

Initial alpha release for testing and development.

**Note**: While `aresilient` is in development stage, no API is guaranteed to be stable from one release to the next. It is very likely that the API will change multiple times before a stable 1.0.0 release.

[Unreleased]: https://github.com/durandtibo/aresilient/compare/main...HEAD
[0.0.1a0]: https://github.com/durandtibo/aresilient/releases/tag/v0.0.1a0
