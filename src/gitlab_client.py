"""
GitLab API client for fetching issues and related data.

This module provides a client for interacting with GitLab API v4 to fetch
issues, comments, related issues, and attachments.
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import HTTPError, RequestException, Timeout

from src.exceptions import GitLabAPIError

logger = logging.getLogger(__name__)


class GitLabClient:
    """
    Client for interacting with GitLab API v4.

    This client handles authentication, API requests, error handling,
    and data fetching for GitLab issues.
    """

    def __init__(
        self,
        url: str,
        token: str,
        project_id: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
    ):
        """
        Initialize GitLab API client.

        Args:
            url: GitLab instance URL (e.g., 'https://gitlab.com')
            token: GitLab Personal Access Token
            project_id: Optional GitLab project ID or path. If None, uses global /api/v4/issues endpoint
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_backoff: Exponential backoff multiplier (default: 2.0)
        """
        self.url = url.rstrip("/")
        self.token = token
        self.project_id = project_id
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self.headers = {"PRIVATE-TOKEN": token, "Content-Type": "application/json"}

        # Use global endpoint if project_id is not provided
        if self.project_id:
            self.base_url = f"{self.url}/api/v4/projects/{self.project_id}"
        else:
            self.base_url = f"{self.url}/api/v4"

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        use_project_endpoint: bool = True,
        **kwargs,
    ) -> requests.Response:
        """
        Make HTTP request to GitLab API with retry logic.

        Args:
            method: HTTP method ('GET', 'POST', etc.)
            endpoint: API endpoint path
            params: Query parameters
            use_project_endpoint: If True and project_id exists, use project-specific endpoint.
                                 If False or project_id is None, use global endpoint.
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            GitLabAPIError: If request fails after retries
        """
        if use_project_endpoint and self.project_id:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
        else:
            # Use global endpoint
            url = f"{self.url}/api/v4/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    timeout=self.timeout,
                    **kwargs,
                )
                response.raise_for_status()
                return response

            except Timeout as e:
                if attempt == self.max_retries - 1:
                    raise GitLabAPIError(
                        f"Request timeout after {self.max_retries} attempts: {e}"
                    )
                wait_time = self.retry_backoff**attempt
                time.sleep(wait_time)

            except HTTPError as e:
                status_code = e.response.status_code if e.response else None

                # Don't retry on client errors (4xx), except 429 (rate limit)
                if status_code and 400 <= status_code < 500 and status_code != 429:
                    raise GitLabAPIError(
                        f"GitLab API error: {e}",
                        status_code=status_code,
                        response=e.response.json() if e.response else None,
                    )

                # Retry on server errors (5xx) and rate limits (429)
                if attempt == self.max_retries - 1:
                    raise GitLabAPIError(
                        f"GitLab API error after {self.max_retries} attempts: {e}",
                        status_code=status_code,
                        response=e.response.json() if e.response else None,
                    )

                if status_code == 429:
                    # Rate limited - check Retry-After header
                    retry_after = int(e.response.headers.get("Retry-After", 60))
                    time.sleep(retry_after)
                else:
                    wait_time = self.retry_backoff**attempt
                    time.sleep(wait_time)

            except RequestException as e:
                if attempt == self.max_retries - 1:
                    raise GitLabAPIError(f"Network error: {e}")
                wait_time = self.retry_backoff**attempt
                time.sleep(wait_time)

        # Should never reach here, but just in case
        raise GitLabAPIError("Request failed after all retries")

    def get_issues(
        self,
        state: str = "opened",
        created_after: Optional[str] = None,
        per_page: int = 20,
        scope: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch list of issues from GitLab.

        Uses global /api/v4/issues endpoint if project_id is not set.
        Uses project-specific /api/v4/projects/{project_id}/issues if project_id is set.

        Args:
            state: Issue state filter ('opened', 'closed', 'all')
            created_after: ISO 8601 timestamp to filter issues created after
            per_page: Number of issues per page (max 100)
            scope: Scope filter for global endpoint ('all', 'assigned_to_me', 'created_by_me', etc.)
            labels: List of label names to filter by (e.g., ['UNIOSS 3', 'bug'])

        Returns:
            List of issue dictionaries

        Raises:
            GitLabAPIError: If API request fails
        """
        params = {
            "state": state,
            "order_by": "created_at",
            "sort": "desc",
            "per_page": min(per_page, 100),  # GitLab max is 100
        }

        if created_after:
            params["created_after"] = created_after

        # Global endpoint parameters
        if scope:
            params["scope"] = scope

        if labels:
            # GitLab API expects labels as comma-separated string or multiple label[] parameters
            # Using comma-separated string is simpler
            params["labels"] = ",".join(labels)

        # Use global endpoint if project_id is not set
        use_project_endpoint = self.project_id is not None
        response = self._make_request(
            "GET", "/issues", params=params, use_project_endpoint=use_project_endpoint
        )
        issues = response.json()
        
        # Log fetched issue IDs
        if issues:
            issue_ids = [f"#{issue.get('iid', '?')} (PID: {issue.get('project_id', '?')})" for issue in issues]
            logger.info(f"✅ Fetched {len(issues)} issue(s): {', '.join(issue_ids)}")
        else:
            logger.info("✅ Fetched 0 issues")
        
        return issues

    def get_issue(
        self, issue_iid: int, project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch single issue by IID (Internal Issue ID).

        Args:
            issue_iid: Internal Issue ID (not the global ID)
            project_id: Project ID from issue data (required when using global endpoint)

        Returns:
            Issue dictionary

        Raises:
            GitLabAPIError: If API request fails or issue not found
        """
        try:
            # If we have project_id from issue data, use it; otherwise use self.project_id
            if project_id:
                # Temporarily use project-specific endpoint
                url = f"{self.url}/api/v4/projects/{project_id}/issues/{issue_iid}"
                for attempt in range(self.max_retries):
                    try:
                        response = requests.get(
                            url, headers=self.headers, timeout=self.timeout
                        )
                        response.raise_for_status()
                        return response.json()
                    except HTTPError as e:
                        status_code = e.response.status_code if e.response else None
                        if status_code == 404:
                            raise GitLabAPIError(
                                f"Issue {issue_iid} not found", status_code=404
                            ) from e
                        if attempt == self.max_retries - 1:
                            raise GitLabAPIError(
                                f"GitLab API error: {e}", status_code=status_code
                            ) from e
                        if status_code == 429:
                            retry_after = int(e.response.headers.get("Retry-After", 60))
                            time.sleep(retry_after)
                        else:
                            wait_time = self.retry_backoff**attempt
                            time.sleep(wait_time)
                    except (Timeout, RequestException) as e:
                        if attempt == self.max_retries - 1:
                            raise GitLabAPIError(f"Network error: {e}") from e
                        wait_time = self.retry_backoff**attempt
                        time.sleep(wait_time)
            elif self.project_id:
                # Use project-specific endpoint
                response = self._make_request("GET", f"/issues/{issue_iid}")
                return response.json()
            else:
                raise GitLabAPIError(
                    "Cannot fetch issue: project_id is required when using global endpoint. "
                    "Provide project_id from issue data."
                )
        except GitLabAPIError:
            raise
        except Exception as e:
            raise GitLabAPIError(f"Unexpected error: {e}") from e

    def get_issue_comments(
        self, issue_iid: int, project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all comments/notes for an issue.

        Args:
            issue_iid: Internal Issue ID
            project_id: Project ID from issue data (required when using global endpoint)

        Returns:
            List of comment dictionaries

        Raises:
            GitLabAPIError: If API request fails
        """
        try:
            if project_id:
                url = (
                    f"{self.url}/api/v4/projects/{project_id}/issues/{issue_iid}/notes"
                )
                for attempt in range(self.max_retries):
                    try:
                        response = requests.get(
                            url, headers=self.headers, timeout=self.timeout
                        )
                        response.raise_for_status()
                        comments = response.json()
                        break
                    except HTTPError as e:
                        if attempt == self.max_retries - 1:
                            raise GitLabAPIError(f"GitLab API error: {e}") from e
                        if e.response and e.response.status_code == 429:
                            retry_after = int(e.response.headers.get("Retry-After", 60))
                            time.sleep(retry_after)
                        else:
                            wait_time = self.retry_backoff**attempt
                            time.sleep(wait_time)
                    except (Timeout, RequestException) as e:
                        if attempt == self.max_retries - 1:
                            raise GitLabAPIError(f"Network error: {e}") from e
                        wait_time = self.retry_backoff**attempt
                        time.sleep(wait_time)
            elif self.project_id:
                response = self._make_request("GET", f"/issues/{issue_iid}/notes")
                comments = response.json()
            else:
                raise GitLabAPIError(
                    "Cannot fetch comments: project_id is required when using global endpoint. "
                    "Provide project_id from issue data."
                )
        except GitLabAPIError:
            raise
        except Exception as e:
            raise GitLabAPIError(f"Unexpected error: {e}") from e

        # Filter out system notes (optional - can be configured)
        return [c for c in comments if not c.get("system", False)]

    def get_related_issues(
        self, issue_iid: int, project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch related/linked issues.

        Args:
            issue_iid: Internal Issue ID
            project_id: Project ID from issue data (required when using global endpoint)

        Returns:
            List of related issue dictionaries (may be empty if API not available)

        Raises:
            GitLabAPIError: If API request fails (but may return empty list if feature not available)
        """
        try:
            if project_id:
                url = (
                    f"{self.url}/api/v4/projects/{project_id}/issues/{issue_iid}/links"
                )
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                links = response.json()
            elif self.project_id:
                response = self._make_request("GET", f"/issues/{issue_iid}/links")
                links = response.json()
            else:
                # Links API requires project context, return empty if not available
                return []

            # Extract related issues from links
            related = []
            for link in links:
                source = link.get("source_issue", {})
                target = link.get("target_issue", {})
                link_type = link.get("link_type", "relates_to")

                # Add both source and target if they're different from current issue
                if source.get("iid") != issue_iid:
                    related.append(
                        {
                            "id": source.get("id"),
                            "iid": source.get("iid"),
                            "title": source.get("title"),
                            "state": source.get("state"),
                            "link_type": link_type,
                            "web_url": source.get("web_url"),
                        }
                    )
                if target.get("iid") != issue_iid:
                    related.append(
                        {
                            "id": target.get("id"),
                            "iid": target.get("iid"),
                            "title": target.get("title"),
                            "state": target.get("state"),
                            "link_type": link_type,
                            "web_url": target.get("web_url"),
                        }
                    )

            return related

        except (GitLabAPIError, HTTPError) as e:
            # Links API may not be available in all GitLab versions
            # Return empty list instead of failing
            status_code = getattr(e, "status_code", None) or (
                e.response.status_code
                if hasattr(e, "response") and e.response
                else None
            )
            if status_code == 404:
                return []
            raise

    def get_issue_attachments(
        self, issue_iid: int, project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract attachments from issue description and comments.

        Note: GitLab stores attachments as markdown links in descriptions/comments.
        This method extracts those URLs.

        Args:
            issue_iid: Internal Issue ID
            project_id: Project ID from issue data (required when using global endpoint)

        Returns:
            List of attachment dictionaries with 'url' and 'source' fields

        Raises:
            GitLabAPIError: If API request fails
        """
        issue = self.get_issue(issue_iid, project_id=project_id)
        # Extract project_id from issue if not provided
        if not project_id and "project_id" in issue:
            project_id = issue["project_id"]
        comments = self.get_issue_comments(issue_iid, project_id=project_id)

        attachments = []

        # Extract from issue description
        description = issue.get("description", "")
        attachments.extend(
            self._extract_attachments_from_text(description, "description")
        )

        # Extract from comments
        for comment in comments:
            body = comment.get("body", "")
            comment_attachments = self._extract_attachments_from_text(
                body, "comment", comment_id=comment.get("id")
            )
            attachments.extend(comment_attachments)

        return attachments

    def _extract_attachments_from_text(
        self, text: str, source: str, comment_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract attachment URLs from markdown text.

        Args:
            text: Text to search (markdown format)
            source: Source of the text ('description' or 'comment')
            comment_id: Comment ID if source is 'comment'

        Returns:
            List of attachment dictionaries
        """
        attachments = []

        # Pattern for markdown links: ![alt](url) or [text](url)
        pattern = r"!\[.*?\]\((.*?)\)|\[.*?\]\((.*?)\)"

        for match in re.finditer(pattern, text):
            url = match.group(1) or match.group(2)
            if url:
                # Check if it's an attachment (uploads directory or external URL)
                if "uploads" in url or url.startswith("http"):
                    attachment = {"url": url, "source": source}
                    if comment_id:
                        attachment["comment_id"] = comment_id
                    attachments.append(attachment)

        return attachments

    def fetch_comprehensive_issue_data(
        self, issue_iid: int, project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive issue data including comments, related issues, and attachments.

        Args:
            issue_iid: Internal Issue ID
            project_id: Project ID from issue data (required when using global endpoint)

        Returns:
            Dictionary with all issue data including:
            - All issue fields
            - 'comments': List of comments
            - 'related_issues': List of related issues
            - 'attachments': List of attachments
            - 'comment_count': Number of comments

        Raises:
            GitLabAPIError: If API request fails
        """
        issue = self.get_issue(issue_iid, project_id=project_id)
        # Extract project_id from issue if not provided
        if not project_id and "project_id" in issue:
            project_id = issue["project_id"]

        comments = self.get_issue_comments(issue_iid, project_id=project_id)
        related_issues = self.get_related_issues(issue_iid, project_id=project_id)
        attachments = self.get_issue_attachments(issue_iid, project_id=project_id)

        return {
            **issue,
            "comments": comments,
            "related_issues": related_issues,
            "attachments": attachments,
            "comment_count": len(comments),
        }

    def parse_webhook_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse GitLab webhook payload and extract issue data.

        Args:
            payload: Webhook payload dictionary

        Returns:
            Extracted issue data dictionary

        Raises:
            ValueError: If payload structure is invalid
        """
        if "object_attributes" not in payload:
            raise ValueError("Invalid webhook payload: missing 'object_attributes'")

        obj_attrs = payload["object_attributes"]

        # Extract labels
        labels = []
        if "labels" in obj_attrs:
            if isinstance(obj_attrs["labels"], list):
                labels = [
                    label.get("title", label) if isinstance(label, dict) else label
                    for label in obj_attrs["labels"]
                ]

        return {
            "id": obj_attrs.get("id"),
            "iid": obj_attrs.get("iid"),
            "title": obj_attrs.get("title", ""),
            "description": obj_attrs.get("description", ""),
            "state": obj_attrs.get("state", "opened"),
            "url": obj_attrs.get("url", ""),
            "labels": labels,
            "created_at": obj_attrs.get("created_at"),
            "updated_at": obj_attrs.get("updated_at"),
            "assignee_id": obj_attrs.get("assignee_id"),
            "author_id": obj_attrs.get("author_id"),
        }

    def validate_webhook_secret(
        self, payload: Dict[str, Any], secret: str, header_token: Optional[str] = None
    ) -> bool:
        """
        Validate webhook secret token.

        Note: GitLab sends the secret token in the X-Gitlab-Token header.
        This is a simple string comparison.

        Args:
            payload: Webhook payload (not used, but kept for API consistency)
            secret: Expected secret token
            header_token: Token from X-Gitlab-Token header

        Returns:
            True if token matches, False otherwise
        """
        if not secret:
            return False

        if header_token:
            return header_token == secret

        # If no header token provided, we can't validate
        # In real implementation, this should check the header
        return False
