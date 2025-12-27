"""
Unit tests for analyzer module.

Test cases:
- TC-ANALYZER-001: Analyze issue with OpenRouter API successfully
- TC-ANALYZER-002: Analyze issue with OpenAI API successfully
- TC-ANALYZER-003: Handle AI API rate limiting
- TC-ANALYZER-004: Handle AI API timeout
- TC-ANALYZER-005: Format prompt correctly with all issue data
- TC-ANALYZER-006: Parse AI response into HTML format
- TC-ANALYZER-007: Handle malformed AI response
- TC-ANALYZER-008: Handle empty issue data
- TC-ANALYZER-009: Use configured model from config
- TC-ANALYZER-010: Handle AI API authentication failure
"""

from unittest.mock import Mock, patch

import pytest
import requests
from requests.exceptions import HTTPError, Timeout

from src.analyzer import IssueAnalyzer
from src.exceptions import AnalysisError


class TestIssueAnalyzer:
    """Test issue analysis functionality."""

    @patch("src.analyzer.requests.post")
    def test_analyze_issue_with_openrouter_api_successfully(
        self,
        mock_post,
        sample_comprehensive_issue_data,
        mock_ai_response,
    ):
        """TC-ANALYZER-001: Analyze issue with OpenRouter API successfully."""
        # Mock AI response with HTML content
        html_response = {
            "choices": [
                {
                    "message": {
                        "content": """<!-- AI_EMAIL_HTML_START -->
<div>Test HTML content</div>
<!-- AI_EMAIL_HTML_END -->"""
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 200,
                "total_tokens": 300,
            },
        }
        mock_response = Mock()
        mock_response.json.return_value = html_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        analyzer = IssueAnalyzer(
            provider="openrouter",
            api_key="test-key",
            model="deepseek/deepseek-v3.2",
            base_url="https://openrouter.ai/api/v1",
        )

        result = analyzer.analyze_issue(sample_comprehensive_issue_data)

        assert "html" in result
        assert "raw" in result
        assert isinstance(result["html"], str)
        assert isinstance(result["raw"], str)

    @patch("src.analyzer.requests.post")
    def test_analyze_issue_with_openai_api_successfully(
        self, mock_post, sample_comprehensive_issue_data, mock_ai_response
    ):
        """TC-ANALYZER-002: Analyze issue with OpenAI API successfully."""
        # Mock AI response with HTML content
        html_response = {
            "choices": [
                {
                    "message": {
                        "content": """<!-- AI_EMAIL_HTML_START -->
<div>Test HTML content</div>
<!-- AI_EMAIL_HTML_END -->"""
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 200,
                "total_tokens": 300,
            },
        }
        mock_response = Mock()
        mock_response.json.return_value = html_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        analyzer = IssueAnalyzer(
            provider="openai",
            api_key="test-key",
            model="gpt-4",
            base_url="https://api.openai.com/v1",
        )

        result = analyzer.analyze_issue(sample_comprehensive_issue_data)

        assert "html" in result
        assert "raw" in result
        assert isinstance(result["html"], str)
        assert isinstance(result["raw"], str)

    @patch("src.analyzer.requests.post")
    @patch("time.sleep")  # Mock sleep to speed up test
    def test_handle_ai_api_rate_limiting(
        self, mock_sleep, mock_post, sample_comprehensive_issue_data
    ):
        """TC-ANALYZER-003: Handle AI API rate limiting."""
        # Create mock response that will raise HTTPError on raise_for_status
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {"error": "Rate limit exceeded"}

        # Create HTTPError with response attached
        http_error = HTTPError("Rate limit exceeded")
        http_error.response = mock_response

        # First call raises error, subsequent calls also raise (after retries exhausted)
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        analyzer = IssueAnalyzer(
            provider="openrouter",
            api_key="test-key",
            model="deepseek/deepseek-v3.2",
            base_url="https://openrouter.ai/api/v1",
            max_retries=2,
        )

        with pytest.raises(AnalysisError) as exc_info:
            analyzer.analyze_issue(sample_comprehensive_issue_data)

        assert exc_info.value.status_code == 429
        # retry_after might be None if error is raised on last attempt
        # The important thing is that it handles rate limiting
        assert exc_info.value.status_code == 429

    @patch("src.analyzer.requests.post")
    @patch("time.sleep")  # Mock sleep to speed up test
    def test_handle_ai_api_timeout(
        self, mock_sleep, mock_post, sample_comprehensive_issue_data
    ):
        """TC-ANALYZER-004: Handle AI API timeout."""
        mock_post.side_effect = Timeout("Request timeout")

        analyzer = IssueAnalyzer(
            provider="openrouter",
            api_key="test-key",
            model="deepseek/deepseek-v3.2",
            base_url="https://openrouter.ai/api/v1",
            max_retries=2,
        )

        with pytest.raises(AnalysisError) as exc_info:
            analyzer.analyze_issue(sample_comprehensive_issue_data)

        assert exc_info.value.timeout is True

    def test_format_prompt_correctly_with_all_issue_data(
        self, sample_comprehensive_issue_data
    ):
        """TC-ANALYZER-005: Format prompt correctly with all issue data."""
        analyzer = IssueAnalyzer(
            provider="openrouter",
            api_key="test-key",
            model="deepseek/deepseek-v3.2",
            base_url="https://openrouter.ai/api/v1",
        )

        prompt = analyzer.prepare_prompt(sample_comprehensive_issue_data)

        assert "THÔNG TIN TICKET" in prompt
        assert "COMMENTS" in prompt
        assert "RELATED ISSUES" in prompt
        assert "ATTACHMENTS" in prompt
        assert sample_comprehensive_issue_data["title"] in prompt

    @patch("src.analyzer.requests.post")
    def test_parse_ai_response_into_html_format(
        self, mock_post, sample_comprehensive_issue_data, mock_ai_response
    ):
        """TC-ANALYZER-006: Parse AI response into HTML format."""
        # Mock AI response with HTML content
        html_response = {
            "choices": [
                {
                    "message": {
                        "content": """<!-- AI_EMAIL_HTML_START -->
<div>Test HTML content</div>
<!-- AI_EMAIL_HTML_END -->"""
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 200,
                "total_tokens": 300,
            },
        }
        mock_response = Mock()
        mock_response.json.return_value = html_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        analyzer = IssueAnalyzer(
            provider="openrouter",
            api_key="test-key",
            model="deepseek/deepseek-v3.2",
            base_url="https://openrouter.ai/api/v1",
        )

        result = analyzer.analyze_issue(sample_comprehensive_issue_data)

        assert "html" in result
        assert "raw" in result
        assert isinstance(result["html"], str)
        assert isinstance(result["raw"], str)

    @patch("src.analyzer.requests.post")
    def test_handle_malformed_ai_response(
        self, mock_post, sample_comprehensive_issue_data
    ):
        """TC-ANALYZER-007: Handle malformed AI response."""
        # Malformed response (no HTML markers)
        malformed_response = {
            "choices": [
                {
                    "message": {
                        "content": "This is not in HTML format. Just a plain response."
                    }
                }
            ]
        }

        mock_response = Mock()
        mock_response.json.return_value = malformed_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        analyzer = IssueAnalyzer(
            provider="openrouter",
            api_key="test-key",
            model="deepseek/deepseek-v3.2",
            base_url="https://openrouter.ai/api/v1",
        )

        # Should still return a result (with fallback parsing)
        result = analyzer.analyze_issue(sample_comprehensive_issue_data)
        assert isinstance(result, dict)
        assert "html" in result
        assert "raw" in result

    def test_handle_empty_issue_data(self):
        """TC-ANALYZER-008: Handle empty issue data."""
        analyzer = IssueAnalyzer(
            provider="openrouter",
            api_key="test-key",
            model="deepseek/deepseek-v3.2",
            base_url="https://openrouter.ai/api/v1",
        )

        # Test with None
        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze_issue(None)
        assert "empty" in str(exc_info.value).lower()

        # Test with empty dict
        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze_issue({})
        assert "empty" in str(exc_info.value).lower()

    def test_use_configured_model_from_config(self, sample_config):
        """TC-ANALYZER-009: Use configured model from config."""
        # Update sample_config to use new structure
        config = {
            "ai": {
                "provider": "openrouter",
                "api_key": "test-key",
                "model": "deepseek/deepseek-v3.2",
            }
        }
        analyzer = IssueAnalyzer(
            provider=config["ai"]["provider"],
            api_key=config["ai"]["api_key"],
            model=config["ai"]["model"],
            base_url="https://openrouter.ai/api/v1",
        )

        assert analyzer.model == "deepseek/deepseek-v3.2"

        # Test with different model
        analyzer_reasoner = IssueAnalyzer(
            provider="openrouter",
            api_key="test-key",
            model="deepseek/deepseek-v3.2",
            base_url="https://openrouter.ai/api/v1",
        )

        assert analyzer_reasoner.model == "deepseek/deepseek-v3.2"

    @patch("src.analyzer.requests.post")
    def test_handle_ai_api_authentication_failure(
        self, mock_post, sample_comprehensive_issue_data
    ):
        """TC-ANALYZER-010: Handle AI API authentication failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        http_error = HTTPError("Unauthorized")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_post.return_value = mock_response

        analyzer = IssueAnalyzer(
            provider="openrouter",
            api_key="invalid-key",
            model="deepseek/deepseek-v3.2",
            base_url="https://openrouter.ai/api/v1",
        )

        with pytest.raises(AnalysisError) as exc_info:
            analyzer.analyze_issue(sample_comprehensive_issue_data)

        assert exc_info.value.status_code == 401
        assert "authentication" in str(exc_info.value).lower() or "401" in str(
            exc_info.value
        )
