#!/usr/bin/env python3
"""
GitLab Issues Analyzer - Main Entry Point

This is the main entry point for the GitLab Issues Analyzer application.
It supports both webhook and polling modes for detecting new GitLab issues.
"""

import argparse
import logging
import re
import signal
import sys
from datetime import datetime
from threading import Event, Thread
from typing import Any, Dict, List, Optional, Union

import pytz
from flask import Flask, jsonify, render_template, request

from src.analysis_cache import AnalysisCache
from src.analyzer import IssueAnalyzer
from src.config import load_config, validate_config
from src.email_sender import EmailSender
from src.exceptions import AnalysisError, ConfigurationError, EmailError, GitLabAPIError
from src.gitlab_client import GitLabClient
from src.monitor import IssueMonitor
from src.reporter import generate_email_report, LABEL_COLORS

# Global flag for graceful shutdown
shutdown_event = Event()
app = Flask(__name__)

# Disable Werkzeug's default request logging to use timezone-aware logging
werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.setLevel(logging.WARNING)

# Global components
gitlab_client: Optional[GitLabClient] = None
analyzer: Optional[IssueAnalyzer] = None
email_sender: Optional[EmailSender] = None
monitor: Optional[IssueMonitor] = None
analysis_cache: Optional[AnalysisCache] = None
config: Optional[dict] = None
dry_run: bool = False
logger: Optional[logging.Logger] = None


def setup_logging(log_level: str = "INFO", timezone: str = "Asia/Ho_Chi_Minh") -> logging.Logger:
    """
    Set up logging configuration with timezone support.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        timezone: Timezone string (e.g., 'Asia/Ho_Chi_Minh')

    Returns:
        Configured logger
    """
    class TimezoneFormatter(logging.Formatter):
        def __init__(self, tz_str):
            super().__init__(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt=None
            )
            try:
                self.tz = pytz.timezone(tz_str)
            except pytz.exceptions.UnknownTimeZoneError:
                self.tz = pytz.UTC

        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created, tz=self.tz)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")

    try:
        pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        basic_logger = logging.getLogger(__name__)
        basic_logger.warning(f"Unknown timezone: {timezone}, falling back to UTC")
        timezone = "UTC"

    formatter = TimezoneFormatter(timezone)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.handlers = [handler]
    
    # Configure Werkzeug logger to use timezone-aware timestamps
    class WerkzeugTimezoneFormatter(logging.Formatter):
        """Formatter for Werkzeug access logs with timezone-aware timestamps."""
        def __init__(self, tz_str):
            try:
                self.tz = pytz.timezone(tz_str)
            except pytz.exceptions.UnknownTimeZoneError:
                self.tz = pytz.UTC
            
            # Use Werkzeug's default format but with timezone-aware timestamps
            super().__init__(
                fmt='%(message)s',
                datefmt=None
            )
        
        def format(self, record):
            # Format the timestamp in timezone
            dt = datetime.fromtimestamp(record.created, tz=self.tz)
            timestamp = dt.strftime("%d/%b/%Y %H:%M:%S")
            
            # Werkzeug access logs format: "IP - - [timestamp] "method path" status"
            # We need to preserve the original message but replace the timestamp
            original_msg = record.getMessage()
            
            # Try to find and replace timestamp in Werkzeug format [DD/MMM/YYYY HH:MM:SS]
            # Pattern matches Werkzeug timestamp format: [02/Jan/2026 04:38:13]
            pattern = r'\[(\d{2}/\w{3}/\d{4} \d{2}:\d{2}:\d{2})\]'
            if re.search(pattern, original_msg):
                # Replace with timezone-aware timestamp
                formatted_msg = re.sub(pattern, f'[{timestamp}]', original_msg)
                record.msg = formatted_msg
                record.args = ()
            
            return super().format(record)
    
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    # Remove existing handlers to avoid duplicate logs
    werkzeug_logger.handlers = []
    # Add our timezone-aware handler with custom formatter
    werkzeug_handler = logging.StreamHandler()
    werkzeug_formatter = WerkzeugTimezoneFormatter(timezone)
    werkzeug_handler.setFormatter(werkzeug_formatter)
    werkzeug_logger.addHandler(werkzeug_handler)
    # Prevent propagation to root logger to avoid duplicate logs
    werkzeug_logger.propagate = False

    return logging.getLogger(__name__)


def initialize_components(cfg: dict) -> None:
    """
    Initialize all application components.

    Args:
        cfg: Configuration dictionary

    Raises:
        ConfigurationError: If configuration is invalid
    """
    global gitlab_client, analyzer, email_sender, monitor, analysis_cache

    # Initialize GitLab client
    gitlab_config = cfg["gitlab"]
    gitlab_client = GitLabClient(
        url=gitlab_config["url"],
        token=gitlab_config["token"],
        project_id=gitlab_config.get(
            "project_id"
        ),  # Optional - None uses global endpoint
        timeout=30,
        max_retries=cfg["app"].get("max_retries", 3),
        retry_backoff=cfg["app"].get("retry_backoff", 2.0),
    )

    # Initialize analyzer
    ai_config = cfg["ai"]
    analyzer = IssueAnalyzer(
        provider=ai_config["provider"],
        api_key=ai_config["api_key"],
        model=ai_config["model"],
        base_url=ai_config.get("base_url"),
        temperature=ai_config.get("temperature", 0.7),
        max_tokens=ai_config.get("max_tokens", 2000),
        timeout=120,
        max_retries=cfg["app"].get("max_retries", 3),
        retry_backoff=cfg["app"].get("retry_backoff", 2.0),
        enable_reasoning=ai_config.get("enable_reasoning", False),
    )

    # Initialize email sender
    smtp_config = cfg["smtp"]
    email_sender = EmailSender(
        host=smtp_config["host"],
        port=smtp_config["port"],
        username=smtp_config["username"],
        password=smtp_config["password"],
        from_email=smtp_config["from_email"],
        use_tls=smtp_config.get("use_tls", True),
        use_ssl=smtp_config.get("use_ssl", False),
        timeout=30,
        max_retries=cfg["app"].get("max_retries", 3),
        retry_backoff=cfg["app"].get("retry_backoff", 2.0),
    )

    # Initialize monitor
    filter_labels = cfg.get("gitlab", {}).get("issue_filter", {}).get("labels")
    monitor = IssueMonitor(
        gitlab_client=gitlab_client,
        filter_labels=filter_labels,
        processed_issues_file=cfg["app"].get("processed_issues_file"),
    )

    # Initialize analysis cache
    cache_file = cfg["app"].get("analysis_cache_file", "data/analysis_cache.json")
    analysis_cache = AnalysisCache(cache_file=cache_file)


