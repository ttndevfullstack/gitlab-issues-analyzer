"""
Unit tests for email_sender module.

Test cases:
- TC-EMAIL-001: Send email successfully
- TC-EMAIL-002: Handle SMTP authentication failure
- TC-EMAIL-003: Handle SMTP connection timeout
- TC-EMAIL-004: Retry email sending on transient failure
- TC-EMAIL-005: Send to multiple recipients
- TC-EMAIL-006: Handle invalid email address format
- TC-EMAIL-007: Use TLS/SSL when configured
"""

import smtplib
from smtplib import SMTPAuthenticationError, SMTPException
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.email_sender import EmailSender
from src.exceptions import EmailError


class TestEmailSender:
    """Test email sending functionality."""

    @patch("smtplib.SMTP")
    def test_send_email_successfully(
        self, mock_smtp_class, sample_smtp_config, mock_smtp_server
    ):
        """TC-EMAIL-001: Send email successfully."""
        mock_smtp_class.return_value = mock_smtp_server

        sender = EmailSender(
            host=sample_smtp_config["host"],
            port=sample_smtp_config["port"],
            username=sample_smtp_config["username"],
            password=sample_smtp_config["password"],
            from_email=sample_smtp_config["from_email"],
        )

        result = sender.send_email(
            to="recipient@example.com", subject="Test Subject", body="Test body"
        )

        assert result is True
        mock_smtp_server.login.assert_called_once()
        mock_smtp_server.sendmail.assert_called_once()

    @patch("smtplib.SMTP")
    def test_handle_smtp_authentication_failure(
        self, mock_smtp_class, sample_smtp_config
    ):
        """TC-EMAIL-002: Handle SMTP authentication failure."""
        mock_server = MagicMock()
        mock_server.login.side_effect = SMTPAuthenticationError(
            535, "Authentication failed"
        )
        mock_smtp_class.return_value = mock_server

        sender = EmailSender(
            host=sample_smtp_config["host"],
            port=sample_smtp_config["port"],
            username=sample_smtp_config["username"],
            password="wrong-password",
            from_email=sample_smtp_config["from_email"],
        )

        with pytest.raises(EmailError) as exc_info:
            sender.send_email(
                to="recipient@example.com", subject="Test Subject", body="Test body"
            )

        assert "authentication" in str(exc_info.value).lower()

    @patch("smtplib.SMTP")
    def test_handle_smtp_connection_timeout(self, mock_smtp_class, sample_smtp_config):
        """TC-EMAIL-003: Handle SMTP connection timeout."""
        mock_smtp_class.side_effect = TimeoutError("Connection timeout")

        sender = EmailSender(
            host=sample_smtp_config["host"],
            port=sample_smtp_config["port"],
            username=sample_smtp_config["username"],
            password=sample_smtp_config["password"],
            from_email=sample_smtp_config["from_email"],
        )

        with pytest.raises(EmailError) as exc_info:
            sender.send_email(
                to="recipient@example.com", subject="Test Subject", body="Test body"
            )

        assert "timeout" in str(exc_info.value).lower()

    @patch("smtplib.SMTP")
    @patch("time.sleep")  # Mock sleep to speed up test
    def test_retry_email_sending_on_transient_failure(
        self, mock_sleep, mock_smtp_class, sample_smtp_config
    ):
        """TC-EMAIL-004: Retry email sending on transient failure."""
        # First call fails, second succeeds
        mock_server_fail = MagicMock()
        mock_server_fail.sendmail.side_effect = SMTPException("Temporary network error")

        mock_server_success = MagicMock()
        mock_server_success.sendmail.return_value = {}

        mock_smtp_class.side_effect = [mock_server_fail, mock_server_success]

        sender = EmailSender(
            host=sample_smtp_config["host"],
            port=sample_smtp_config["port"],
            username=sample_smtp_config["username"],
            password=sample_smtp_config["password"],
            from_email=sample_smtp_config["from_email"],
            max_retries=3,
        )

        # Should retry and eventually succeed
        result = sender.send_email(
            to="recipient@example.com", subject="Test Subject", body="Test body"
        )

        assert result is True
        assert mock_smtp_class.call_count == 2

    @patch("smtplib.SMTP")
    def test_send_to_multiple_recipients(
        self, mock_smtp_class, sample_smtp_config, mock_smtp_server
    ):
        """TC-EMAIL-005: Send to multiple recipients."""
        mock_smtp_class.return_value = mock_smtp_server

        sender = EmailSender(
            host=sample_smtp_config["host"],
            port=sample_smtp_config["port"],
            username=sample_smtp_config["username"],
            password=sample_smtp_config["password"],
            from_email=sample_smtp_config["from_email"],
        )

        recipients = ["recipient1@example.com", "recipient2@example.com"]

        result = sender.send_email(
            to=recipients, subject="Test Subject", body="Test body"
        )

        assert result is True
        # Verify sendmail was called with list of recipients
        call_args = mock_smtp_server.sendmail.call_args
        assert call_args is not None
        assert call_args[0][1] == recipients

    def test_handle_invalid_email_address_format(self, sample_smtp_config):
        """TC-EMAIL-006: Handle invalid email address format."""
        sender = EmailSender(
            host=sample_smtp_config["host"],
            port=sample_smtp_config["port"],
            username=sample_smtp_config["username"],
            password=sample_smtp_config["password"],
            from_email=sample_smtp_config["from_email"],
        )

        with pytest.raises(ValueError) as exc_info:
            sender.send_email(
                to="invalid-email-format", subject="Test Subject", body="Test body"
            )

        assert (
            "email" in str(exc_info.value).lower()
            or "format" in str(exc_info.value).lower()
        )

    @patch("smtplib.SMTP")
    def test_use_tls_when_configured(
        self, mock_smtp_class, sample_smtp_config, mock_smtp_server
    ):
        """TC-EMAIL-007: Use TLS/SSL when configured."""
        mock_smtp_class.return_value = mock_smtp_server

        # Config with TLS enabled
        sender = EmailSender(
            host=sample_smtp_config["host"],
            port=sample_smtp_config["port"],
            username=sample_smtp_config["username"],
            password=sample_smtp_config["password"],
            from_email=sample_smtp_config["from_email"],
            use_tls=True,
        )

        sender.send_email(
            to="recipient@example.com", subject="Test Subject", body="Test body"
        )

        # Verify starttls was called (for TLS)
        if not sample_smtp_config.get("use_ssl", False):
            mock_smtp_server.starttls.assert_called_once()
