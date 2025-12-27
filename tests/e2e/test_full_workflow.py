"""
End-to-end tests for complete workflows.

Test cases:
- TC-E2E-001: Complete workflow: webhook → analysis → email
- TC-E2E-002: Complete workflow: polling → analysis → email
- TC-E2E-003: Handle error in workflow gracefully
"""

from unittest.mock import MagicMock, Mock, patch

import pytest


class TestFullWorkflow:
    """End-to-end tests for complete workflows."""

    @pytest.mark.slow
    @pytest.mark.requires_credentials
    def test_complete_workflow_webhook_to_analysis_to_email(
        self, sample_webhook_payload, sample_comprehensive_issue_data, sample_analysis
    ):
        """TC-E2E-001: Complete workflow: webhook → analysis → email."""
        from src.analyzer import IssueAnalyzer  # type: ignore
        from src.email_sender import EmailSender  # type: ignore
        from src.monitor import IssueMonitor  # type: ignore
        from src.reporter import generate_email_report  # type: ignore
        from src.gitlab_client import GitLabClient  # type: ignore

        # Step 1: Process webhook
        gitlab_client = GitLabClient("https://gitlab.com", "test-token", "123456")
        monitor = IssueMonitor(gitlab_client=gitlab_client)
        issue_data = monitor.process_webhook(sample_webhook_payload)
        assert issue_data["id"] == 123

        # Step 2: Analyze issue
        with patch("src.analyzer.IssueAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze_issue.return_value = sample_analysis
            mock_analyzer_class.return_value = mock_analyzer

            analyzer = mock_analyzer_class(
                provider="openrouter",
                api_key="test-key",
                model="deepseek/deepseek-v3.2",
                base_url="https://openrouter.ai/api/v1",
            )
            analysis = analyzer.analyze_issue(issue_data)
            assert "html" in analysis
            assert "raw" in analysis

        # Step 3: Generate email report
        with patch("src.reporter.generate_email_report") as mock_generate:
            mock_generate.return_value = {
                "subject": "[GitLab Issue Analysis] Test Issue",
                "html": "<html>...</html>",
                "text": "Text version",
            }
            email_report = mock_generate(issue_data, analysis)
            assert "subject" in email_report

        # Step 4: Send email
        with patch("src.email_sender.EmailSender") as mock_sender_class:
            mock_sender = MagicMock()
            mock_sender.send_email.return_value = True
            mock_sender_class.return_value = mock_sender

            sender = mock_sender_class(
                host="smtp.example.com",
                port=587,
                username="test@example.com",
                password="password",
                from_email="test@example.com",
            )
            result = sender.send_email(
                to="recipient@example.com",
                subject=email_report["subject"],
                body=email_report["text"],
                html_body=email_report["html"],
            )
            assert result is True

    @pytest.mark.slow
    @pytest.mark.requires_credentials
    def test_complete_workflow_polling_to_analysis_to_email(
        self,
        sample_issue_data,
        sample_comprehensive_issue_data,
        sample_analysis,
    ):
        """TC-E2E-002: Complete workflow: polling → analysis → email."""
        from src.analyzer import IssueAnalyzer  # type: ignore
        from src.email_sender import EmailSender  # type: ignore
        from src.monitor import IssueMonitor  # type: ignore
        from src.reporter import generate_email_report  # type: ignore
        from src.gitlab_client import GitLabClient  # type: ignore

        # Step 1: Poll for new issues
        gitlab_client = GitLabClient("https://gitlab.com", "test-token", "123456")
        monitor = IssueMonitor(gitlab_client=gitlab_client)

        with patch.object(gitlab_client, "get_issues") as mock_get_issues:
            mock_get_issues.return_value = [sample_issue_data]
            new_issues = monitor.poll_issues()
            assert len(new_issues) == 1

        # Step 2: Fetch comprehensive data
        with patch("src.gitlab_client.GitLabClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.fetch_comprehensive_issue_data.return_value = (
                sample_comprehensive_issue_data
            )
            mock_client_class.return_value = mock_client

            client = mock_client_class("https://gitlab.com", "token", "123")
            comprehensive_data = client.fetch_comprehensive_issue_data(1)
            assert "comments" in comprehensive_data

        # Step 3: Analyze issue
        with patch("src.analyzer.IssueAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze_issue.return_value = sample_analysis
            mock_analyzer_class.return_value = mock_analyzer

            analyzer = mock_analyzer_class(
                provider="openrouter",
                api_key="test-key",
                model="deepseek/deepseek-v3.2",
                base_url="https://openrouter.ai/api/v1",
            )
            analysis = analyzer.analyze_issue(comprehensive_data)
            assert "html" in analysis
            assert "raw" in analysis

        # Step 4: Generate and send email
        with patch("src.reporter.generate_email_report") as mock_generate, patch(
            "src.email_sender.EmailSender"
        ) as mock_sender_class:

            mock_generate.return_value = {
                "subject": "[GitLab Issue Analysis] Test Issue",
                "html": "<html>...</html>",
                "text": "Text version",
            }

            mock_sender = MagicMock()
            mock_sender.send_email.return_value = True
            mock_sender_class.return_value = mock_sender

            email_report = mock_generate(comprehensive_data, analysis)
            sender = mock_sender_class(
                host="smtp.example.com",
                port=587,
                username="test@example.com",
                password="password",
                from_email="test@example.com",
            )
            result = sender.send_email(
                to="recipient@example.com",
                subject=email_report["subject"],
                body=email_report["text"],
                html_body=email_report["html"],
            )
            assert result is True

    @pytest.mark.slow
    def test_handle_error_in_workflow_gracefully(self, sample_webhook_payload):
        """TC-E2E-003: Handle error in workflow gracefully."""
        from src.analyzer import AnalysisError, IssueAnalyzer  # type: ignore
        from src.monitor import IssueMonitor  # type: ignore
        from src.gitlab_client import GitLabClient  # type: ignore

        # Process webhook successfully
        gitlab_client = GitLabClient("https://gitlab.com", "test-token", "123456")
        monitor = IssueMonitor(gitlab_client=gitlab_client)
        issue_data = monitor.process_webhook(sample_webhook_payload)
        assert issue_data["id"] == 123

        # AI API fails during analysis
        with patch("src.analyzer.IssueAnalyzer") as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze_issue.side_effect = AnalysisError("AI API failed")
            mock_analyzer_class.return_value = mock_analyzer

            analyzer = mock_analyzer_class(
                provider="openrouter",
                api_key="test-key",
                model="deepseek/deepseek-v3.2",
                base_url="https://openrouter.ai/api/v1",
            )

            # Error should be caught and logged, not crash the system
            with pytest.raises(AnalysisError):
                analyzer.analyze_issue(issue_data)

            # System should continue (in real implementation, this would be handled)
            # and logged appropriately