def process_issue(
    issue_iid: int,
    project_id: Optional[int] = None,
    skip_cache: bool = False,
    to_email: Optional[Union[str, List[str]]] = None,
) -> bool:
    """
    Process a single issue: fetch, analyze, and send email.

    Args:
        issue_iid: Internal Issue ID
        project_id: Optional project ID from issue data (required when using global endpoint)
        skip_cache: If True, skip cached analysis and re-analyze the issue
        to_email: Optional custom recipient email(s). If None, uses default from config.

    Returns:
        True if processed successfully, False otherwise
    """
    try:
        logger.info(f"👉 Processing issue #{issue_iid}")

        if dry_run:
            return True

        # Fetch basic issue data first to get issue_id for cache check
        # Use get_issue (lighter) instead of fetch_comprehensive_issue_data
        logger.info(f"👉 Fetching basic data for issue #{issue_iid}")
        basic_issue_data = gitlab_client.get_issue(issue_iid, project_id=project_id)
        issue_id = basic_issue_data.get("id")
        logger.info(f"✅ Fetched basic data for issue #{issue_iid} successfully")

        # Check cache first (unless skip_cache is True) - avoid comprehensive fetch if cached
        cached_data = None
        if not skip_cache and issue_id and analysis_cache:
            cached_data = analysis_cache.get_issue_with_report(issue_id, issue_iid)

        if cached_data:
            logger.info(
                f"👉 Using cached analysis for issue #{issue_iid} (ID: {issue_id})"
            )
            analysis = cached_data.get("analysis", {})
            report = cached_data.get("email_report", {})
            # Use cached issue_data merged with basic data
            issue_data = {**basic_issue_data, **cached_data.get("issue_data", {})}
        else:
            if skip_cache:
                logger.info(
                    f"👉 Skipping cache and re-analyzing issue #{issue_iid} (ID: {issue_id})"
                )
            # Fetch comprehensive issue data (comments, attachments, etc.) for analysis
            logger.info(f"👉 Fetching comprehensive data for issue #{issue_iid}")
            comprehensive_data = gitlab_client.fetch_comprehensive_issue_data(
                issue_iid, project_id=project_id
            )
            # Merge with basic data
            issue_data = {**basic_issue_data, **comprehensive_data}
            logger.info(f"✅ Fetched comprehensive data for issue #{issue_iid} successfully")
            
            # Analyze issue
            logger.info(f"👉 Analyzing issue #{issue_iid}...")
            gitlab_url = config.get("gitlab", {}).get("url") if config else None
            try:
                analysis = analyzer.analyze_issue(issue_data, gitlab_url=gitlab_url)
            except AnalysisError as e:
                # Store error in cache for UI display
                error_message = str(e)
                if issue_id and analysis_cache:
                    analysis_cache.set(
                        issue_id,
                        {},  # Empty analysis
                        issue_iid,
                        issue_data,
                        email_report=None,
                        error=error_message,
                    )
                raise

            # Generate email report
            subject_prefix = config["smtp"].get("subject_prefix", "[GitLab Issue Analysis]")
            report = generate_email_report(issue_data, analysis, subject_prefix)

            # Cache analysis and email report together (only once, after both are ready)
            if issue_id and analysis_cache:
                analysis_cache.set(
                    issue_id, analysis, issue_iid, issue_data, email_report=report, error=None
                )

        # Send email (non-blocking - mark as processed even if email fails)
        # Use custom to_email if provided, otherwise use default from config
        email_recipients = to_email if to_email is not None else config["smtp"]["to_email"]
        if isinstance(email_recipients, str):
            email_recipients = [email_recipients]

        try:
            logger.info(f"👉 Sending email for issue #{issue_iid} to {email_recipients}")
            email_sender.send_email(
                to=email_recipients,
                subject=report["subject"],
                body=report["text"],
                html_body=report["html"],
            )
            logger.info(f"✅ Email sent successfully for issue #{issue_iid}")
        except EmailError as e:
            logger.warning(
                f"Email failed for issue #{issue_iid}: {e}. Issue will still be marked as processed."
            )

        # Mark as processed (even if email failed)
        if issue_id:
            monitor.mark_as_processed(issue_id)

        logger.info(f"🎯 Processed the issue #{issue_iid} successful")
        return True

    except GitLabAPIError as e:
        logger.error(f"❌ GitLab API error processing issue #{issue_iid}: {e}")
        return False
    except AnalysisError as e:
        logger.error(f"❌ Analysis error processing issue #{issue_iid}: {e}")
        return False
    except Exception as e:
        logger.error(
            f"❌ Unexpected error processing issue #{issue_iid}: {e}", exc_info=True
        )
        return False


