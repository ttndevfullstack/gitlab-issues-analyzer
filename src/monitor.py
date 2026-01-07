"""
Issue monitor module for detecting new GitLab issues.

This module supports both webhook mode (real-time) and polling mode
(periodic checks) for detecting new issues.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.exceptions import GitLabAPIError
from src.gitlab_client import GitLabClient

logger = logging.getLogger(__name__)


class IssueMonitor:
    """
    Monitor for detecting new GitLab issues.

    Supports both webhook mode (real-time) and polling mode (periodic checks).
    Tracks processed issues to avoid duplicates.
    """

    def __init__(
        self,
        gitlab_client: GitLabClient,
        filter_labels: Optional[List[str]] = None,
        processed_issues_file: Optional[str] = None,
    ):
        """
        Initialize issue monitor.

        Args:
            gitlab_client: GitLab API client instance
            filter_labels: List of labels to filter issues (None = process all)
            processed_issues_file: Path to file for persisting processed issue IDs
        """
        self.gitlab_client = gitlab_client
        self.filter_labels = filter_labels or []
        self.processed_issues_file = processed_issues_file

        # In-memory set of processed issue IDs
        self.processed_issues: Set[int] = set()

        # Load processed issues from file if provided
        if self.processed_issues_file:
            self._load_processed_issues()

    def poll_issues(
        self,
        state: str = "opened",
        created_after: Optional[str] = None,
        scope: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Poll GitLab API for new issues.

        Args:
            state: Issue state filter ('opened', 'closed', 'all')
            created_after: ISO 8601 timestamp to filter issues created after
            scope: Scope filter for global endpoint ('all', 'assigned_to_me', etc.)
            labels: List of label names to filter by

        Returns:
            List of new issue dictionaries (not yet processed)
        """
        try:
            all_issues = self.gitlab_client.get_issues(
                state=state,
                created_after=created_after,
                scope=scope,
                labels=labels,
            )

            # Filter out already processed issues
            new_issues = []
            for issue in all_issues:
                issue_id = issue.get("id")
                if issue_id and not self.is_processed(issue_id):
                    # Check if issue should be processed (label filter)
                    if self.should_process_issue(issue):
                        new_issues.append(issue)

            # Log new issues to process (debug level - main.py will log at info level which issues will be analyzed)
            if new_issues:
                new_issue_ids = [f"#{issue.get('iid', '?')} (PID: {issue.get('project_id', '?')})" for issue in new_issues]
                logger.debug(f"✅ Found {len(new_issues)} new issue(s) to process: {', '.join(new_issue_ids)}")
            elif all_issues:
                processed_issue_ids = [f"#{issue.get('iid', '?')} (PID: {issue.get('project_id', '?')})" for issue in all_issues]
                logger.debug(f"✅ All {len(all_issues)} fetched issue(s) already processed: {', '.join(processed_issue_ids)}")

            return new_issues

        except GitLabAPIError as e:
            logger.error(f"Error polling issues: {e}")
            raise

    def process_webhook(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process GitLab webhook payload and extract issue data.

        Args:
            payload: Webhook payload dictionary

        Returns:
            Issue data dictionary if issue should be processed, None otherwise

        Raises:
            ValueError: If payload structure is invalid
        """
        try:
            # Extract issue data from webhook
            issue_data = self.extract_issue_data(payload)

            # Check if already processed
            issue_id = issue_data.get("id")
            if issue_id and self.is_processed(issue_id):
                logger.info(f"Issue {issue_id} already processed, skipping")
                return None

            # Check if issue should be processed (label filter)
            if not self.should_process_issue(issue_data):
                logger.info(
                    f"Issue {issue_id} does not match filter criteria, skipping"
                )
                return None

            return issue_data

        except (KeyError, ValueError) as e:
            logger.error(f"Error processing webhook: {e}")
            raise ValueError(f"Invalid webhook payload: {e}")

    def extract_issue_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract issue data from webhook payload.

        Args:
            payload: Webhook payload dictionary

        Returns:
            Extracted issue data dictionary

        Raises:
            ValueError: If payload structure is invalid
        """
        return self.gitlab_client.parse_webhook_payload(payload)

    def should_process_issue(self, issue_data: Dict[str, Any]) -> bool:
        """
        Check if issue should be processed based on filter criteria.

        Args:
            issue_data: Issue data dictionary

        Returns:
            True if issue should be processed, False otherwise
        """
        # If no filter labels specified, process all issues
        if not self.filter_labels:
            return True

        # Get issue labels
        labels = issue_data.get("labels", [])
        if not labels:
            return False

        # Extract label names
        label_names = []
        for label in labels:
            if isinstance(label, dict):
                label_names.append(label.get("name", label.get("title", "")))
            else:
                label_names.append(str(label))

        # Check if any filter label matches
        for filter_label in self.filter_labels:
            if filter_label in label_names:
                return True

        return False

    def mark_as_processed(self, issue_id: int) -> None:
        """
        Mark issue as processed.

        Args:
            issue_id: Issue ID to mark as processed
        """
        self.processed_issues.add(issue_id)

        # Persist to file if configured
        if self.processed_issues_file:
            self._save_processed_issues()

    def is_processed(self, issue_id: int) -> bool:
        """
        Check if issue has been processed.

        Args:
            issue_id: Issue ID to check

        Returns:
            True if issue has been processed, False otherwise
        """
        return issue_id in self.processed_issues

    def _load_processed_issues(self) -> None:
        """Load processed issue IDs from file."""
        if not self.processed_issues_file:
            return

        file_path = Path(self.processed_issues_file)
        if not file_path.exists():
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.processed_issues = set(data)
                elif isinstance(data, dict) and "processed_issues" in data:
                    self.processed_issues = set(data["processed_issues"])
                else:
                    logger.warning(f"Unexpected format in {self.processed_issues_file}")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading processed issues file: {e}")
            self.processed_issues = set()

    def _save_processed_issues(self) -> None:
        """Save processed issue IDs to file."""
        if not self.processed_issues_file:
            return

        try:
            file_path = Path(self.processed_issues_file)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(list(self.processed_issues), f, indent=2)
        except IOError as e:
            logger.warning(f"Error saving processed issues file: {e}")
