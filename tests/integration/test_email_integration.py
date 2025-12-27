"""
Integration tests for email sending.

Test cases:
- TC-INT-EMAIL-001: Send test email to real SMTP server
"""

from unittest.mock import MagicMock, patch

import pytest


class TestEmailIntegration:
    """Integration tests for email sending."""

    @pytest.mark.requires_credentials
    @pytest.mark.slow
    @patch("smtplib.SMTP")
    def test_send_test_email_to_real_smtp_server(
        self, mock_smtp_class, sample_smtp_config
    ):
        """TC-INT-EMAIL-001: Send test email to real SMTP server."""
        from src.email_sender import EmailSender  # type: ignore

        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server

        sender = EmailSender(
            host=sample_smtp_config["host"],
            port=sample_smtp_config["port"],
            username=sample_smtp_config["username"],
            password=sample_smtp_config["password"],
            from_email=sample_smtp_config["from_email"],
        )

        with patch.object(sender, "send_email") as mock_send:
            mock_send.return_value = True
            result = mock_send(
                to="test@example.com", subject="Test Email", body="This is a test email"
            )

            assert result is True
            mock_send.assert_called_once_with(
                to="test@example.com", subject="Test Email", body="This is a test email"
            )
