"""
Custom exception classes for GitLab Issues Analyzer.

This module defines all custom exceptions used throughout the application.
"""

from typing import Optional


class GitLabIssuesAnalyzerError(Exception):
    """Base exception for all GitLab Issues Analyzer errors."""

    pass


class ConfigurationError(GitLabIssuesAnalyzerError):
    """Raised when configuration is invalid or missing required fields."""

    pass


class GitLabAPIError(GitLabIssuesAnalyzerError):
    """Raised when GitLab API operations fail."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[dict] = None,
    ):
        """
        Initialize GitLab API error.

        Args:
            message: Error message
            status_code: HTTP status code (if available)
            response: API response dictionary (if available)
        """
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AnalysisError(GitLabIssuesAnalyzerError):
    """Raised when issue analysis fails."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        timeout: bool = False,
        retry_after: Optional[int] = None,
    ):
        """
        Initialize analysis error.

        Args:
            message: Error message
            status_code: HTTP status code (if available)
            timeout: Whether error was due to timeout
            retry_after: Seconds to wait before retry (if rate limited)
        """
        super().__init__(message)
        self.status_code = status_code
        self.timeout = timeout
        self.retry_after = retry_after


class EmailError(GitLabIssuesAnalyzerError):
    """Raised when email sending fails."""

    def __init__(self, message: str, smtp_error: Optional[Exception] = None):
        """
        Initialize email error.

        Args:
            message: Error message
            smtp_error: Original SMTP exception (if available)
        """
        super().__init__(message)
        self.smtp_error = smtp_error