def process_issue_from_data(
    issue: Dict[str, Any], project_id: Optional[int] = None, skip_cache: bool = False
) -> bool:
    """
    Process an issue from issue data: fetch details, analyze, and send email.

    This function uses the issue data from polling/webhook to avoid re-fetching
    the basic issue information. The issue data already contains project_id from
    the global API endpoint response (which returns issues from multiple projects).

    Args:
        issue: Issue dictionary from API response (must include 'iid' and 'project_id')
        project_id: Optional project ID (extracted from issue if not provided)
        skip_cache: If True, skip cached analysis and re-analyze the issue

    Returns:
        True if processed successfully, False otherwise
    """
    issue_iid = issue.get("iid")
    if not issue_iid:
        logger.error("❌ Issue data missing 'iid' field")
        return False

    # Extract project_id from issue data if not provided
    # This is required because the global endpoint returns issues from multiple projects
    if not project_id:
        project_id = issue.get("project_id")

    if not project_id:
        logger.error(
            f"❌ Cannot process issue #{issue_iid}: missing project_id in issue data"
        )
        return False

    try:
        logger.info(f"👉 Processing issue #{issue_iid} from project {project_id}")

        if dry_run:
            return True

        # Check cache first (unless skip_cache is True) - we already have issue data with id
        issue_id = issue.get("id")
        cached_data = None
        if not skip_cache and issue_id and analysis_cache:
            cached_data = analysis_cache.get_issue_with_report(issue_id, issue_iid)

        if cached_data:
            logger.info(
                f"👉 Using cached analysis for issue #{issue_iid} (ID: {issue_id})"
            )
            analysis = cached_data.get("analysis", {})
            report = cached_data.get("email_report", {})
            # Use cached issue_data merged with original issue data
            issue_data = {**issue, **cached_data.get("issue_data", {})}
        else:
            if skip_cache:
                logger.info(
                    f"👉 Skipping cache and re-analyzing issue #{issue_iid} (ID: {issue_id})"
                )
            # Fetch comprehensive issue data (comments, attachments, etc.) for analysis
            logger.info(f"👉 Fetching comprehensive data for issue #{issue_iid}")
            comprehensive_data = gitlab_client.fetch_comprehensive_issue_data(
                issue_iid, project_id=project_id
            )
            # Merge with the original issue data to ensure we have all fields
            issue_data = {**issue, **comprehensive_data}
            logger.info(f"✅ Fetched comprehensive data for issue #{issue_iid} successfully")
            
            # Analyze issue
            logger.info(f"👉 Analyzing issue #{issue_iid}...")
            gitlab_url = config.get("gitlab", {}).get("url") if config else None
            try:
                analysis = analyzer.analyze_issue(issue_data, gitlab_url=gitlab_url)
            except AnalysisError as e:
                # Store error in cache for UI display
                error_message = str(e)
                if issue_id and analysis_cache:
                    analysis_cache.set(
                        issue_id,
                        {},  # Empty analysis
                        issue_iid,
                        issue_data,
                        email_report=None,
                        error=error_message,
                    )
                raise

            # Generate email report
            subject_prefix = config["smtp"].get("subject_prefix", "[GitLab Issue Analysis]")
            report = generate_email_report(issue_data, analysis, subject_prefix)

            # Cache analysis and email report together (only once, after both are ready)
            if issue_id and analysis_cache:
                analysis_cache.set(
                    issue_id, analysis, issue_iid, issue_data, email_report=report, error=None
                )

        # Send email (non-blocking - mark as processed even if email fails)
        to_email = config["smtp"]["to_email"]
        if isinstance(to_email, str):
            to_email = [to_email]

        try:
            logger.info(f"👉 Sending email for issue #{issue_iid} to {to_email}")
            email_sender.send_email(
                to=to_email,
                subject=report["subject"],
                body=report["text"],
                html_body=report["html"],
            )
            logger.info(f"✅ Email sent successfully for issue #{issue_iid}")
        except EmailError as e:
            logger.warning(
                f"Email failed for issue #{issue_iid}: {e}. Issue will still be marked as processed."
            )

        # Mark as processed (even if email failed)
        if issue_id:
            monitor.mark_as_processed(issue_id)

        logger.info(f"🎯 Processed the issue #{issue_iid} successful")
        return True

    except GitLabAPIError as e:
        logger.error(f"❌ GitLab API error processing issue #{issue_iid}: {e}")
        return False
    except AnalysisError as e:
        logger.error(f"❌ Analysis error processing issue #{issue_iid}: {e}")
        return False
    except Exception as e:
        logger.error(
            f"❌ Unexpected error processing issue #{issue_iid}: {e}", exc_info=True
        )
        return False


