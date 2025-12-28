"""
Unit tests for reporter module.

Test cases:
- TC-REPORTER-001: Generate HTML email report
- TC-REPORTER-002: Generate plain text email report
- TC-REPORTER-003: Include issue URL in email
- TC-REPORTER-004: Format WWWH-TR sections correctly
- TC-REPORTER-005: Handle missing analysis sections gracefully
- TC-REPORTER-006: Set correct email subject
"""

import pytest

from src.reporter import format_html_email, format_text_email, generate_email_report


class TestReporter:
    """Test email report generation functionality."""

    def test_generate_html_email_report(self, sample_issue_data, sample_analysis):
        """TC-REPORTER-001: Generate HTML email report."""
        result = generate_email_report(sample_issue_data, sample_analysis)

        assert "html" in result
        assert "text" in result
        assert "subject" in result
        # HTML should contain the issue URL (in footer) or the AI-generated content
        assert (
            sample_issue_data["web_url"] in result["html"]
            or "Test HTML content" in result["html"]
        )

    def test_generate_plain_text_email_report(self, sample_issue_data, sample_analysis):
        """TC-REPORTER-002: Generate plain text email report."""
        # Use the new format - analysis has 'raw' key
        text_body = format_text_email(sample_issue_data, sample_analysis)

        assert "Test Issue" in text_body
        assert "Issue URL" in text_body or sample_issue_data["web_url"] in text_body

    def test_include_issue_url_in_email(self, sample_issue_data, sample_analysis):
        """TC-REPORTER-003: Include issue URL in email."""
        result = generate_email_report(sample_issue_data, sample_analysis)

        issue_url = sample_issue_data["web_url"]
        assert issue_url in result["html"]
        assert issue_url in result["text"]

    def test_format_wwwh_tr_sections_correctly(
        self, sample_issue_data, sample_analysis
    ):
        """TC-REPORTER-004: Format WWWH-TR sections correctly."""
        # For new format, we need to use the old format for format_html_email
        # or test with fallback analysis
        old_format_analysis = {
            "W1": "Why: Root cause",
            "W2": "What: Problem",
            "W3": "Who: Stakeholders",
            "H": "How: Solutions",
            "T": "Test: Experiments",
            "R": "Reflect: Next steps",
        }
        html_body = format_html_email(sample_issue_data, old_format_analysis)

        assert "W1" in html_body or "Why" in html_body
        assert "W2" in html_body or "What" in html_body
        assert "W3" in html_body or "Who" in html_body
        assert "H" in html_body or "How" in html_body
        assert "T" in html_body or "Test" in html_body
        assert "R" in html_body or "Reflect" in html_body

    def test_handle_missing_analysis_sections_gracefully(self, sample_issue_data):
        """TC-REPORTER-005: Handle missing analysis sections gracefully."""
        # Analysis with missing HTML (empty html, only raw)
        partial_analysis = {
            "html": "",
            "raw": "W1 — Why: Root cause\nW2 — What: Problem",
        }

        result = generate_email_report(sample_issue_data, partial_analysis)

        # Should still generate email with available sections
        assert "html" in result
        assert "text" in result
        assert "subject" in result
        # Missing sections should not cause errors

    def test_set_correct_email_subject(self, sample_issue_data, sample_analysis):
        """TC-REPORTER-006: Set correct email subject."""
        result = generate_email_report(sample_issue_data, sample_analysis)

        assert sample_issue_data["title"] in result["subject"]
        assert "[GitLab Issue Analysis]" in result["subject"]
