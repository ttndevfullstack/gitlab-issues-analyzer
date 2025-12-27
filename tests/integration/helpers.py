"""
Integration test helpers.

This module provides utilities for integration testing.
"""

import json
import os
from typing import Any, Dict, Optional


def get_test_config() -> Optional[Dict[str, Any]]:
    """
    Get test configuration from environment variables.

    Returns:
        Configuration dictionary if all required test credentials are set, None otherwise
    """
    required_vars = [
        "TEST_GITLAB_URL",
        "TEST_GITLAB_TOKEN",
        "TEST_GITLAB_PROJECT_ID",
        "TEST_AI_API_KEY",
        "TEST_SMTP_HOST",
        "TEST_SMTP_USERNAME",
        "TEST_SMTP_PASSWORD",
        "TEST_SMTP_FROM_EMAIL",
        "TEST_SMTP_TO_EMAIL",
    ]

    # Check if all required variables are set
    if not all(os.getenv(var) for var in required_vars):
        return None

    return {
        "gitlab": {
            "url": os.getenv("TEST_GITLAB_URL"),
            "token": os.getenv("TEST_GITLAB_TOKEN"),
            "project_id": os.getenv("TEST_GITLAB_PROJECT_ID"),
        },
        "ai": {
            "provider": os.getenv("TEST_AI_PROVIDER", "deepseek"),
            "api_key": os.getenv("TEST_AI_API_KEY"),
            "model": os.getenv("TEST_AI_MODEL", "deepseek-chat"),
        },
        "smtp": {
            "host": os.getenv("TEST_SMTP_HOST"),
            "port": int(os.getenv("TEST_SMTP_PORT", "587")),
            "username": os.getenv("TEST_SMTP_USERNAME"),
            "password": os.getenv("TEST_SMTP_PASSWORD"),
            "from_email": os.getenv("TEST_SMTP_FROM_EMAIL"),
            "to_email": os.getenv("TEST_SMTP_TO_EMAIL"),
        },
        "app": {"mode": "poll", "poll_interval": 60, "log_level": "DEBUG"},
    }


def create_test_issue_data(issue_iid: int = 1) -> Dict[str, Any]:
    """
    Create test issue data structure.

    Args:
        issue_iid: Issue IID

    Returns:
        Test issue data dictionary
    """
    return {
        "id": 100 + issue_iid,
        "iid": issue_iid,
        "title": f"Test Issue #{issue_iid}",
        "description": "This is a test issue for integration testing",
        "state": "opened",
        "labels": ["test"],
        "author": {"id": 1, "username": "testuser", "name": "Test User"},
        "assignee": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "web_url": f"https://gitlab.com/test/project/-/issues/{issue_iid}",
        "comments": [],
        "related_issues": [],
        "attachments": [],
        "comment_count": 0,
    }


def skip_if_no_credentials():
    """
    Pytest marker helper to skip tests if credentials are not available.

    Usage:
        @pytest.mark.skipif(not get_test_config(), reason="Test credentials not available")
        def test_something():
            ...
    """
    return get_test_config() is None
