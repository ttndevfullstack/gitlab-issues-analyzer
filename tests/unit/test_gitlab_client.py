"""
Unit tests for gitlab_client module.

Test cases:
- TC-GITLAB-001: Fetch issue by IID successfully
- TC-GITLAB-002: Handle 404 error for non-existent issue
- TC-GITLAB-003: Fetch issue comments successfully
- TC-GITLAB-004: Fetch related issues successfully
- TC-GITLAB-005: Fetch issue attachments successfully
- TC-GITLAB-006: Handle API rate limiting (429 error)
- TC-GITLAB-007: Handle network timeout
- TC-GITLAB-008: Handle invalid authentication token
- TC-GITLAB-009: Parse webhook payload correctly
- TC-GITLAB-010: Validate webhook secret
- TC-GITLAB-011: Fetch comprehensive issue data
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from requests.exceptions import HTTPError, Timeout

from src.exceptions import GitLabAPIError
from src.gitlab_client import GitLabClient


class TestGitLabClient:
    """Test GitLab API client functionality."""

    @patch("src.gitlab_client.requests.request")
    def test_fetch_issue_by_iid_successfully(self, mock_request, sample_issue_data):
        """TC-GITLAB-001: Fetch issue by IID successfully."""
        mock_response = Mock()
        mock_response.json.return_value = sample_issue_data
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        client = GitLabClient("https://gitlab.com", "test-token", "123456")
        issue = client.get_issue(1)

        assert issue["id"] == 123
        assert issue["iid"] == 1
        assert issue["title"] == "Test Issue"
        mock_request.assert_called_once()

    @patch("src.gitlab_client.requests.get")
    def test_handle_404_error_for_nonexistent_issue(self, mock_get):
        """TC-GITLAB-002: Handle 404 error for non-existent issue."""
        mock_response = Mock()
        http_error = HTTPError("404 Not Found")
        http_error.response = mock_response
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "404 Issue Not Found"}
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        client = GitLabClient("https://gitlab.com", "test-token", "123456")

        with pytest.raises(GitLabAPIError) as exc_info:
            client.get_issue(999, project_id=123456)

        assert exc_info.value.status_code == 404

    @patch("src.gitlab_client.requests.request")
    def test_fetch_issue_comments_successfully(self, mock_request):
        """TC-GITLAB-003: Fetch issue comments successfully."""
        comments_data = [
            {
                "id": 1,
                "body": "First comment",
                "author": {"name": "User1"},
                "created_at": "2024-01-01T00:00:00Z",
                "system": False,
            },
            {
                "id": 2,
                "body": "Second comment",
                "author": {"name": "User2"},
                "created_at": "2024-01-01T01:00:00Z",
                "system": False,
            },
        ]

        mock_response = Mock()
        mock_response.json.return_value = comments_data
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        client = GitLabClient("https://gitlab.com", "test-token", "123456")
        comments = client.get_issue_comments(1)

        assert len(comments) == 2
        assert comments[0]["body"] == "First comment"
        mock_request.assert_called_once()

    @patch("src.gitlab_client.requests.request")
    def test_fetch_related_issues_successfully(self, mock_request):
        """TC-GITLAB-004: Fetch related issues successfully."""
        related_issues = [
            {
                "source_issue": {"id": 123, "iid": 1, "title": "Issue 1"},
                "target_issue": {
                    "id": 124,
                    "iid": 2,
                    "title": "Issue 2",
                    "state": "opened",
                    "web_url": "https://gitlab.com/issues/2",
                },
                "link_type": "relates_to",
            }
        ]

        mock_response = Mock()
        mock_response.json.return_value = related_issues
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        client = GitLabClient("https://gitlab.com", "test-token", "123456")
        issues = client.get_related_issues(1)

        assert len(issues) > 0
        assert issues[0]["title"] == "Issue 2"
        mock_request.assert_called_once()

    @patch("src.gitlab_client.requests.request")
    def test_fetch_issue_attachments_successfully(
        self, mock_request, sample_issue_data
    ):
        """TC-GITLAB-005: Fetch issue attachments successfully."""
        # Mock get_issue and get_issue_comments
        issue_response = Mock()
        issue_response.json.return_value = {
            **sample_issue_data,
            "description": "![screenshot](https://gitlab.com/uploads/abc123/screenshot.png)",
        }
        issue_response.raise_for_status = Mock()

        comments_response = Mock()
        comments_response.json.return_value = []
        comments_response.raise_for_status = Mock()

        mock_request.side_effect = [issue_response, comments_response]

        client = GitLabClient("https://gitlab.com", "test-token", "123456")
        attachments = client.get_issue_attachments(1)

        assert len(attachments) > 0
        assert "uploads" in attachments[0]["url"] or "http" in attachments[0]["url"]

    @patch("src.gitlab_client.requests.request")
    @patch("time.sleep")  # Mock sleep to speed up test
    def test_handle_api_rate_limiting_429_error(self, mock_sleep, mock_request):
        """TC-GITLAB-006: Handle API rate limiting (429 error)."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.raise_for_status.side_effect = HTTPError("Rate limit exceeded")
        mock_response.json.return_value = {"message": "Rate limit exceeded"}
        mock_request.return_value = mock_response

        client = GitLabClient(
            "https://gitlab.com", "test-token", "123456", max_retries=2
        )

        with pytest.raises(GitLabAPIError) as exc_info:
            client.get_issue(1)

        # Should have retried
        assert mock_request.call_count > 1

    @patch("src.gitlab_client.requests.request")
    @patch("time.sleep")  # Mock sleep to speed up test
    def test_handle_network_timeout(self, mock_sleep, mock_request):
        """TC-GITLAB-007: Handle network timeout."""
        mock_request.side_effect = Timeout("Connection timeout")

        client = GitLabClient(
            "https://gitlab.com", "test-token", "123456", max_retries=2
        )

        with pytest.raises(GitLabAPIError) as exc_info:
            client.get_issue(1)

        assert "timeout" in str(exc_info.value).lower()

    @patch("src.gitlab_client.requests.get")
    def test_handle_invalid_authentication_token(self, mock_get):
        """TC-GITLAB-008: Handle invalid authentication token."""
        mock_response = Mock()
        http_error = HTTPError("Unauthorized")
        http_error.response = mock_response
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = http_error
        mock_response.json.return_value = {"message": "Unauthorized"}
        mock_get.return_value = mock_response

        client = GitLabClient("https://gitlab.com", "invalid-token", "123456")

        with pytest.raises(GitLabAPIError) as exc_info:
            client.get_issue(1, project_id=123456)

        assert exc_info.value.status_code == 401

    def test_parse_webhook_payload_correctly(self, sample_webhook_payload):
        """TC-GITLAB-009: Parse webhook payload correctly."""
        client = GitLabClient("https://gitlab.com", "test-token", "123456")
        issue_data = client.parse_webhook_payload(sample_webhook_payload)

        assert issue_data["id"] == 123
        assert issue_data["iid"] == 1
        assert issue_data["title"] == "Test Issue"
        assert "url" in issue_data

    def test_validate_webhook_secret(self):
        """TC-GITLAB-010: Validate webhook secret."""
        client = GitLabClient("https://gitlab.com", "test-token", "123456")

        # Test with correct secret
        assert (
            client.validate_webhook_secret({}, "correct-secret", "correct-secret")
            is True
        )

        # Test with incorrect secret
        assert (
            client.validate_webhook_secret({}, "correct-secret", "wrong-secret")
            is False
        )

        # Test with no secret
        assert client.validate_webhook_secret({}, None, "token") is False

    @patch("src.gitlab_client.requests.request")
    def test_fetch_comprehensive_issue_data(
        self, mock_request, sample_comprehensive_issue_data
    ):
        """TC-GITLAB-011: Fetch comprehensive issue data."""
        # Mock responses for get_issue, get_issue_comments, get_related_issues
        issue_response = Mock()
        issue_response.json.return_value = sample_comprehensive_issue_data
        issue_response.raise_for_status = Mock()

        comments_response = Mock()
        comments_response.json.return_value = sample_comprehensive_issue_data.get(
            "comments", []
        )
        comments_response.raise_for_status = Mock()

        links_response = Mock()
        links_response.json.return_value = []
        links_response.raise_for_status = Mock()

        # get_issue_attachments calls get_issue and get_issue_comments again
        mock_request.side_effect = [
            issue_response,  # get_issue
            comments_response,  # get_issue_comments
            links_response,  # get_related_issues (or 404)
            issue_response,  # get_issue (for attachments)
            comments_response,  # get_issue_comments (for attachments)
        ]

        client = GitLabClient("https://gitlab.com", "test-token", "123456")
        result = client.fetch_comprehensive_issue_data(1)

        assert "id" in result
        assert "comments" in result
        assert "related_issues" in result
        assert "attachments" in result
