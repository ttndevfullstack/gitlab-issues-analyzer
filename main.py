#!/usr/bin/env python3
"""
GitLab Issues Analyzer - Main Entry Point

This is the main entry point for the GitLab Issues Analyzer application.
It supports both webhook and polling modes for detecting new GitLab issues.
"""

import argparse
import logging
import signal
import sys
from threading import Event, Thread
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request

from src.analysis_cache import AnalysisCache
from src.analyzer import IssueAnalyzer
from src.config import load_config, validate_config
from src.email_sender import EmailSender
from src.exceptions import AnalysisError, ConfigurationError, EmailError, GitLabAPIError
from src.gitlab_client import GitLabClient
from src.monitor import IssueMonitor
from src.reporter import generate_email_report

# Global flag for graceful shutdown
shutdown_event = Event()
app = Flask(__name__)

# Global components (initialized in main)
gitlab_client: Optional[GitLabClient] = None
analyzer: Optional[IssueAnalyzer] = None
email_sender: Optional[EmailSender] = None
monitor: Optional[IssueMonitor] = None
analysis_cache: Optional[AnalysisCache] = None
config: Optional[dict] = None
dry_run: bool = False
logger: Optional[logging.Logger] = None


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
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
    issue_iid: int, project_id: Optional[int] = None, skip_cache: bool = False
) -> bool:
    """
    Process a single issue: fetch, analyze, and send email.

    Args:
        issue_iid: Internal Issue ID
        project_id: Optional project ID from issue data (required when using global endpoint)
        skip_cache: If True, skip cached analysis and re-analyze the issue

    Returns:
        True if processed successfully, False otherwise
    """
    try:
        logger.info(f"👉 Processing issue #{issue_iid}")

        # Fetch comprehensive issue data
        if dry_run:
            return True

        logger.info(f"👉 Fetching data for issue #{issue_iid}")
        issue_data = gitlab_client.fetch_comprehensive_issue_data(
            issue_iid, project_id=project_id
        )
        logger.info(f"✅ Fetched data for issue #{issue_iid} successfully")

        # Check cache first (unless skip_cache is True)
        issue_id = issue_data.get("id")
        cached_analysis = None
        if not skip_cache and issue_id and analysis_cache:
            cached_analysis = analysis_cache.get(issue_id, issue_iid)

        if cached_analysis:
            logger.info(
                f"Using cached analysis for issue #{issue_iid} (ID: {issue_id})"
            )
            analysis = cached_analysis
        else:
            if skip_cache:
                logger.info(
                    f"👉 Skipping cache and re-analyzing issue #{issue_iid} (ID: {issue_id})"
                )
            # Analyze issue
            logger.info(f"👉 Analyzing issue #{issue_iid}...")
            gitlab_url = config.get("gitlab", {}).get("url") if config else None
            analysis = analyzer.analyze_issue(issue_data, gitlab_url=gitlab_url)

        # Generate email report
        subject_prefix = config["smtp"].get("subject_prefix", "[GitLab Issue Analysis]")
        report = generate_email_report(issue_data, analysis, subject_prefix)

        # Cache analysis and email report together (only once, after both are ready)
        if issue_id and analysis_cache:
            analysis_cache.set(
                issue_id, analysis, issue_iid, issue_data, email_report=report
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

        # Fetch comprehensive issue data (comments, attachments, etc.)
        if dry_run:
            return True

        logger.info(f"👉 Fetching data for issue #{issue_iid}")
        # Use the issue data we already have, only fetch additional details
        issue_data = gitlab_client.fetch_comprehensive_issue_data(
            issue_iid, project_id=project_id
        )

        # Merge with the original issue data to ensure we have all fields
        issue_data = {**issue, **issue_data}
        logger.info(f"✅ Fetched data for issue #{issue_iid} successfully")

        # Check cache first (unless skip_cache is True)
        issue_id = issue_data.get("id")
        cached_analysis = None
        if not skip_cache and issue_id and analysis_cache:
            cached_analysis = analysis_cache.get(issue_id, issue_iid)

        if cached_analysis:
            logger.info(
                f"Using cached analysis for issue #{issue_iid} (ID: {issue_id})"
            )
            analysis = cached_analysis
        else:
            if skip_cache:
                logger.info(
                    f"👉 Skipping cache and re-analyzing issue #{issue_iid} (ID: {issue_id})"
                )
            # Analyze issue
            logger.info(f"👉 Analyzing issue #{issue_iid}...")
            gitlab_url = config.get("gitlab", {}).get("url") if config else None
            analysis = analyzer.analyze_issue(issue_data, gitlab_url=gitlab_url)

        # Generate email report
        subject_prefix = config["smtp"].get("subject_prefix", "[GitLab Issue Analysis]")
        report = generate_email_report(issue_data, analysis, subject_prefix)

        # Cache analysis and email report together (only once, after both are ready)
        if issue_id and analysis_cache:
            analysis_cache.set(
                issue_id, analysis, issue_iid, issue_data, email_report=report
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
    except Exception as e:
        logger.error(f"❌ Error in Flask server: {e}", exc_info=True)


def run_polling_mode(poll_interval: int) -> None:
    """
    Run application in polling mode.

    Args:
        poll_interval: Polling interval in seconds
    """
    # Start Flask server in background thread for dashboard access
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
            # Poll for new issues

            # Get filter configuration
            gitlab_config = config.get("gitlab", {})
            issue_filter = gitlab_config.get("issue_filter", {})
            scope = issue_filter.get("scope")  # e.g., "all"
            labels = issue_filter.get("labels")  # e.g., ["UNIOSS 3"]

            # Get system start time to filter out old issues
            # Only process issues created after the system started
            created_after = None
            if analysis_cache:
                system_start_time = analysis_cache.get_system_start_time()
                if system_start_time:
                    created_after = system_start_time
                    logger.debug(f"👉 Filtering issues created after: {created_after}")

            new_issues = monitor.poll_issues(
                state="opened",
                created_after=created_after,
                scope=scope,
                labels=labels,
            )

            if new_issues:
                # Apply max_issues_per_poll limit (for testing mode)
                max_issues = config["app"].get("max_issues_per_poll")
                if max_issues is not None and max_issues > 0:
                    new_issues = new_issues[:max_issues]

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
                logger.info("👉 No new issues found")

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
    return render_template("dashboard.html")


@app.route("/issues", methods=["GET"])
def issues_list():
    """
    List all processed issues UI.

    Returns:
        Rendered issues list HTML page
    """
    return render_template("issues_list.html")


@app.route("/issues/<int:issue_id>", methods=["GET"])
def issue_view(issue_id: int):
    """
    View issue details UI.

    Args:
        issue_id: GitLab issue ID

    Returns:
        Rendered issue view HTML page
    """
    return render_template("issue_view.html", issue_id=issue_id)


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
            "issue_iid": int
        }

    Returns:
        JSON response with result
    """
    try:
        if not request.json:
            return jsonify({"error": "Request body is required"}), 400

        project_id = request.json.get("project_id")
        issue_iid = request.json.get("issue_iid")

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

        # Process the issue (skip cache for manual triggers to always get fresh analysis)
        success = process_issue(issue_iid, project_id=project_id, skip_cache=True)

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
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Failed to process issue #{issue_iid} from project {project_id}",
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
    List all processed issues.

    Returns:
        JSON response with list of processed issues
    """
    try:
        if not analysis_cache:
            return jsonify({"error": "Analysis cache not initialized"}), 503

        issues = analysis_cache.get_all_issues()
        return jsonify({"issues": issues, "count": len(issues)}), 200
    except Exception as e:
        logger.error(f"❌ Error listing issues: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/issues/<int:issue_id>", methods=["GET"])
def get_issue_details(issue_id: int):
    """
    Get details of a processed issue including analysis and email report.

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

        return jsonify(cached_data), 200
    except Exception as e:
        logger.error(f"❌ Error getting issue details: {e}", exc_info=True)
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
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "GitLab Issues Analyzer",
                "version": "0.1.0",
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
    logger.info(f"✅ Website available at http://{host}:{port}/")
    logger.info("Press Ctrl+C to stop the server.")

    try:
        app.run(host=host, port=port, debug=False)
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

    # Set up logging
    logger = setup_logging("INFO")

    # System boot message
    logger.info("🚀 Booting the system - GitLab Issues Analyzer v0.1.0")

    # Load and validate configuration (from environment variables only)
    logger.info("👉 Loading configuration from environment...")
    config = load_config()
    validate_config(config)

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
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))

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
            logger.info(f"✅ Website available at http://{flask_host}:{flask_port}/")
            # Run Flask server in main thread (blocking)
            app.run(host=flask_host, port=flask_port, debug=False)
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
