"""
Email sender module for sending analysis reports via SMTP.

This module handles SMTP connections, email composition, and sending
with retry logic and error handling.
"""

import re
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPAuthenticationError, SMTPException
from typing import List, Optional, Union

from src.exceptions import EmailError


class EmailSender:
    """
    Email sender for sending analysis reports via SMTP.

    Supports TLS/SSL encryption, multiple recipients, and retry logic.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True,
        use_ssl: bool = False,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
    ):
        """
        Initialize email sender.

        Args:
            host: SMTP server hostname
            port: SMTP server port
            username: SMTP username (usually email address)
            password: SMTP password or app password
            from_email: Sender email address
            use_tls: Use TLS encryption (default: True)
            use_ssl: Use SSL encryption (default: False, for port 465)
            timeout: Connection timeout in seconds (default: 30)
            max_retries: Maximum retry attempts (default: 3)
            retry_backoff: Exponential backoff multiplier (default: 2.0)
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

    def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> bool:
        """
        Send email with retry logic.

        Args:
            to: Recipient email address(es) - string or list of strings
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body

        Returns:
            True if email sent successfully

        Raises:
            EmailError: If email sending fails after retries
            ValueError: If email address format is invalid
        """
        # Normalize recipients to list
        if isinstance(to, str):
            recipients = [to]
        else:
            recipients = to

        # Validate email addresses
        for email in recipients:
            if not self._is_valid_email(email):
                raise ValueError(f"Invalid email address format: {email}")

        # Create email message
        msg = self._create_message(recipients, subject, body, html_body)

        # Send with retry logic
        return self._send_with_retry(recipients, msg)

    def _create_message(
        self, recipients: List[str], subject: str, body: str, html_body: Optional[str]
    ) -> MIMEMultipart:
        """
        Create email message.

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body

        Returns:
            MIMEMultipart message object
        """
        if html_body:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
        else:
            msg = MIMEText(body, "plain")

        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = ", ".join(recipients)

        return msg

    def _send_with_retry(self, recipients: List[str], msg: MIMEMultipart) -> bool:
        """
        Send email with retry logic and exponential backoff.

        Args:
            recipients: List of recipient email addresses
            msg: Email message object

        Returns:
            True if sent successfully

        Raises:
            EmailError: If sending fails after all retries
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return self._send_email_once(recipients, msg)

            except SMTPAuthenticationError as e:
                # Don't retry authentication errors
                raise EmailError(f"SMTP authentication failed: {e}", smtp_error=e)

            except (SMTPException, OSError, TimeoutError) as e:
                last_error = e

                # Don't retry on last attempt
                if attempt == self.max_retries - 1:
                    break

                # Wait before retry with exponential backoff
                wait_time = self.retry_backoff**attempt
                time.sleep(wait_time)

        # All retries failed
        error_msg = f"Failed to send email after {self.max_retries} attempts"
        if last_error:
            error_msg += f": {last_error}"

        raise EmailError(error_msg, smtp_error=last_error)

    def _send_email_once(self, recipients: List[str], msg: MIMEMultipart) -> bool:
        """
        Send email once (single attempt).

        Args:
            recipients: List of recipient email addresses
            msg: Email message object

        Returns:
            True if sent successfully

        Raises:
            SMTPException: If sending fails
            OSError: If connection fails
            TimeoutError: If connection times out
        """
        if self.use_ssl:
            # SSL connection (typically port 465)
            server = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout)
        else:
            # Regular connection (typically port 587)
            server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)

        try:
            # Start TLS if configured
            if self.use_tls and not self.use_ssl:
                server.starttls()

            # Login
            server.login(self.username, self.password)

            # Send email
            server.sendmail(self.from_email, recipients, msg.as_string())

            return True

        finally:
            # Always close connection
            try:
                server.quit()
            except Exception:
                pass  # Ignore errors during cleanup

    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            True if email format is valid, False otherwise
        """
        pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        return pattern.match(email) is not None