def run_flask_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """
    Run Flask server in a separate thread.

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    logger.info(f"👉 Starting Flask server (host: {host}, port: {port})")
    try:
        app.run(host=host, port=port, debug=False, use_reloader=False)
        logger.info(f"✅ Flask server started successfully at http://{host}:{port}/")
    except Exception as e:
        logger.error(f"❌ Error in Flask server: {e}", exc_info=True)


def run_polling_mode(poll_interval: int) -> None:
    """
    Run application in polling mode.

    Args:
        poll_interval: Polling interval in seconds
    """
    # Start Flask server in background thread for dashboard access during polling
    flask_host = config.get("app", {}).get("webhook_host", "0.0.0.0")
    flask_port = config.get("app", {}).get("webhook_port", 8000)
    flask_thread = Thread(
        target=run_flask_server,
        args=(flask_host, flask_port),
        daemon=True,
        name="FlaskServer",
    )
    flask_thread.start()
    logger.info(f"✅ Website available at http://{flask_host}:{flask_port}/")

    while not shutdown_event.is_set():
        try:
            gitlab_config = config.get("gitlab", {})
            issue_filter = gitlab_config.get("issue_filter", {})
            scope = issue_filter.get("scope")
            labels = issue_filter.get("labels")

            # Get start time from ENV or default to current time
            issue_start_time = config.get("app", {}).get("issue_start_time")
            
            if issue_start_time:
                # Normalize to ISO 8601 format for GitLab API
                normalized_time = issue_start_time.strip().replace(" ", "T", 1)
                if not (normalized_time.endswith("Z") or ("+" in normalized_time[-6:] or "-" in normalized_time[-6:])):
                    normalized_time += "Z"
                created_after = normalized_time
            else:
                created_after = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Format timestamp for display in configured timezone
            formatted_time = created_after
            try:
                time_str = created_after.replace("Z", "+00:00")
                dt_utc = datetime.fromisoformat(time_str)
                timezone_str = config.get("app", {}).get("timezone", "Asia/Ho_Chi_Minh")
                tz = pytz.timezone(timezone_str)
                if dt_utc.tzinfo is None:
                    dt_utc = pytz.UTC.localize(dt_utc)
                dt_local = dt_utc.astimezone(tz)
                formatted_time = dt_local.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                logger.debug(f"Failed to format timestamp: {e}")
            
            logger.info(f"👉 Start time to filter issues: {formatted_time}")

            new_issues = monitor.poll_issues(
                state="opened",
                created_after=created_after,
                scope=scope,
                labels=labels,
            )

            if new_issues:
                # Filter out already cached issues to avoid reprocessing
                issues_to_analyze = []
                cached_issues = []
                
                for issue in new_issues:
                    issue_id = issue.get("id")
                    issue_iid = issue.get("iid")
                    
                    if issue_id and analysis_cache:
                        cached_data = analysis_cache.get_issue_with_report(issue_id, issue_iid)
                        if cached_data:
                            cached_issues.append(issue)
                            continue
                    
                    issues_to_analyze.append(issue)
                
                # Apply limit for testing mode
                max_issues = config["app"].get("max_issues_per_poll")
                original_count = len(issues_to_analyze)
                if max_issues is not None and max_issues > 0:
                    issues_to_analyze = issues_to_analyze[:max_issues]
                    if len(issues_to_analyze) < original_count:
                        logger.info(f"📊 Limited to {len(issues_to_analyze)} issue(s) due to MAX_ISSUES_PER_POLL={max_issues}")

                # Log new issues found (not cached)
                if issues_to_analyze:
                    issue_list = [f"#{issue.get('iid', '?')} (PID: {issue.get('project_id', '?')})" for issue in issues_to_analyze]
                    logger.info(f"✅ Found {len(issues_to_analyze)} new issue(s): {', '.join(issue_list)}")
                else:
                    logger.info("👉 No new issues")
                
                # Update new_issues to only include issues to analyze
                new_issues = issues_to_analyze

                processed_count = 0
                for issue in new_issues:
                    if shutdown_event.is_set():
                        break

                    # Double-check limit as safety measure
                    max_issues = config["app"].get("max_issues_per_poll")
                    if (
                        max_issues is not None
                        and max_issues > 0
                        and processed_count >= max_issues
                    ):
                        break

                    issue_iid = issue.get("iid")
                    # Extract project_id from issue data (required for fetching details)
                    project_id = issue.get("project_id")
                    if issue_iid:
                        # Pass the full issue data to avoid re-fetching
                        if process_issue_from_data(issue, project_id=project_id):
                            processed_count += 1
                    else:
                        logger.warning(f"⚠️ Skipping issue without IID: {issue}")
            else:
                logger.info("👉 No new issues")

            # Wait for next poll (with interruptible sleep)
            if not shutdown_event.wait(poll_interval):
                continue
            else:
                break

        except KeyboardInterrupt:
            shutdown_event.set()
            break
        except Exception as e:
            logger.error(f"❌ Error in polling loop: {e}", exc_info=True)
            # Continue polling even if there's an error
            if not shutdown_event.wait(min(poll_interval, 60)):
                continue
            else:
                break


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    """
    Handle GitLab webhook requests.

    Returns:
        JSON response
    """
    try:
        # Check if automation is enabled
        enable_automation = (
            config.get("app", {}).get("enable_automation", True) if config else True
        )
        if not enable_automation:
            return (
                jsonify(
                    {
                        "message": "Automation is disabled. Use the dashboard to manually trigger analysis."
                    }
                ),
                200,
            )

        # Validate request has JSON payload
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        payload = request.get_json()
        if not payload:
            return jsonify({"error": "Invalid or empty JSON payload"}), 400

        # Get webhook secret from header
        header_token = request.headers.get("X-Gitlab-Token")
        webhook_secret = config["gitlab"].get("webhook_secret")

        # Validate webhook (check gitlab_client is initialized)
        if webhook_secret:
            if not gitlab_client or not gitlab_client.validate_webhook_secret(
                payload, webhook_secret, header_token
            ):
                logger.warning("⚠️ Invalid webhook secret")
                return jsonify({"error": "Invalid webhook secret"}), 401

        # Process webhook
        issue_data = monitor.process_webhook(payload)

        if not issue_data:
            logger.info("ℹ️ Issue already processed or filtered, skipping")
            return jsonify({"message": "Issue already processed or filtered"}), 200

        issue_iid = issue_data.get("iid")
        if not issue_iid:
            logger.warning("⚠️ No issue IID in webhook payload")
            return jsonify({"error": "Invalid webhook payload"}), 400

        # Extract project_id from issue data if available
        project_id = issue_data.get("project_id")

        # Process issue using the webhook data (synchronously for now)
        # In production, you might want to use a queue/background task
        success = process_issue_from_data(issue_data, project_id=project_id)

        if success:
            return jsonify({"message": "Issue processed successfully"}), 200
        else:
            return jsonify({"message": "Issue processing failed"}), 500

    except ValueError as e:
        logger.error(f"❌ Invalid webhook payload: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/", methods=["GET"])
@app.route("/dashboard", methods=["GET"])
def dashboard():
    """
    Dashboard UI endpoint.

    Returns:
        Rendered dashboard HTML page
    """
    app_version = config.get("app", {}).get("version", "0.1.0") if config else "0.1.0"
    return render_template("dashboard.html", version=app_version)


@app.route("/issues", methods=["GET"])
def issues_list():
    """
    List all processed issues UI.

    Returns:
        Rendered issues list HTML page
    """
    app_version = config.get("app", {}).get("version", "0.1.0") if config else "0.1.0"
    return render_template("issues_list.html", version=app_version, label_colors=LABEL_COLORS)


@app.route("/issues/<int:issue_id>", methods=["GET"])
def issue_view(issue_id: int):
    """
    View issue details UI.

    Args:
        issue_id: GitLab issue ID

    Returns:
        Rendered issue view HTML page
    """
    app_version = config.get("app", {}).get("version", "0.1.0") if config else "0.1.0"
    return render_template("issue_view.html", issue_id=issue_id, version=app_version)


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """
    Get application statistics.

    Returns:
        JSON response with statistics
    """
    try:
        # Get processed count from analysis cache (more accurate and persistent)
        processed_count = 0
        if analysis_cache:
            processed_count = analysis_cache.get_processed_count()
        elif monitor:
            # Fallback to monitor's processed issues count
            processed_count = len(monitor.processed_issues)

        app_mode = config.get("app", {}).get("mode", "unknown") if config else "unknown"
        gitlab_url = config.get("gitlab", {}).get("url", "") if config else ""
        enable_automation = (
            config.get("app", {}).get("enable_automation", True) if config else True
        )

        # Get main configuration
        ai_provider = (
            config.get("ai", {}).get("provider", "unknown") if config else "unknown"
        )
        ai_model = config.get("ai", {}).get("model", "unknown") if config else "unknown"
        ai_reasoning = (
            config.get("ai", {}).get("enable_reasoning", False) if config else False
        )
        environment = (
            config.get("app", {}).get("environment", "unknown") if config else "unknown"
        )
        poll_interval = (
            config.get("app", {}).get("poll_interval", 900) if config else 900
        )
        max_issues_per_poll = (
            config.get("app", {}).get("max_issues_per_poll") if config else None
        )
        gitlab_labels = (
            config.get("gitlab", {}).get("issue_filter", {}).get("labels")
            if config
            else None
        )

        return (
            jsonify(
                {
                    "processed_count": processed_count,
                    "app_mode": app_mode,
                    "gitlab_url": gitlab_url,
                    "automation_enabled": enable_automation,
                    "config": {
                        "gitlab_labels": gitlab_labels,
                        "gitlab_url": gitlab_url,
                        "ai_provider": ai_provider,
                        "ai_model": ai_model,
                        "ai_reasoning": ai_reasoning,
                        "environment": environment,
                        "poll_interval": poll_interval,
                        "max_issues_per_poll": max_issues_per_poll,
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}", exc_info=True)
        return jsonify({"error": "Failed to get statistics"}), 500


@app.route("/api/trigger", methods=["POST"])
def trigger_analysis():
    """
    Manually trigger issue analysis.

    Request body:
        {
            "project_id": int,
            "issue_iid": int,
            "to_email": str or list[str] (optional) - Custom recipient email(s)
        }

    Returns:
        JSON response with result
    """
    try:
        if not request.json:
            return jsonify({"error": "Request body is required"}), 400

        project_id = request.json.get("project_id")
        issue_iid = request.json.get("issue_iid")
        to_email = request.json.get("to_email")  # Optional custom recipient email(s)

        if not project_id or not issue_iid:
            return (
                jsonify({"error": "Both 'project_id' and 'issue_iid' are required"}),
                400,
            )

        # Validate components are initialized
        if not gitlab_client or not analyzer or not email_sender or not monitor:
            return jsonify({"error": "Application components not initialized"}), 503

        logger.info(
            f"🎯 Manual trigger process issue #{issue_iid} from project {project_id} (skipping cache)"
        )
        if to_email:
            logger.info(f"📧 Using custom recipient email(s): {to_email}")

        # Process the issue (skip cache for manual triggers to always get fresh analysis)
        try:
            success = process_issue(
                issue_iid, project_id=project_id, skip_cache=True, to_email=to_email
            )

            if success:
                return (
                    jsonify(
                        {
                            "success": True,
                            "message": f"Issue #{issue_iid} from project {project_id} processed successfully",
                        }
                    ),
                    200,
                )
            else:
                # Check if there's an error stored in cache for this issue
                error_message = None
                if analysis_cache:
                    # Try to get the issue from cache to see if there's an error
                    issue_data = None
                    try:
                        # Fetch issue data to get issue_id
                        issue_data = gitlab_client.fetch_comprehensive_issue_data(
                            issue_iid, project_id=project_id
                        )
                        issue_id = issue_data.get("id") if issue_data else None
                        if issue_id:
                            cached_data = analysis_cache.get_issue_with_report(issue_id, issue_iid)
                            if cached_data and cached_data.get("error"):
                                error_message = cached_data.get("error")
                    except Exception:
                        pass  # Ignore errors when fetching issue data for error retrieval
                
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": error_message or f"Failed to process issue #{issue_iid} from project {project_id}",
                        }
                    ),
                    500,
                )
        except AnalysisError as e:
            # AnalysisError was raised, store it and return the error message
            error_message = str(e)
            # Try to store error in cache if we have issue data
            try:
                issue_data = gitlab_client.fetch_comprehensive_issue_data(
                    issue_iid, project_id=project_id
                )
                issue_id = issue_data.get("id") if issue_data else None
                if issue_id and analysis_cache:
                    analysis_cache.set(
                        issue_id,
                        {},  # Empty analysis
                        issue_iid,
                        issue_data,
                        email_report=None,
                        error=error_message,
                    )
            except Exception:
                pass  # Ignore errors when storing error in cache
            
            return (
                jsonify(
                    {
                        "success": False,
                        "error": error_message,
                    }
                ),
                500,
            )

    except ValueError as e:
        logger.error(f"❌ Invalid request: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"❌ Error triggering analysis: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/issues", methods=["GET"])
def list_processed_issues():
    """
    List all processed issues with latest state from GitLab.

    Fetches the current state of each issue from GitLab and updates the cache.

    Returns:
        JSON response with list of processed issues with updated states
    """
    try:
        if not analysis_cache:
            return jsonify({"error": "Analysis cache not initialized"}), 503

        if not gitlab_client:
            return jsonify({"error": "GitLab client not initialized"}), 503

        # Get all cached issues
        issues = analysis_cache.get_all_issues()
        
        # Update states from GitLab for each issue
        updated_count = 0
        for issue in issues:
            issue_iid = issue.get("issue_iid")
            issue_id = issue.get("issue_id")
            project_id = issue.get("project_id")
            
            # Skip if we don't have required info to fetch from GitLab
            if not issue_iid or not project_id:
                continue
            
            try:
                # Fetch latest issue data from GitLab
                latest_issue = gitlab_client.get_issue(issue_iid, project_id=project_id)
                latest_state = latest_issue.get("state")
                latest_updated_at = latest_issue.get("updated_at")
                
                # Update cache if state changed
                if latest_state and latest_state != issue.get("state"):
                    analysis_cache.update_issue_state(
                        issue_id, latest_state, latest_updated_at
                    )
                    # Update the issue in our list
                    issue["state"] = latest_state
                    if latest_updated_at:
                        issue["updated_at"] = latest_updated_at
                    updated_count += 1
                elif latest_state:
                    # State is the same, but update updated_at if available
                    if latest_updated_at and latest_updated_at != issue.get("updated_at"):
                        analysis_cache.update_issue_state(
                            issue_id, latest_state, latest_updated_at
                        )
                        issue["updated_at"] = latest_updated_at
            except GitLabAPIError as e:
                # Log error but continue with other issues
                logger.warning(
                    f"⚠️ Failed to fetch latest state for issue #{issue_iid} (ID: {issue_id}): {e}"
                )
                continue
            except Exception as e:
                # Log unexpected errors but continue
                logger.warning(
                    f"⚠️ Unexpected error fetching state for issue #{issue_iid} (ID: {issue_id}): {e}"
                )
                continue
        
        if updated_count > 0:
            logger.debug(f"✅ Updated state for {updated_count} issue(s)")
        
        # Get updated issues list from cache
        issues = analysis_cache.get_all_issues()
        return jsonify({"issues": issues, "count": len(issues)}), 200
    except Exception as e:
        logger.error(f"❌ Error listing issues: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/issues/<int:issue_id>", methods=["GET"])
def get_issue_details(issue_id: int):
    """
    Get details of a processed issue including analysis and email report.
    Updates issue state from GitLab before returning.

    Args:
        issue_id: GitLab issue ID

    Returns:
        JSON response with issue details, analysis, and email report
    """
    try:
        if not analysis_cache:
            return jsonify({"error": "Analysis cache not initialized"}), 503

        cached_data = analysis_cache.get_issue_with_report(issue_id)
        if not cached_data:
            return jsonify({"error": f"Issue {issue_id} not found in cache"}), 404

        # Update state from GitLab if we have the required info
        issue_data = cached_data.get("issue_data", {})
        issue_iid = cached_data.get("issue_iid")
        project_id = issue_data.get("project_id")
        
        if gitlab_client and issue_iid and project_id:
            try:
                # Fetch latest issue data from GitLab
                latest_issue = gitlab_client.get_issue(issue_iid, project_id=project_id)
                latest_state = latest_issue.get("state")
                latest_updated_at = latest_issue.get("updated_at")
                
                # Update cache if state changed
                if latest_state and latest_state != issue_data.get("state"):
                    analysis_cache.update_issue_state(
                        issue_id, latest_state, latest_updated_at
                    )
                    # Update the cached_data with new state
                    issue_data["state"] = latest_state
                    if latest_updated_at:
                        issue_data["updated_at"] = latest_updated_at
                elif latest_state and latest_updated_at:
                    # Update updated_at even if state is the same
                    if latest_updated_at != issue_data.get("updated_at"):
                        analysis_cache.update_issue_state(
                            issue_id, latest_state, latest_updated_at
                        )
                        issue_data["updated_at"] = latest_updated_at
            except GitLabAPIError as e:
                # Log warning but continue with cached data
                logger.warning(
                    f"⚠️ Failed to fetch latest state for issue #{issue_iid} (ID: {issue_id}): {e}"
                )
            except Exception as e:
                # Log unexpected errors but continue
                logger.warning(
                    f"⚠️ Unexpected error fetching state for issue #{issue_iid} (ID: {issue_id}): {e}"
                )

        return jsonify(cached_data), 200
    except Exception as e:
        logger.error(f"❌ Error getting issue details: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/issues/<int:issue_id>", methods=["DELETE"])
def delete_issue(issue_id: int):
    """
    Delete a specific issue from cache.

    Args:
        issue_id: GitLab issue ID

    Returns:
        JSON response with result
    """
    try:
        if not analysis_cache:
            return jsonify({"error": "Analysis cache not initialized"}), 503

        deleted = analysis_cache.delete(issue_id)
        if deleted:
            logger.info(f"✅ Deleted issue {issue_id} from cache")
            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Issue {issue_id} deleted successfully",
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": f"Issue {issue_id} not found in cache"}), 404
    except Exception as e:
        logger.error(f"❌ Error deleting issue: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/issues", methods=["DELETE"])
def clear_all_issues():
    """
    Clear all cached issues.

    Returns:
        JSON response with result
    """
    try:
        if not analysis_cache:
            return jsonify({"error": "Analysis cache not initialized"}), 503

        analysis_cache.clear()
        logger.info("✅ Cleared all cached issues")
        return (
            jsonify(
                {
                    "success": True,
                    "message": "All cached issues cleared successfully",
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"❌ Error clearing all issues: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/issues/<int:issue_id>/reanalyze", methods=["POST"])
def reanalyze_issue(issue_id: int):
    """
    Reanalyze an issue without sending email.

    Args:
        issue_id: GitLab issue ID

    Request body (optional):
        {
            "project_id": int,
            "issue_iid": int
        }

    Returns:
        JSON response with result
    """
    try:
        if not analysis_cache or not analyzer or not gitlab_client:
            return jsonify({"error": "Application components not initialized"}), 503

        # Get cached issue data to find project_id and issue_iid
        cached_data = analysis_cache.get_issue_with_report(issue_id)
        if not cached_data:
            return jsonify({"error": f"Issue {issue_id} not found in cache"}), 404

        issue_data = cached_data.get("issue_data", {})
        # Use get_json(silent=True) to avoid exception on empty/invalid JSON
        request_data = request.get_json(silent=True) or {}
        project_id = request_data.get("project_id")
        issue_iid = request_data.get("issue_iid")

        # Use cached data if not provided
        # Get project_id from cached issue_data
        if not project_id:
            project_id = issue_data.get("project_id")
        # Get issue_iid from cached_data (now included in get_issue_with_report return)
        if not issue_iid:
            issue_iid = cached_data.get("issue_iid")

        if not project_id or not issue_iid:
            return jsonify({"error": "Missing project_id or issue_iid"}), 400

        logger.info(
            f"🎯 Reanalyzing issue #{issue_iid} (ID: {issue_id}) from project {project_id}"
        )

        # Fetch fresh issue data
        fresh_issue_data = gitlab_client.fetch_comprehensive_issue_data(
            issue_iid, project_id=project_id
        )

        # Merge with cached issue data
        fresh_issue_data = {**issue_data, **fresh_issue_data}

        # Reanalyze
        gitlab_url = config.get("gitlab", {}).get("url") if config else None
        analysis = analyzer.analyze_issue(fresh_issue_data, gitlab_url=gitlab_url)

        # Generate new email report
        subject_prefix = config["smtp"].get("subject_prefix", "[GitLab Issue Analysis]")
        report = generate_email_report(fresh_issue_data, analysis, subject_prefix)

        # Update cache with new analysis and report
        analysis_cache.set(
            issue_id, analysis, issue_iid, fresh_issue_data, email_report=report
        )

        logger.info(f"✅ Reanalysis complete for issue #{issue_iid} (ID: {issue_id})")

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Issue #{issue_iid} (ID: {issue_id}) reanalyzed successfully",
                    "issue_id": issue_id,
                    "issue_iid": issue_iid,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"❌ Error reanalyzing issue: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/issues/<int:issue_id>/resend", methods=["POST"])
def resend_email(issue_id: int):
    """
    Resend email for an issue without reanalyzing.

    Args:
        issue_id: GitLab issue ID

    Returns:
        JSON response with result
    """
    try:
        if not analysis_cache or not email_sender:
            return jsonify({"error": "Application components not initialized"}), 503

        # Get cached issue data and email report
        cached_data = analysis_cache.get_issue_with_report(issue_id)
        if not cached_data:
            return jsonify({"error": f"Issue {issue_id} not found in cache"}), 404

        email_report = cached_data.get("email_report", {})
        if not email_report:
            return (
                jsonify({"error": f"No email report found for issue {issue_id}"}),
                404,
            )

        issue_data = cached_data.get("issue_data", {})
        issue_iid = issue_data.get("issue_iid") or issue_data.get("iid")

        logger.info(f"🎯 Resending email for issue #{issue_iid} (ID: {issue_id})")

        # Send email
        to_email = config["smtp"]["to_email"]
        if isinstance(to_email, str):
            to_email = [to_email]

        try:
            email_sender.send_email(
                to=to_email,
                subject=email_report["subject"],
                body=email_report["text"],
                html_body=email_report["html"],
            )
            logger.info(
                f"✅ Email resent successfully for issue #{issue_iid} (ID: {issue_id})"
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Email resent successfully for issue #{issue_iid} (ID: {issue_id})",
                        "issue_id": issue_id,
                        "issue_iid": issue_iid,
                    }
                ),
                200,
            )
        except EmailError as e:
            logger.error(f"Email failed for issue #{issue_iid}: {e}")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Email failed: {e}",
                    }
                ),
                500,
            )
    except Exception as e:
        logger.error(f"❌ Error resending email: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/issues/<int:issue_id>/reanalyze-and-resend", methods=["POST"])
def reanalyze_and_resend(issue_id: int):
    """
    Reanalyze an issue and resend the email.

    Args:
        issue_id: GitLab issue ID

    Request body (optional):
        {
            "project_id": int,
            "issue_iid": int
        }

    Returns:
        JSON response with result
    """
    try:
        if not analysis_cache or not analyzer or not email_sender or not gitlab_client:
            return jsonify({"error": "Application components not initialized"}), 503

        # Get cached issue data to find project_id and issue_iid
        cached_data = analysis_cache.get_issue_with_report(issue_id)
        if not cached_data:
            return jsonify({"error": f"Issue {issue_id} not found in cache"}), 404

        issue_data = cached_data.get("issue_data", {})
        # Use get_json(silent=True) to avoid exception on empty/invalid JSON
        request_data = request.get_json(silent=True) or {}
        project_id = request_data.get("project_id")
        issue_iid = request_data.get("issue_iid")

        # Use cached data if not provided
        # Get project_id from cached issue_data
        if not project_id:
            project_id = issue_data.get("project_id")
        # Get issue_iid from cached_data (now included in get_issue_with_report return)
        if not issue_iid:
            issue_iid = cached_data.get("issue_iid")

        if not project_id or not issue_iid:
            return jsonify({"error": "Missing project_id or issue_iid"}), 400

        logger.info(
            f"🎯 Reanalyzing and resending email for issue #{issue_iid} (ID: {issue_id}) from project {project_id}"
        )

        # Fetch fresh issue data
        fresh_issue_data = gitlab_client.fetch_comprehensive_issue_data(
            issue_iid, project_id=project_id
        )

        # Merge with cached issue data
        fresh_issue_data = {**issue_data, **fresh_issue_data}

        # Reanalyze
        gitlab_url = config.get("gitlab", {}).get("url") if config else None
        analysis = analyzer.analyze_issue(fresh_issue_data, gitlab_url=gitlab_url)

        # Generate new email report
        subject_prefix = config["smtp"].get("subject_prefix", "[GitLab Issue Analysis]")
        report = generate_email_report(fresh_issue_data, analysis, subject_prefix)

        # Update cache with new analysis and report
        analysis_cache.set(
            issue_id, analysis, issue_iid, fresh_issue_data, email_report=report
        )

        # Send email
        to_email = config["smtp"]["to_email"]
        if isinstance(to_email, str):
            to_email = [to_email]

        try:
            email_sender.send_email(
                to=to_email,
                subject=report["subject"],
                body=report["text"],
                html_body=report["html"],
            )
            logger.info(
                f"✅ Reanalysis and email sent successfully for issue #{issue_iid} (ID: {issue_id})"
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Issue #{issue_iid} (ID: {issue_id}) reanalyzed and email sent successfully",
                        "issue_id": issue_id,
                        "issue_iid": issue_iid,
                    }
                ),
                200,
            )
        except EmailError as e:
            logger.error(f"Email failed for issue #{issue_iid}: {e}")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Reanalysis completed but email failed: {e}",
                        "issue_id": issue_id,
                        "issue_iid": issue_iid,
                    }
                ),
                500,
            )
    except Exception as e:
        logger.error(f"❌ Error reanalyzing and resending: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON response with health status
    """
    app_version = config.get("app", {}).get("version", "0.1.0") if config else "0.1.0"
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "GitLab Issues Analyzer",
                "version": app_version,
            }
        ),
        200,
    )


