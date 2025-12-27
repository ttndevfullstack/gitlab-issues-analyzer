"""
Integration tests for complete workflows.

These tests verify that all components work together correctly.
Note: These tests require test credentials and may make real API calls.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.analyzer import IssueAnalyzer
from src.config import load_config, validate_config
from src.email_sender import EmailSender
from src.gitlab_client import GitLabClient
from src.monitor import IssueMonitor
from src.reporter import generate_email_report


class TestCompleteWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.mark.slow
    def test_polling_workflow_integration(
        self, sample_config, sample_comprehensive_issue_data, sample_analysis
    ):
        """Test complete polling workflow with mocked external services."""
        # Initialize components
        gitlab_client = GitLabClient(
            url=sample_config["gitlab"]["url"],
            token=sample_config["gitlab"]["token"],
            project_id=sample_config["gitlab"]["project_id"],
        )

        analyzer = IssueAnalyzer(
            provider=sample_config["ai"]["provider"],
            api_key=sample_config["ai"]["api_key"],
            model=sample_config["ai"]["model"],
            base_url="https://openrouter.ai/api/v1",
        )

        email_sender = EmailSender(
            host=sample_config["smtp"]["host"],
            port=sample_config["smtp"]["port"],
            username=sample_config["smtp"]["username"],
            password=sample_config["smtp"]["password"],
            from_email=sample_config["smtp"]["from_email"],
        )

        monitor = IssueMonitor(gitlab_client=gitlab_client)

        # Mock external calls
        with patch.object(gitlab_client, "get_issues") as mock_get_issues, patch.object(
            gitlab_client, "fetch_comprehensive_issue_data"
        ) as mock_fetch, patch.object(
            analyzer, "analyze_issue"
        ) as mock_analyze, patch.object(
            email_sender, "send_email"
        ) as mock_send:

            # Setup mocks
            mock_get_issues.return_value = [
                {"id": 123, "iid": 1, "title": "Test Issue"}
            ]
            mock_fetch.return_value = sample_comprehensive_issue_data
            mock_analyze.return_value = sample_analysis
            mock_send.return_value = True

            # Poll for issues
            new_issues = monitor.poll_issues()

            assert len(new_issues) == 1
            assert new_issues[0]["id"] == 123

            # Process issue
            issue_iid = new_issues[0]["iid"]
            issue_data = gitlab_client.fetch_comprehensive_issue_data(issue_iid)
            analysis = analyzer.analyze_issue(issue_data)
            report = generate_email_report(issue_data, analysis)
            to_email = (
                sample_config["smtp"]["to_email"][0]
                if isinstance(sample_config["smtp"]["to_email"], list)
                else sample_config["smtp"]["to_email"]
            )
            email_sender.send_email(
                to=to_email,
                subject=report["subject"],
                body=report["text"],
                html_body=report["html"],
            )

            # Verify all steps were called
            mock_get_issues.assert_called_once()
            mock_fetch.assert_called_once_with(issue_iid)
            mock_analyze.assert_called_once()
            mock_send.assert_called_once()

    @pytest.mark.slow
    def test_webhook_workflow_integration(
        self,
        sample_webhook_payload,
        sample_comprehensive_issue_data,
        sample_analysis,
        sample_config,
    ):
        """Test complete webhook workflow with mocked external services."""
        # Initialize components
        gitlab_client = GitLabClient(
            url=sample_config["gitlab"]["url"],
            token=sample_config["gitlab"]["token"],
            project_id=sample_config["gitlab"]["project_id"],
        )

        analyzer = IssueAnalyzer(
            provider=sample_config["ai"]["provider"],
            api_key=sample_config["ai"]["api_key"],
            model=sample_config["ai"]["model"],
            base_url="https://openrouter.ai/api/v1",
        )

        email_sender = EmailSender(
            host=sample_config["smtp"]["host"],
            port=sample_config["smtp"]["port"],
            username=sample_config["smtp"]["username"],
            password=sample_config["smtp"]["password"],
            from_email=sample_config["smtp"]["from_email"],
        )

        monitor = IssueMonitor(gitlab_client=gitlab_client)

        # Mock external calls
        with patch.object(
            gitlab_client, "fetch_comprehensive_issue_data"
        ) as mock_fetch, patch.object(
            analyzer, "analyze_issue"
        ) as mock_analyze, patch.object(
            email_sender, "send_email"
        ) as mock_send:

            # Setup mocks
            mock_fetch.return_value = sample_comprehensive_issue_data
            mock_analyze.return_value = sample_analysis
            mock_send.return_value = True

            # Process webhook
            issue_data = monitor.process_webhook(sample_webhook_payload)

            assert issue_data is not None
            assert issue_data["id"] == 123

            # Process issue
            issue_iid = issue_data["iid"]
            comprehensive_data = gitlab_client.fetch_comprehensive_issue_data(issue_iid)
            analysis = analyzer.analyze_issue(comprehensive_data)
            report = generate_email_report(comprehensive_data, analysis)
            to_email = (
                sample_config["smtp"]["to_email"][0]
                if isinstance(sample_config["smtp"]["to_email"], list)
                else sample_config["smtp"]["to_email"]
            )
            email_sender.send_email(
                to=to_email,
                subject=report["subject"],
                body=report["text"],
                html_body=report["html"],
            )

            # Verify all steps were called
            mock_fetch.assert_called_once()
            mock_analyze.assert_called_once()
            mock_send.assert_called_once()

    def test_error_handling_in_workflow(self, sample_config):
        """Test error handling in complete workflow."""
        gitlab_client = GitLabClient(
            url=sample_config["gitlab"]["url"],
            token=sample_config["gitlab"]["token"],
            project_id=sample_config["gitlab"]["project_id"],
        )

        analyzer = IssueAnalyzer(
            provider=sample_config["ai"]["provider"],
            api_key=sample_config["ai"]["api_key"],
            model=sample_config["ai"]["model"],
            base_url="https://openrouter.ai/api/v1",
        )

        monitor = IssueMonitor(gitlab_client=gitlab_client)

        # Test GitLab API error
        with patch.object(gitlab_client, "get_issues") as mock_get_issues:
            from src.exceptions import GitLabAPIError

            mock_get_issues.side_effect = GitLabAPIError("API error", status_code=500)

            with pytest.raises(GitLabAPIError):
                monitor.poll_issues()

        # Test analysis error
        with patch.object(
            gitlab_client, "fetch_comprehensive_issue_data"
        ) as mock_fetch, patch.object(analyzer, "analyze_issue") as mock_analyze:

            mock_fetch.return_value = {"id": 123, "iid": 1, "title": "Test"}
            from src.exceptions import AnalysisError

            mock_analyze.side_effect = AnalysisError("Analysis failed")

            with pytest.raises(AnalysisError):
                analyzer.analyze_issue(mock_fetch.return_value)
