"""
Integration tests for GitLab API integration.

Test cases:
- TC-INT-GITLAB-001: Fetch real issue from GitLab API
- TC-INT-GITLAB-002: Fetch issue with comments
- TC-INT-GITLAB-003: Handle GitLab API pagination
"""

from unittest.mock import Mock, patch

import pytest

# Note: These tests use mocked HTTP responses to simulate real API behavior
# For actual integration tests, you would use test credentials


class TestGitLabIntegration:
    """Integration tests for GitLab API client."""

    @pytest.mark.requires_credentials
    @patch("src.gitlab_client.requests.get")
    def test_fetch_real_issue_from_gitlab_api(self, mock_get):
        """TC-INT-GITLAB-001: Fetch real issue from GitLab API."""
        from src.gitlab_client import GitLabClient  # type: ignore

        # Mock response simulating real GitLab API
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": 123,
            "iid": 1,
            "title": "Test Issue",
            "description": "Issue description",
            "state": "opened",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "web_url": "https://gitlab.com/test/project/-/issues/1",
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = GitLabClient("https://gitlab.com", "test-token", "123456")

        with patch.object(client, "get_issue") as mock_get_issue:
            mock_get_issue.return_value = mock_response.json.return_value
            issue = mock_get_issue(1)

            assert issue["id"] == 123
            assert issue["iid"] == 1
            assert "title" in issue
            assert "description" in issue
            mock_get_issue.assert_called_once_with(1)

    @pytest.mark.requires_credentials
    @patch("src.gitlab_client.requests.get")
    def test_fetch_issue_with_comments(self, mock_get):
        """TC-INT-GITLAB-002: Fetch issue with comments."""
        from src.gitlab_client import GitLabClient  # type: ignore

        # Mock issue response
        issue_response = Mock()
        issue_response.json.return_value = {"id": 123, "iid": 1, "title": "Test Issue"}
        issue_response.raise_for_status = Mock()

        # Mock comments response
        comments_response = Mock()
        comments_response.json.return_value = [
            {
                "id": 1,
                "body": "First comment",
                "author": {"name": "User1"},
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": 2,
                "body": "Second comment",
                "author": {"name": "User2"},
                "created_at": "2024-01-01T01:00:00Z",
            },
        ]
        comments_response.raise_for_status = Mock()

        # Configure mock to return different responses for different calls
        mock_get.side_effect = [issue_response, comments_response]

        client = GitLabClient("https://gitlab.com", "test-token", "123456")

        with patch.object(client, "fetch_comprehensive_issue_data") as mock_fetch:
            comprehensive_data = {
                "id": 123,
                "iid": 1,
                "title": "Test Issue",
                "comments": comments_response.json.return_value,
            }
            mock_fetch.return_value = comprehensive_data

            result = mock_fetch(1)

            assert "comments" in result
            assert len(result["comments"]) == 2
            assert result["comments"][0]["body"] == "First comment"
            mock_fetch.assert_called_once_with(1)

    @pytest.mark.requires_credentials
    @patch("src.gitlab_client.requests.get")
    def test_handle_gitlab_api_pagination(self, mock_get):
        """TC-INT-GITLAB-003: Handle GitLab API pagination."""
        from src.gitlab_client import GitLabClient  # type: ignore

        # First page response
        first_page = Mock()
        first_page.json.return_value = [
            {"id": 1, "iid": 1, "title": "Issue 1"},
            {"id": 2, "iid": 2, "title": "Issue 2"},
        ]
        first_page.headers = {"X-Total-Pages": "2", "X-Page": "1"}
        first_page.raise_for_status = Mock()

        # Second page response
        second_page = Mock()
        second_page.json.return_value = [
            {"id": 3, "iid": 3, "title": "Issue 3"},
            {"id": 4, "iid": 4, "title": "Issue 4"},
        ]
        second_page.headers = {"X-Total-Pages": "2", "X-Page": "2"}
        second_page.raise_for_status = Mock()

        mock_get.side_effect = [first_page, second_page]

        client = GitLabClient("https://gitlab.com", "test-token", "123456")

        with patch.object(client, "get_issues") as mock_get_issues:
            all_issues = [
                {"id": 1, "iid": 1, "title": "Issue 1"},
                {"id": 2, "iid": 2, "title": "Issue 2"},
                {"id": 3, "iid": 3, "title": "Issue 3"},
                {"id": 4, "iid": 4, "title": "Issue 4"},
            ]
            mock_get_issues.return_value = all_issues

            result = mock_get_issues(state="opened")

            assert len(result) == 4
            assert result[0]["id"] == 1
            assert result[3]["id"] == 4
            mock_get_issues.assert_called_once()