def run_webhook_mode(host: str, port: int) -> None:
    """
    Run application in webhook mode.

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    # Enable debug mode and reloader in development environment
    is_development = config.get("app", {}).get("environment", "production") == "development"
    debug_mode = is_development
    use_reloader = is_development
    
    logger.info(f"✅ Website available at http://{host}:{port}/")
    logger.info(f"🔄 Auto-reload: {'enabled' if use_reloader else 'disabled'} (environment: {config.get('app', {}).get('environment', 'production')})")
    logger.info("Press Ctrl+C to stop the server.")

    try:
        app.run(host=host, port=port, debug=debug_mode, use_reloader=use_reloader)
    except Exception as e:
        logger.error(f"❌ Error in webhook server: {e}", exc_info=True)
        raise


def signal_handler(signum: int, frame) -> None:
    """
    Handle shutdown signals.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    shutdown_event.set()


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="GitLab Issues Analyzer - Analyze GitLab issues using AI and send email reports"
    )

    parser.add_argument(
        "--mode",
        choices=["webhook", "poll"],
        default="poll",
        help="Application mode: webhook (real-time) or poll (periodic checks)",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Polling interval in seconds (overrides config, polling mode only)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (don't send emails or make API calls)",
    )

    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    global config, dry_run, logger

    args = parse_arguments()
    dry_run = args.dry_run

    # Load configuration first to get timezone
    config = load_config()
    validate_config(config)
    
    # Get timezone from config
    timezone = config.get("app", {}).get("timezone", "Asia/Ho_Chi_Minh")
    
    # Set up logging with timezone
    logger = setup_logging("INFO", timezone)

    # System boot message
    logger.info("🚀 Booting the system - GitLab Issues Analyzer v0.1.0")
    logger.info(f"🌏 Timezone: {timezone}")

    # Load and validate configuration (from environment variables only)
    logger.info("👉 Loading configuration from environment")

    # System information
    logger.info(f"⚙️ _Environment: {config['app'].get('environment', 'production')}")
    logger.info(f"⚙️ _Mode: {args.mode}")
    enable_automation = config["app"].get("enable_automation", True)
    logger.info(
        f"⚙️ _Automation status: {'enabled' if enable_automation else 'disabled'}"
    )
    logger.info(f"⚙️ _AI Provider: {config.get('ai', {}).get('provider', 'unknown')}")
    logger.info(f"⚙️ _AI Model: {config.get('ai', {}).get('model', 'unknown')}")
    max_issues = config["app"].get("max_issues_per_poll")
    if max_issues:
        logger.info(f"⚙️ _Max Issues Per Poll: {max_issues}")
    else:
        logger.info("⚙️ _Max Issues Per Poll: Unlimited")
    logger.info("✅ Loaded configuration from environment successfully")

    if dry_run:
        logger.info("⚠️ DRY RUN MODE - No actual operations will be performed")

    try:
        # Update log level from config
        log_level = config["app"].get("log_level", "INFO")
        timezone = config["app"].get("timezone", "Asia/Ho_Chi_Minh")
        # Re-setup logging with correct timezone and log level
        logger = setup_logging(log_level, timezone)
        logger.info(f"🌏 Logging timezone: {timezone}")

        # Initialize components
        logger.info("👉 Initializing components...")
        initialize_components(config)
        logger.info("✅ All components initialized successfully")
        logger.info("🚀 Booted the system successfully - GitLab Issues Analyzer v0.1.0")

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Check if automation is enabled
        enable_automation = config["app"].get("enable_automation", True)

        if not enable_automation:
            # Start Flask server only (no polling/webhook automation)
            flask_host = config["app"].get("webhook_host", "0.0.0.0")
            flask_port = config["app"].get("webhook_port", 8000)
            # Enable debug mode and reloader in development environment
            is_development = config.get("app", {}).get("environment", "production") == "development"
            debug_mode = is_development
            use_reloader = is_development
            
            logger.info(f"✅ Website available at http://{flask_host}:{flask_port}/")
            logger.info(f"🔄 Auto-reload: {'enabled' if use_reloader else 'disabled'} (environment: {config.get('app', {}).get('environment', 'production')})")
            # Run Flask server in main thread (blocking)
            app.run(host=flask_host, port=flask_port, debug=debug_mode, use_reloader=use_reloader)
        else:
            # Run in selected mode (automation enabled)
            if args.mode == "poll":
                poll_interval = args.interval or config["app"].get("poll_interval", 900)
                run_polling_mode(poll_interval)
            elif args.mode == "webhook":
                host = config["app"].get("webhook_host", "0.0.0.0")
                port = config["app"].get("webhook_port", 8000)
                run_webhook_mode(host, port)

        return 0

    except ConfigurationError as e:
        logger.error(f"❌ Configuration error: {e}")
        return 1
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
