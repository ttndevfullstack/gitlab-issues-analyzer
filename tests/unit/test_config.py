"""
Unit tests for config module.

Test cases:
- TC-CONFIG-001: Load configuration from environment variables
- TC-CONFIG-002: Load configuration from environment variables
- TC-CONFIG-003: Environment variables override config file
- TC-CONFIG-004: Use default values when config is missing
- TC-CONFIG-005: Raise error for missing required configuration
- TC-CONFIG-006: Validate GitLab URL format
- TC-CONFIG-007: Validate SMTP port is integer
"""

import json
import os
from pathlib import Path

import pytest

from src.config import load_config, validate_config
from src.exceptions import ConfigurationError


class TestConfigLoading:
    """Test configuration loading from various sources."""

    def test_load_config_from_environment_variables(self, sample_config, monkeypatch):
        """TC-CONFIG-001: Load configuration from environment variables."""
        # Set environment variables
        monkeypatch.setenv("GITLAB_URL", "https://gitlab.com")
        monkeypatch.setenv("GITLAB_TOKEN", "test-token-123")
        monkeypatch.setenv("GITLAB_PROJECT_ID", "123456")
        monkeypatch.setenv("AI_API_KEY", "test-api-key-123")
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USERNAME", "test@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "test@example.com")
        monkeypatch.setenv("SMTP_TO_EMAIL", "recipient@example.com")

        # Load config (should use environment variables)
        config = load_config()

        assert config["gitlab"]["url"] == "https://gitlab.com"
        assert config["gitlab"]["token"] == "test-token-123"
        assert config["gitlab"]["project_id"] == "123456"

    def test_load_config_from_json_file(self, sample_config, tmp_path, monkeypatch):
        """TC-CONFIG-002: Load configuration from environment variables (config.json support removed)."""
        # Set environment variables (config.json support was removed)
        monkeypatch.setenv("GITLAB_URL", sample_config["gitlab"]["url"])
        monkeypatch.setenv("GITLAB_TOKEN", "test-token")
        monkeypatch.setenv("AI_API_KEY", "test-key")
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USERNAME", "test@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "test@example.com")
        monkeypatch.setenv("SMTP_TO_EMAIL", "recipient@example.com")

        config = load_config()

        assert config["gitlab"]["url"] == sample_config["gitlab"]["url"]

    def test_environment_variables_are_used(self, sample_config, monkeypatch):
        """TC-CONFIG-003: Environment variables are used for configuration."""
        # Set environment variables
        monkeypatch.setenv("GITLAB_URL", "https://new-gitlab.com")
        monkeypatch.setenv("GITLAB_TOKEN", "test-token")
        monkeypatch.setenv("GITLAB_PROJECT_ID", "123456")
        monkeypatch.setenv("AI_API_KEY", "test-key")
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USERNAME", "test@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "test@example.com")
        monkeypatch.setenv("SMTP_TO_EMAIL", "recipient@example.com")

        config = load_config()

        # Environment variable should be used
        assert config["gitlab"]["url"] == "https://new-gitlab.com"

    def test_use_default_values_when_config_missing(self, monkeypatch):
        """TC-CONFIG-004: Use default values when config is missing."""
        # Clear all environment variables
        for key in list(os.environ.keys()):
            if key.startswith(("GITLAB_", "AI_", "SMTP_", "APP_")):
                monkeypatch.delenv(key, raising=False)

        # Load config (will use defaults for optional settings)
        config = load_config()

        # Check defaults
        assert config["app"]["poll_interval"] == 900
        assert config["app"]["log_level"] == "INFO"
        assert config["ai"]["provider"] == "openrouter"
        assert config["smtp"]["port"] == 587

    def test_raise_error_for_missing_required_config(self, monkeypatch):
        """TC-CONFIG-005: Raise error for missing required configuration."""
        # Clear all environment variables
        for key in list(os.environ.keys()):
            if key.startswith(("GITLAB_", "AI_", "SMTP_", "APP_")):
                monkeypatch.delenv(key, raising=False)

        config = load_config()

        # Should raise error when validating (required settings missing)
        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(config)

        assert "GITLAB_TOKEN" in str(exc_info.value) or "gitlab.token" in str(
            exc_info.value
        )

    def test_validate_gitlab_url_format(self, sample_config):
        """TC-CONFIG-006: Validate GitLab URL format."""
        # Valid URL - need to add required AI_API_KEY
        valid_config = sample_config.copy()
        valid_config["gitlab"]["url"] = "https://gitlab.com"
        valid_config["ai"]["api_key"] = "test-key"

        # Should not raise
        validate_config(valid_config)

        # Invalid URL
        invalid_config = sample_config.copy()
        invalid_config["gitlab"]["url"] = "not-a-url"

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(invalid_config)

        assert "URL" in str(exc_info.value)

    def test_validate_smtp_port_is_integer(self, sample_config):
        """TC-CONFIG-007: Validate SMTP port is integer."""
        # Valid port - need to add required AI_API_KEY
        valid_config = sample_config.copy()
        valid_config["smtp"]["port"] = 587
        valid_config["ai"]["api_key"] = "test-key"

        # Should not raise
        validate_config(valid_config)

        # Invalid port (string)
        invalid_config = sample_config.copy()
        invalid_config["smtp"]["port"] = "not-a-number"

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(invalid_config)

        assert "port" in str(exc_info.value).lower()
