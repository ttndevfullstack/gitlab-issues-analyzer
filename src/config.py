"""
Configuration management for GitLab Issues Analyzer.

This module handles loading and validating configuration from environment variables.
Configuration is loaded from .env file or environment variables (recommended for Docker).
"""

import os
import re
from typing import Any, Dict

from dotenv import load_dotenv

from src.exceptions import ConfigurationError

# Load .env file if it exists (for local development)
load_dotenv()


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables only.

    Configuration priority:
    1. Environment variables (from .env file or system environment)
    2. Default values (for optional settings)

    All configuration must be provided via environment variables.
    Use a .env file for local development or set environment variables directly.

    Returns:
        Configuration dictionary

    Raises:
        ConfigurationError: If required configuration is missing
    """
    # Start with defaults
    config = _get_default_config()

    # Load from environment variables (overrides defaults)
    env_config = _load_from_environment()
    config = _merge_config(config, env_config)

    return config


def _get_default_config() -> Dict[str, Any]:
    """Get default configuration values."""
    return {
        "gitlab": {
            "url": None,
            "token": None,
            "project_id": None,  # Optional - if None, uses global /api/v4/issues endpoint
            "webhook_secret": None,
            "issue_filter": {  # For global endpoint filtering
                "scope": None,  # e.g., "all", "assigned_to_me", "created_by_me"
                "labels": None,  # e.g., ["UNIOSS 3", "bug"]
            },
        },
        "ai": {
            "provider": "openrouter",  # Default to OpenRouter for DeepSeek
            "api_key": None,
            "model": "deepseek/deepseek-v3.2",  # OpenRouter model format
            "base_url": None,  # Will be set based on provider
            "temperature": 0.7,
            "max_tokens": 2000,
            "enable_reasoning": True,  # Enable deepthink mode for DeepSeek
        },
        "smtp": {
            "host": None,
            "port": 587,
            "username": None,
            "password": None,
            "from_email": None,
            "to_email": None,
            "use_tls": True,
            "use_ssl": False,
            "subject_prefix": "[GitLab Issue Analysis]",
        },
        "app": {
            "environment": "production",  # production, development, testing
            "mode": "poll",
            "poll_interval": 900,
            "webhook_port": 8000,
            "webhook_host": "0.0.0.0",
            "log_level": "INFO",
            "processed_issues_file": None,
            "max_retries": 3,
            "retry_backoff": 2.0,
            "max_issues_per_poll": None,  # Limit number of issues to process per poll (for testing)
            "enable_automation": True,  # Enable/disable automated polling/webhook processing
            "timezone": "Asia/Ho_Chi_Minh",  # Default to Vietnam timezone
            "version": "0.1.0",  # Application version
        },
    }


def _load_from_environment() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {}

    # GitLab configuration
    if os.getenv("GITLAB_URL"):
        config.setdefault("gitlab", {})["url"] = os.getenv("GITLAB_URL")
    if os.getenv("GITLAB_TOKEN"):
        config.setdefault("gitlab", {})["token"] = os.getenv("GITLAB_TOKEN")
    if os.getenv("GITLAB_PROJECT_ID"):
        config.setdefault("gitlab", {})["project_id"] = os.getenv("GITLAB_PROJECT_ID")
    if os.getenv("GITLAB_WEBHOOK_SECRET"):
        config.setdefault("gitlab", {})["webhook_secret"] = os.getenv(
            "GITLAB_WEBHOOK_SECRET"
        )

    # Issue filter configuration (for global endpoint)
    if os.getenv("GITLAB_ISSUE_SCOPE"):
        config.setdefault("gitlab", {}).setdefault("issue_filter", {})["scope"] = (
            os.getenv("GITLAB_ISSUE_SCOPE")
        )
    if os.getenv("GITLAB_ISSUE_LABELS"):
        # Support comma-separated labels
        labels_str = os.getenv("GITLAB_ISSUE_LABELS")
        if labels_str:
            config.setdefault("gitlab", {}).setdefault("issue_filter", {})["labels"] = [
                label.strip() for label in labels_str.split(",")
            ]

    # AI Provider configuration
    if os.getenv("AI_PROVIDER"):
        config.setdefault("ai", {})["provider"] = os.getenv("AI_PROVIDER")
    if os.getenv("AI_API_KEY"):
        config.setdefault("ai", {})["api_key"] = os.getenv("AI_API_KEY")
    if os.getenv("AI_MODEL"):
        config.setdefault("ai", {})["model"] = os.getenv("AI_MODEL")
    if os.getenv("AI_BASE_URL"):
        config.setdefault("ai", {})["base_url"] = os.getenv("AI_BASE_URL")
    if os.getenv("AI_TEMPERATURE"):
        try:
            config.setdefault("ai", {})["temperature"] = float(
                os.getenv("AI_TEMPERATURE")
            )
        except ValueError:
            pass
    if os.getenv("AI_MAX_TOKENS"):
        try:
            config.setdefault("ai", {})["max_tokens"] = int(os.getenv("AI_MAX_TOKENS"))
        except ValueError:
            pass
    if os.getenv("AI_ENABLE_REASONING"):
        config.setdefault("ai", {})["enable_reasoning"] = os.getenv(
            "AI_ENABLE_REASONING"
        ).lower() in ("true", "1", "yes")

    # SMTP configuration
    if os.getenv("SMTP_HOST"):
        config.setdefault("smtp", {})["host"] = os.getenv("SMTP_HOST")
    if os.getenv("SMTP_PORT"):
        try:
            config.setdefault("smtp", {})["port"] = int(os.getenv("SMTP_PORT"))
        except ValueError:
            pass
    if os.getenv("SMTP_USERNAME"):
        config.setdefault("smtp", {})["username"] = os.getenv("SMTP_USERNAME")
    if os.getenv("SMTP_PASSWORD"):
        config.setdefault("smtp", {})["password"] = os.getenv("SMTP_PASSWORD")
    if os.getenv("SMTP_FROM_EMAIL"):
        config.setdefault("smtp", {})["from_email"] = os.getenv("SMTP_FROM_EMAIL")
    if os.getenv("SMTP_TO_EMAIL"):
        # Support comma-separated or single email
        to_email = os.getenv("SMTP_TO_EMAIL")
        if "," in to_email:
            config.setdefault("smtp", {})["to_email"] = [
                e.strip() for e in to_email.split(",")
            ]
        else:
            config.setdefault("smtp", {})["to_email"] = to_email
    if os.getenv("SMTP_USE_TLS"):
        config.setdefault("smtp", {})["use_tls"] = os.getenv(
            "SMTP_USE_TLS"
        ).lower() in ("true", "1", "yes")
    if os.getenv("SMTP_USE_SSL"):
        config.setdefault("smtp", {})["use_ssl"] = os.getenv(
            "SMTP_USE_SSL"
        ).lower() in ("true", "1", "yes")

    # Application configuration
    if os.getenv("APP_ENVIRONMENT") or os.getenv("ENVIRONMENT"):
        # Support both APP_ENVIRONMENT and ENVIRONMENT for flexibility
        env_value = os.getenv("APP_ENVIRONMENT") or os.getenv("ENVIRONMENT")
        config.setdefault("app", {})["environment"] = env_value.lower()
    if os.getenv("APP_MODE"):
        config.setdefault("app", {})["mode"] = os.getenv("APP_MODE")
    if os.getenv("POLL_INTERVAL"):
        try:
            config.setdefault("app", {})["poll_interval"] = int(
                os.getenv("POLL_INTERVAL")
            )
        except ValueError:
            pass
    if os.getenv("WEBHOOK_PORT"):
        try:
            config.setdefault("app", {})["webhook_port"] = int(
                os.getenv("WEBHOOK_PORT")
            )
        except ValueError:
            pass
    if os.getenv("WEBHOOK_HOST"):
        config.setdefault("app", {})["webhook_host"] = os.getenv("WEBHOOK_HOST")
    if os.getenv("LOG_LEVEL"):
        config.setdefault("app", {})["log_level"] = os.getenv("LOG_LEVEL")
    if os.getenv("PROCESSED_ISSUES_FILE"):
        config.setdefault("app", {})["processed_issues_file"] = os.getenv(
            "PROCESSED_ISSUES_FILE"
        )
    if os.getenv("MAX_RETRIES"):
        try:
            config.setdefault("app", {})["max_retries"] = int(os.getenv("MAX_RETRIES"))
        except ValueError:
            pass
    if os.getenv("RETRY_BACKOFF"):
        try:
            config.setdefault("app", {})["retry_backoff"] = float(
                os.getenv("RETRY_BACKOFF")
            )
        except ValueError:
            pass
    if os.getenv("MAX_ISSUES_PER_POLL"):
        try:
            config.setdefault("app", {})["max_issues_per_poll"] = int(
                os.getenv("MAX_ISSUES_PER_POLL")
            )
        except ValueError:
            pass
    if os.getenv("ENABLE_AUTOMATION") or os.getenv("AUTOMATION_ENABLED"):
        # Support both ENABLE_AUTOMATION and AUTOMATION_ENABLED
        automation_value = os.getenv("ENABLE_AUTOMATION") or os.getenv(
            "AUTOMATION_ENABLED"
        )
        config.setdefault("app", {})[
            "enable_automation"
        ] = automation_value.lower() in (
            "true",
            "1",
            "yes",
        )
    if os.getenv("TIMEZONE"):
        config.setdefault("app", {})["timezone"] = os.getenv("TIMEZONE")
    if os.getenv("APP_VERSION") or os.getenv("VERSION"):
        # Support both APP_VERSION and VERSION for flexibility
        version_value = os.getenv("APP_VERSION") or os.getenv("VERSION")
        config.setdefault("app", {})["version"] = version_value

    return config


def _merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge override configuration into base configuration.

    Args:
        base: Base configuration dictionary
        override: Override configuration dictionary

    Returns:
        Merged configuration dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value

    return result


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration and raise errors for invalid values.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigurationError: If configuration is invalid
    """
    errors = []

    # Validate GitLab configuration
    gitlab = config.get("gitlab", {})
    if not gitlab.get("url"):
        errors.append("Missing required configuration: gitlab.url (or GITLAB_URL)")
    elif not _is_valid_url(gitlab["url"]):
        errors.append(f"Invalid GitLab URL format: {gitlab['url']}")

    if not gitlab.get("token"):
        errors.append("Missing required configuration: gitlab.token (or GITLAB_TOKEN)")

    # project_id is optional - if not provided, uses global /api/v4/issues endpoint
    # In that case, issue_filter should be configured
    if not gitlab.get("project_id"):
        issue_filter = gitlab.get("issue_filter", {})
        if not issue_filter.get("scope") and not issue_filter.get("labels"):
            errors.append(
                "When project_id is not set, you must configure issue_filter.scope "
                "(e.g., 'all') or issue_filter.labels (e.g., ['UNIOSS 3']) "
                "to filter issues from the global endpoint"
            )

    # Validate AI provider configuration
    ai = config.get("ai", {})
    if not ai.get("api_key"):
        errors.append("Missing required configuration: ai.api_key (or AI_API_KEY)")

    provider = ai.get("provider", "openrouter")

    # Auto-migrate deprecated providers
    if provider == "deepseek":
        # Migrate deepseek to openrouter with appropriate model
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(
            "Provider 'deepseek' is deprecated. Auto-migrating to 'openrouter' with model 'deepseek/deepseek-v3.2'. "
            "Please update your environment variables to use 'openrouter' provider."
        )
        ai["provider"] = "openrouter"
        if ai.get("model") in ["deepseek-chat", "deepseek-reasoner"]:
            ai["model"] = "deepseek/deepseek-v3.2"
        elif not ai.get("model") or ai.get("model") == "deepseek-chat":
            ai["model"] = "deepseek/deepseek-v3.2"
        if ai.get("base_url") == "https://api.deepseek.com/v1":
            ai["base_url"] = "https://openrouter.ai/api/v1"
        if ai.get("enable_reasoning") is None:
            ai["enable_reasoning"] = True
        provider = "openrouter"

    if provider not in ["openrouter", "openai"]:
        errors.append(
            f"Invalid AI provider: {provider}. Must be one of: openrouter, openai"
        )

    # Set default base_url based on provider if not specified
    if not ai.get("base_url"):
        base_urls = {
            "openrouter": "https://openrouter.ai/api/v1",
            "openai": "https://api.openai.com/v1",
        }
        if provider in base_urls:
            ai["base_url"] = base_urls[provider]

    # Validate temperature
    temperature = ai.get("temperature", 0.7)
    if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
        errors.append(
            f"Invalid temperature: {temperature}. Must be between 0.0 and 2.0"
        )

    # Validate max_tokens
    max_tokens = ai.get("max_tokens", 2000)
    if not isinstance(max_tokens, int) or max_tokens < 1:
        errors.append(f"Invalid max_tokens: {max_tokens}. Must be a positive integer")

    # Validate SMTP configuration
    smtp = config.get("smtp", {})
    if not smtp.get("host"):
        errors.append("Missing required configuration: smtp.host (or SMTP_HOST)")

    port = smtp.get("port")
    if port is None:
        errors.append("Missing required configuration: smtp.port (or SMTP_PORT)")
    elif not isinstance(port, int) or port < 1 or port > 65535:
        errors.append(
            f"Invalid SMTP port: {port}. Must be an integer between 1 and 65535"
        )

    if not smtp.get("username"):
        errors.append(
            "Missing required configuration: smtp.username (or SMTP_USERNAME)"
        )

    if not smtp.get("password"):
        errors.append(
            "Missing required configuration: smtp.password (or SMTP_PASSWORD)"
        )

    if not smtp.get("from_email"):
        errors.append(
            "Missing required configuration: smtp.from_email (or SMTP_FROM_EMAIL)"
        )
    elif not _is_valid_email(smtp["from_email"]):
        errors.append(f"Invalid from_email format: {smtp['from_email']}")

    if not smtp.get("to_email"):
        errors.append(
            "Missing required configuration: smtp.to_email (or SMTP_TO_EMAIL)"
        )
    else:
        to_email = smtp["to_email"]
        if isinstance(to_email, str):
            if not _is_valid_email(to_email):
                errors.append(f"Invalid to_email format: {to_email}")
        elif isinstance(to_email, list):
            for email in to_email:
                if not _is_valid_email(email):
                    errors.append(f"Invalid to_email format: {email}")
        else:
            errors.append("to_email must be a string or list of strings")

    # Validate use_tls and use_ssl
    if not isinstance(smtp.get("use_tls", True), bool):
        errors.append("smtp.use_tls must be a boolean")
    if not isinstance(smtp.get("use_ssl", False), bool):
        errors.append("smtp.use_ssl must be a boolean")

    # Validate application configuration
    app = config.get("app", {})

    # Validate environment
    environment = app.get("environment", "production")
    if environment not in ["production", "development", "testing"]:
        errors.append(
            f"Invalid app.environment: {environment}. Must be one of: production, development, testing"
        )

    # Apply environment-specific defaults (only if no errors so far)
    if not errors:
        if environment == "testing":
            # Testing mode: limit to 1 issue, shorter poll interval, debug logging
            if app.get("max_issues_per_poll") is None:
                app["max_issues_per_poll"] = 1
            if app.get("log_level") == "INFO":
                app["log_level"] = "DEBUG"
            if app.get("poll_interval", 900) > 300:
                app["poll_interval"] = 60  # 1 minute for testing
        elif environment == "development":
            # Development mode: debug logging, shorter poll interval
            if app.get("log_level") == "INFO":
                app["log_level"] = "DEBUG"
            if app.get("poll_interval", 900) > 300:
                app["poll_interval"] = 300  # 5 minutes for development

    mode = app.get("mode", "poll")
    if mode not in ["webhook", "poll"]:
        errors.append(f"Invalid app.mode: {mode}. Must be 'webhook' or 'poll'")

    if mode == "webhook" and not gitlab.get("webhook_secret"):
        errors.append(
            "Missing required configuration for webhook mode: gitlab.webhook_secret (or GITLAB_WEBHOOK_SECRET)"
        )

    poll_interval = app.get("poll_interval", 900)
    if not isinstance(poll_interval, int) or poll_interval < 1:
        errors.append(
            f"Invalid poll_interval: {poll_interval}. Must be a positive integer"
        )

    webhook_port = app.get("webhook_port", 8000)
    if not isinstance(webhook_port, int) or webhook_port < 1 or webhook_port > 65535:
        errors.append(
            f"Invalid webhook_port: {webhook_port}. Must be an integer between 1 and 65535"
        )

    log_level = app.get("log_level", "INFO")
    if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        errors.append(
            f"Invalid log_level: {log_level}. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
        )

    max_retries = app.get("max_retries", 3)
    if not isinstance(max_retries, int) or max_retries < 0:
        errors.append(
            f"Invalid max_retries: {max_retries}. Must be a non-negative integer"
        )

    retry_backoff = app.get("retry_backoff", 2.0)
    if not isinstance(retry_backoff, (int, float)) or retry_backoff < 0:
        errors.append(
            f"Invalid retry_backoff: {retry_backoff}. Must be a non-negative number"
        )

    # Raise errors if any found
    if errors:
        error_message = "Configuration validation failed:\n" + "\n".join(
            f"  - {error}" for error in errors
        )
        raise ConfigurationError(error_message)


def _is_valid_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL string to validate

    Returns:
        True if URL is valid, False otherwise
    """
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return url_pattern.match(url) is not None


def _is_valid_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email string to validate

    Returns:
        True if email is valid, False otherwise
    """
    email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    return email_pattern.match(email) is not None
