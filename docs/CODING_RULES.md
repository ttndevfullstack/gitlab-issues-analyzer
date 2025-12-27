# Coding Rules and Standards

This document defines coding standards, conventions, and best practices for the GitLab Issues Analyzer project.

## Table of Contents

1. [General Principles](#general-principles)
2. [Code Style](#code-style)
3. [Naming Conventions](#naming-conventions)
4. [Code Organization](#code-organization)
5. [Error Handling](#error-handling)
6. [Logging](#logging)
7. [Documentation](#documentation)
8. [Security Rules](#security-rules)
9. [Performance Guidelines](#performance-guidelines)
10. [Testing Requirements](#testing-requirements)

## General Principles

### 1.1 Code Quality
- **Readability First**: Code should be self-documenting and easy to understand
- **Simplicity**: Prefer simple solutions over complex ones
- **DRY (Don't Repeat Yourself)**: Avoid code duplication
- **Single Responsibility**: Each function/class should have one clear purpose
- **Fail Fast**: Validate inputs early and fail with clear error messages

### 1.2 Python Version
- **Minimum Version**: Python 3.9+
- **Type Hints**: Use type hints for all function signatures
- **Modern Python**: Use modern Python features (f-strings, dataclasses, etc.)

### 1.3 Dependencies
- **Minimal Dependencies**: Only add dependencies when absolutely necessary
- **Version Pinning**: Pin major versions in `requirements.txt`
- **Security**: Regularly update dependencies for security patches

## Code Style

### 2.1 PEP 8 Compliance
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters (soft limit, 120 hard limit)
- Use blank lines to separate logical sections

### 2.2 Formatting Tools
- Use `black` for code formatting (if adopted)
- Use `flake8` or `pylint` for linting
- Use `mypy` for type checking (if adopted)

### 2.3 Code Example
```python
# Good: Clear, readable, type-hinted
def analyze_issue(issue_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Analyze a GitLab issue using AI.
    
    Args:
        issue_data: Dictionary containing issue information
        
    Returns:
        Dictionary with WWWH-TR analysis sections
        
    Raises:
        ValueError: If issue_data is invalid
        APIError: If AI API call fails
    """
    if not issue_data:
        raise ValueError("issue_data cannot be empty")
    
    # Implementation here
    return analysis_result

# Bad: Unclear, no type hints, no docstring
def analyze(d):
    if d:
        return process(d)
    return {}
```

## Naming Conventions

### 3.1 Files and Modules
- **Files**: `snake_case.py`
- **Modules**: `snake_case.py`
- **Examples**: `gitlab_client.py`, `email_sender.py`, `config.py`

### 3.2 Classes
- **Classes**: `PascalCase`
- **Examples**: `GitLabClient`, `EmailSender`, `ConfigManager`

### 3.3 Functions and Methods
- **Functions**: `snake_case()`
- **Methods**: `snake_case()`
- **Private Methods**: `_leading_underscore()` (single underscore)
- **Examples**: `get_issues()`, `send_email()`, `_validate_token()`

### 3.4 Variables
- **Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private Variables**: `_leading_underscore`
- **Examples**: `issue_id`, `MAX_RETRIES`, `_api_key`

### 3.5 Naming Guidelines
- Use descriptive names (avoid abbreviations unless widely known)
- Boolean variables should be questions: `is_valid`, `has_errors`
- Functions should be verbs: `fetch_issue()`, `validate_config()`
- Classes should be nouns: `IssueAnalyzer`, `EmailReporter`

## Code Organization

### 4.1 Import Organization
Order imports in this sequence:
1. Standard library imports
2. Third-party imports
3. Local application imports

Separate each group with a blank line.

```python
# Standard library
import json
import os
from typing import Dict, List, Optional

# Third-party
import requests
from flask import Flask, request

# Local
from src.gitlab_client import GitLabClient
from src.analyzer import IssueAnalyzer
from src.config import Config
```

### 4.2 Module Structure
Each module should follow this structure:
1. Module docstring
2. Imports
3. Constants
4. Classes
5. Functions
6. Main execution (if applicable)

```python
"""
Module for GitLab API integration.

This module provides a client for interacting with GitLab API v4.
"""

import requests
from typing import Dict, List, Optional

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Classes
class GitLabClient:
    """Client for GitLab API operations."""
    pass

# Functions
def validate_project_id(project_id: str) -> bool:
    """Validate GitLab project ID format."""
    pass
```

### 4.3 Function Length
- **Maximum**: 50 lines per function
- **Preferred**: 20-30 lines
- If a function exceeds 50 lines, consider breaking it into smaller functions

### 4.4 Class Design
- Keep classes focused on a single responsibility
- Use composition over inheritance when possible
- Prefer functions over classes for simple operations

## Error Handling

### 5.1 Exception Types
- Use built-in exceptions when appropriate (`ValueError`, `TypeError`, `KeyError`)
- Create custom exceptions for domain-specific errors
- Never use bare `except:` clauses

### 5.2 Custom Exceptions
```python
# Define custom exceptions in appropriate modules
class GitLabAPIError(Exception):
    """Base exception for GitLab API errors."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass

class AnalysisError(Exception):
    """Raised when issue analysis fails."""
    pass
```

### 5.3 Error Handling Patterns
```python
# Good: Specific exception handling
try:
    issue = client.get_issue(issue_id)
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        logger.warning(f"Issue {issue_id} not found")
        return None
    raise GitLabAPIError(f"Failed to fetch issue: {e}") from e
except requests.exceptions.RequestException as e:
    logger.error(f"Network error: {e}")
    raise GitLabAPIError(f"Network error: {e}") from e

# Bad: Bare except or too broad
try:
    issue = client.get_issue(issue_id)
except:  # Too broad
    pass
```

### 5.4 Retry Logic
- Implement retry logic with exponential backoff
- Use maximum retry limits (default: 3 attempts)
- Log retry attempts
- Don't retry on client errors (4xx), only on server errors (5xx) and network errors

```python
def call_api_with_retry(url: str, max_retries: int = 3) -> Dict:
    """Call API with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
            time.sleep(wait_time)
```

## Logging

### 6.1 Log Levels
Use appropriate log levels:
- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages (normal operations)
- **WARNING**: Warning messages (recoverable errors)
- **ERROR**: Error messages (failures that need attention)
- **CRITICAL**: Critical errors (system failures)

### 6.2 Logging Format
```python
import logging

logger = logging.getLogger(__name__)

# Good: Structured logging with context
logger.info("Processing issue", extra={
    "issue_id": issue_id,
    "project_id": project_id
})

logger.error("Failed to analyze issue", exc_info=True, extra={
    "issue_id": issue_id,
    "error": str(e)
})

# Bad: String concatenation in logs
logger.info("Processing issue " + str(issue_id))
```

### 6.3 Logging Best Practices
- Include context (issue_id, project_id, etc.) in log messages
- Use `exc_info=True` when logging exceptions
- Don't log sensitive information (API keys, passwords, tokens)
- Use appropriate log levels (don't log everything as ERROR)

## Documentation

### 7.1 Docstrings
- Use Google-style docstrings for all public functions and classes
- Include: description, Args, Returns, Raises sections
- Keep docstrings up-to-date with code changes

```python
def fetch_issue_data(
    issue_iid: int,
    include_comments: bool = True
) -> Dict[str, Any]:
    """
    Fetch comprehensive issue data from GitLab API.
    
    This function retrieves issue information including title, description,
    labels, and optionally all comments and related issues.
    
    Args:
        issue_iid: The internal issue ID (IID) in GitLab
        include_comments: Whether to include comments in the response
        
    Returns:
        Dictionary containing issue data with keys:
        - title: Issue title
        - description: Issue description
        - labels: List of label names
        - comments: List of comments (if include_comments=True)
        
    Raises:
        GitLabAPIError: If API request fails
        ValueError: If issue_iid is invalid
        
    Example:
        >>> issue = fetch_issue_data(123, include_comments=True)
        >>> print(issue['title'])
        'Fix login bug'
    """
    pass
```

### 7.2 Comments
- Use comments to explain "why", not "what"
- Code should be self-documenting
- Remove commented-out code before committing

```python
# Good: Explains why
# Retry with exponential backoff to handle transient network issues
time.sleep(2 ** attempt)

# Bad: Explains what (code already does this)
# Sleep for 2 to the power of attempt seconds
time.sleep(2 ** attempt)
```

### 7.3 Type Hints
- Use type hints for all function parameters and return values
- Use `Optional[T]` for nullable values
- Use `Union[T, U]` for multiple types
- Use `Dict[str, Any]` for flexible dictionaries

```python
from typing import Dict, List, Optional, Union, Any

def process_issues(
    issues: List[Dict[str, Any]],
    filter_by_label: Optional[str] = None
) -> Dict[str, Union[int, List[Dict[str, Any]]]]:
    """Process a list of issues."""
    pass
```

## Security Rules

### 8.1 Credential Management
- **NEVER** commit credentials, API keys, or tokens to version control
- Use environment variables for sensitive data
- Use `.gitignore` to exclude config files with secrets
- Validate credentials on startup, not at runtime

### 8.2 Input Validation
- Validate all external inputs (webhook payloads, API responses, config files)
- Sanitize user inputs before processing
- Use type checking and validation libraries when appropriate

```python
# Good: Validate input
def validate_webhook_payload(payload: Dict[str, Any]) -> bool:
    """Validate webhook payload structure."""
    required_fields = ['object_kind', 'object_attributes']
    if not all(field in payload for field in required_fields):
        raise ValueError("Invalid webhook payload: missing required fields")
    return True

# Bad: Trust input blindly
def process_webhook(payload: Dict):
    issue_id = payload['object_attributes']['iid']  # May raise KeyError
```

### 8.3 API Security
- Use HTTPS for all API calls
- Validate webhook signatures when available
- Implement rate limiting to prevent abuse
- Don't expose internal errors to external callers

### 8.4 File Security
- Never read `.env` files or any files containing secrets
- Validate file paths to prevent directory traversal
- Use secure file permissions for config files

## Performance Guidelines

### 9.1 API Calls
- Implement request timeouts (default: 30 seconds)
- Use connection pooling for multiple requests
- Cache responses when appropriate (but be careful with state)
- Batch API calls when possible

### 9.2 Memory Usage
- Avoid loading large datasets into memory
- Use generators for large data processing
- Clean up resources (close files, connections)

### 9.3 Code Performance
- Profile before optimizing
- Use appropriate data structures (dicts for lookups, sets for membership)
- Avoid premature optimization

## Testing Requirements

### 10.1 Test Coverage
- Aim for 80%+ code coverage
- Test all public functions and classes
- Test error paths and edge cases
- Test integration between components

### 10.2 Test Organization
- Mirror source structure in `tests/` directory
- One test file per source module: `test_monitor.py` for `monitor.py`
- Use descriptive test names: `test_fetch_issue_with_invalid_id_raises_error()`

### 10.3 Test Best Practices
- Use mocking for external APIs
- Use fixtures for common test data
- Keep tests independent and isolated
- Test one thing per test function

See the test files in `tests/` directory for detailed test case specifications.

## Code Review Checklist

Before submitting code, ensure:

- [ ] Code follows PEP 8 style guide
- [ ] All functions have type hints and docstrings
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate and doesn't expose secrets
- [ ] No hardcoded credentials or secrets
- [ ] Input validation is implemented
- [ ] Tests are written and passing
- [ ] Documentation is updated
- [ ] Imports are organized correctly
- [ ] Code is reviewed for security issues

## Tools and Automation

### Recommended Tools
- **Linting**: `flake8` or `pylint`
- **Formatting**: `black` (optional)
- **Type Checking**: `mypy` (optional)
- **Testing**: `pytest`
- **Coverage**: `pytest-cov`

### Pre-commit Hooks (Optional)
Consider setting up pre-commit hooks to:
- Run linters
- Check code formatting
- Run tests
- Check for secrets in commits

## Additional Resources

- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)

---

**Last Updated**: See document header for last update date.

**Documentation Version**: 1.0

