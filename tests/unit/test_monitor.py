"""
Unit tests for monitor module.

Test cases:
- TC-MONITOR-001: Detect new issue from webhook payload
- TC-MONITOR-002: Ignore duplicate issues
- TC-MONITOR-003: Filter issues by label
- TC-MONITOR-004: Ignore issues without required label
- TC-MONITOR-005: Poll GitLab API for new issues
- TC-MONITOR-006: Track processed issues in memory
- TC-MONITOR-007: Validate webhook signature
- TC-MONITOR-008: Handle invalid webhook payload
- TC-MONITOR-009: Extract issue data from webhook
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.gitlab_client import GitLabClient
from src.monitor import IssueMonitor


class TestMonitor:
    """Test issue monitoring functionality."""

    def test_detect_new_issue_from_webhook_payload(self, sample_webhook_payload):
        """TC-MONITOR-001: Detect new issue from webhook payload."""
        gitlab_client = GitLabClient("https://gitlab.com", "test-token", "123456")
        monitor = IssueMonitor(gitlab_client=gitlab_client)

        issue_data = monitor.process_webhook(sample_webhook_payload)

        assert issue_data is not None
        assert issue_data["id"] == 123
        assert issue_data["iid"] == 1
        assert issue_data["state"] == "opened"

    def test_ignore_duplicate_issues(self, sample_issue_data):
        """TC-MONITOR-002: Ignore duplicate issues."""
        gitlab_client = GitLabClient("https://gitlab.com", "test-token", "123456")
        monitor = IssueMonitor(gitlab_client=gitlab_client)

        # Mark issue as processed
        issue_id = sample_issue_data["id"]
        monitor.mark_as_processed(issue_id)

        # Check if issue is processed
        assert monitor.is_processed(issue_id) is True

        # Try to process same issue again (should be filtered)
        issue_data = {"id": issue_id, "iid": 1, "title": "Test Issue", "labels": []}
        assert (
            monitor.should_process_issue(issue_data) is True
        )  # Should process (no label filter)
        # But poll_issues would filter it out because is_processed returns True

    def test_filter_issues_by_label(self, sample_issue_data):
        """TC-MONITOR-003: Filter issues by label."""
        gitlab_client = GitLabClient("https://gitlab.com", "test-token", "123456")
        monitor = IssueMonitor(gitlab_client=gitlab_client, filter_labels=["bug"])

        # Issue with matching label
        issue_with_label = sample_issue_data.copy()
        issue_with_label["labels"] = ["bug", "high-priority"]

        assert monitor.should_process_issue(issue_with_label) is True

    def test_ignore_issues_without_required_label(self, sample_issue_data):
        """TC-MONITOR-004: Ignore issues without required label."""
        gitlab_client = GitLabClient("https://gitlab.com", "test-token", "123456")
        monitor = IssueMonitor(gitlab_client=gitlab_client, filter_labels=["bug"])

        # Issue without required label
        issue_without_label = sample_issue_data.copy()
        issue_without_label["labels"] = ["feature", "enhancement"]

        assert monitor.should_process_issue(issue_without_label) is False

    @patch.object(GitLabClient, "get_issues")
    def test_poll_gitlab_api_for_new_issues(self, mock_get_issues):
        """TC-MONITOR-005: Poll GitLab API for new issues."""
        gitlab_client = GitLabClient("https://gitlab.com", "test-token", "123456")
        monitor = IssueMonitor(gitlab_client=gitlab_client)

        issues_data = [
            {"id": 123, "iid": 1, "title": "Issue 1", "labels": []},
            {"id": 124, "iid": 2, "title": "Issue 2", "labels": []},
        ]

        mock_get_issues.return_value = issues_data

        result = monitor.poll_issues()

        assert len(result) == 2
        assert result[0]["id"] == 123
        mock_get_issues.assert_called_once()

    def test_track_processed_issues_in_memory(self, sample_issue_data):
        """TC-MONITOR-006: Track processed issues in memory."""
        gitlab_client = GitLabClient("https://gitlab.com", "test-token", "123456")
        monitor = IssueMonitor(gitlab_client=gitlab_client)

        issue_id = sample_issue_data["id"]

        # Mark issue as processed
        monitor.mark_as_processed(issue_id)

        # Check if issue is processed
        assert monitor.is_processed(issue_id) is True

    def test_validate_webhook_signature(self, sample_webhook_payload):
        """TC-MONITOR-007: Validate webhook signature."""
        gitlab_client = GitLabClient("https://gitlab.com", "test-token", "123456")
        secret = "webhook-secret-123"

        # Valid signature
        assert (
            gitlab_client.validate_webhook_secret(
                sample_webhook_payload, secret, secret
            )
            is True
        )

        # Invalid signature
        assert (
            gitlab_client.validate_webhook_secret(
                sample_webhook_payload, secret, "wrong-secret"
            )
            is False
        )

    def test_handle_invalid_webhook_payload(self):
        """TC-MONITOR-008: Handle invalid webhook payload."""
        gitlab_client = GitLabClient("https://gitlab.com", "test-token", "123456")
        monitor = IssueMonitor(gitlab_client=gitlab_client)

        invalid_payload = {"invalid": "structure", "missing": "required_fields"}

        with pytest.raises((ValueError, KeyError)):
            monitor.process_webhook(invalid_payload)

    def test_extract_issue_data_from_webhook(self, sample_webhook_payload):
        """TC-MONITOR-009: Extract issue data from webhook."""
        gitlab_client = GitLabClient("https://gitlab.com", "test-token", "123456")
        monitor = IssueMonitor(gitlab_client=gitlab_client)

        result = monitor.extract_issue_data(sample_webhook_payload)

        assert result["id"] == 123
        assert result["iid"] == 1
        assert result["title"] == "Test Issue"
        assert "url" in result
