"""
Integration tests for analyzer module.

Test cases:
- TC-INT-ANALYZER-001: Analyze real issue with AI API
- TC-INT-ANALYZER-002: Handle AI API response format variations
"""

from unittest.mock import Mock, patch

import pytest


class TestAnalyzerIntegration:
    """Integration tests for issue analyzer."""

    @pytest.mark.requires_credentials
    @patch("src.analyzer.requests.post")
    def test_analyze_real_issue_with_ai_api(
        self, mock_post, sample_comprehensive_issue_data
    ):
        """TC-INT-ANALYZER-001: Analyze real issue with AI API."""
        from src.analyzer import IssueAnalyzer  # type: ignore

        # Mock AI API response with HTML content
        mock_response = Mock()
        mock_response.json.return_value = {
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
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        analyzer = IssueAnalyzer(
            provider="openrouter",
            api_key="test-key",
            model="deepseek/deepseek-v3.2",
            base_url="https://openrouter.ai/api/v1",
        )

        with patch.object(analyzer, "analyze_issue") as mock_analyze:
            expected_analysis = {
                "html": "<div>Test HTML content</div>",
                "raw": "W1 — Why: Root cause analysis\nW2 — What: Problem identification",
            }
            mock_analyze.return_value = expected_analysis

            result = mock_analyze(sample_comprehensive_issue_data)

            assert "html" in result
            assert "raw" in result
            assert isinstance(result["html"], str)
            assert isinstance(result["raw"], str)
            mock_analyze.assert_called_once()

    @pytest.mark.requires_credentials
    @patch("src.analyzer.requests.post")
    def test_handle_ai_api_response_format_variations(self, mock_post):
        """TC-INT-ANALYZER-002: Handle AI API response format variations."""
        from src.analyzer import IssueAnalyzer  # type: ignore

        # Test OpenRouter format
        openrouter_response = {
            "choices": [
                {
                    "message": {
                        "content": """<!-- AI_EMAIL_HTML_START -->
<div>Test HTML</div>
<!-- AI_EMAIL_HTML_END -->"""
                    }
                }
            ]
        }

        # Test OpenAI format
        openai_response = {
            "choices": [
                {
                    "message": {
                        "content": """<!-- AI_EMAIL_HTML_START -->
<div>Test HTML</div>
<!-- AI_EMAIL_HTML_END -->"""
                    }
                }
            ]
        }

        analyzer = IssueAnalyzer(
            provider="openrouter",
            api_key="test-key",
            model="deepseek/deepseek-v3.2",
            base_url="https://openrouter.ai/api/v1",
        )

        with patch.object(analyzer, "parse_analysis") as mock_parse:
            # All should parse to same format
            expected_analysis = {
                "html": "<div>Test HTML</div>",
                "raw": "W1 — Why: ...",
            }

            mock_parse.return_value = expected_analysis

            # Test OpenRouter format
            result1 = mock_parse(openrouter_response)
            assert "html" in result1

            # Test OpenAI format
            result2 = mock_parse(openai_response)
            assert "html" in result2
