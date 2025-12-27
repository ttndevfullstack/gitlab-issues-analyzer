"""
Pytest configuration and shared fixtures.

This module provides common fixtures used across all test modules.
"""

from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def sample_issue_data() -> Dict[str, Any]:
    """Sample issue data for testing."""
    return {
        "id": 123,
        "iid": 1,
        "title": "Test Issue",
        "description": "This is a test issue description",
        "state": "opened",
        "labels": ["bug", "high-priority"],
        "author": {
            "name": "Test User",
            "username": "testuser",
            "email": "test@example.com",
        },
        "assignee": {"name": "Assignee User", "username": "assignee"},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "web_url": "https://gitlab.com/test/project/-/issues/1",
        "milestone": None,
        "priority": "high",
    }


@pytest.fixture
def sample_comprehensive_issue_data(sample_issue_data) -> Dict[str, Any]:
    """Sample comprehensive issue data with comments, related issues, and attachments."""
    return {
        **sample_issue_data,
        "comments": [
            {
                "id": 1,
                "body": "This is a comment",
                "author": {"name": "Commenter", "username": "commenter"},
                "created_at": "2024-01-01T01:00:00Z",
            },
            {
                "id": 2,
                "body": "Another comment",
                "author": {"name": "Another User", "username": "another"},
                "created_at": "2024-01-01T02:00:00Z",
            },
        ],
        "related_issues": [
            {
                "id": 124,
                "iid": 2,
                "title": "Related Issue",
                "state": "opened",
                "web_url": "https://gitlab.com/test/project/-/issues/2",
            }
        ],
        "attachments": [
            {
                "filename": "screenshot.png",
                "url": "https://gitlab.com/test/project/uploads/abc123/screenshot.png",
            }
        ],
    }


@pytest.fixture
def sample_analysis() -> Dict[str, str]:
    """Sample analysis result for testing (new format with html and raw)."""
    return {
        "html": """<!-- AI_EMAIL_HTML_START -->
<div>Test HTML content with analysis</div>
<!-- AI_EMAIL_HTML_END -->""",
        "raw": "W1 — Why: Root cause analysis\nW2 — What: Problem identification\nW3 — Who: Stakeholders\nH — How: Solutions and trade-offs\nT — Test: Experiments and milestones\nR — Reflect: Best choice and next steps",
    }


@pytest.fixture
def sample_webhook_payload() -> Dict[str, Any]:
    """Sample GitLab webhook payload for testing."""
    return {
        "object_kind": "issue",
        "event_type": "issue",
        "user": {"name": "Test User", "username": "testuser"},
        "project": {
            "id": 456,
            "name": "Test Project",
            "path_with_namespace": "test/project",
        },
        "object_attributes": {
            "id": 123,
            "iid": 1,
            "title": "Test Issue",
            "description": "Issue description",
            "state": "opened",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "url": "https://gitlab.com/test/project/-/issues/1",
        },
        "labels": [
            {"title": "bug", "color": "#d9534f"},
            {"title": "high-priority", "color": "#f0ad4e"},
        ],
        "assignee": {"name": "Assignee User", "username": "assignee"},
    }


@pytest.fixture
def mock_gitlab_response() -> Mock:
    """Mock GitLab API response."""
    mock = Mock()
    mock.json.return_value = {
        "id": 123,
        "iid": 1,
        "title": "Test Issue",
        "description": "Test description",
        "state": "opened",
    }
    mock.raise_for_status = Mock()
    mock.status_code = 200
    return mock


@pytest.fixture
def mock_gitlab_404_response() -> Mock:
    """Mock GitLab API 404 response."""
    mock = Mock()
    mock.raise_for_status.side_effect = Exception("404 Not Found")
    mock.status_code = 404
    return mock


@pytest.fixture
def mock_ai_response() -> Dict[str, Any]:
    """Mock AI API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": """W1 — Why: Root cause analysis
W2 — What: Problem identification
W3 — Who: Stakeholders
H — How: Solutions and trade-offs
T — Test: Experiments and milestones
R — Reflect: Best choice and next steps"""
                }
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
    }


@pytest.fixture
def mock_smtp_server() -> MagicMock:
    """Mock SMTP server for testing."""
    mock_server = MagicMock()
    mock_server.sendmail.return_value = {}
    mock_server.quit.return_value = None
    return mock_server


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample configuration dictionary for testing."""
    return {
        "gitlab": {
            "url": "https://gitlab.com",
            "token": "test-token-123",
            "project_id": "123456",
            "webhook_secret": "webhook-secret-123",
        },
        "ai": {
            "provider": "openrouter",
            "api_key": "test-api-key-123",
            "model": "deepseek/deepseek-v3.2",
            "temperature": 0.7,
            "max_tokens": 2000,
            "enable_reasoning": True,
        },
        "smtp": {
            "host": "smtp.example.com",
            "port": 587,
            "username": "test@example.com",
            "password": "test-password",
            "from_email": "test@example.com",
            "to_email": ["recipient@example.com"],
            "use_tls": True,
        },
        "app": {
            "mode": "webhook",
            "poll_interval": 60,
            "webhook_port": 8080,
            "log_level": "INFO",
        },
    }


@pytest.fixture
def sample_smtp_config() -> Dict[str, Any]:
    """Sample SMTP configuration for testing."""
    return {
        "host": "smtp.example.com",
        "port": 587,
        "username": "test@example.com",
        "password": "test-password",
        "from_email": "test@example.com",
        "to_email": ["recipient@example.com"],
        "use_tls": True,
    }
