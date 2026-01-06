"""
Analysis cache module for storing and retrieving issue analysis results.

This module provides persistent caching of analysis results to avoid re-analyzing
the same issues after container restarts.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AnalysisCache:
    """
    Cache for storing issue analysis results.

    Stores analysis results in a JSON file in the data folder to persist
    across container restarts.
    """

    def __init__(self, cache_file: str = "data/analysis_cache.json"):
        """
        Initialize analysis cache.

        Args:
            cache_file: Path to cache file (relative to project root or absolute)
        """
        self.cache_file = Path(cache_file)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.metadata: Dict[str, Any] = {"count_processed_issues": 0}

        # Ensure data directory exists
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing cache
        self._load_cache()

        # Initialize system start time if not exists (for filtering old issues)
        if "system_start_time" not in self.metadata:
            from datetime import datetime

            self.metadata["system_start_time"] = datetime.utcnow().isoformat() + "Z"
            self._save_cache()

    def _get_cache_key(self, issue_id: int, issue_iid: Optional[int] = None) -> str:
        """
        Generate cache key for an issue.

        Uses issue_id as primary key, with issue_iid as fallback for uniqueness.

        Args:
            issue_id: GitLab issue ID (unique across all projects)
            issue_iid: Issue IID (project-specific, optional)

        Returns:
            Cache key string
        """
        # Use issue_id as primary key since it's globally unique
        return f"issue_{issue_id}"

    def get(
        self, issue_id: int, issue_iid: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis for an issue.

        Args:
            issue_id: GitLab issue ID
            issue_iid: Issue IID (optional, for logging)

        Returns:
            Cached analysis dictionary if found, None otherwise
        """
        cache_key = self._get_cache_key(issue_id, issue_iid)
        cached = self.cache.get(cache_key)

        if cached:
            return cached.get("analysis")
        else:
            return None

    def set(
        self,
        issue_id: int,
        analysis: Dict[str, Any],
        issue_iid: Optional[int] = None,
        issue_data: Optional[Dict[str, Any]] = None,
        email_report: Optional[Dict[str, str]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Cache analysis result for an issue.

        Args:
            issue_id: GitLab issue ID
            analysis: Analysis result dictionary
            issue_iid: Issue IID (optional, for reference)
            issue_data: Optional issue data for reference (cached for retrieval)
            email_report: Optional email report dictionary with 'subject', 'html', 'text'
            error: Optional error message if analysis failed
        """
        cache_key = self._get_cache_key(issue_id, issue_iid)

        # Store analysis with metadata
        cache_entry = {
            "analysis": analysis,
            "issue_id": issue_id,
            "issue_iid": issue_iid,
        }

        # Store error if provided
        if error:
            cache_entry["error"] = error

        # Store email report if provided
        if email_report:
            cache_entry["email_report"] = email_report

        # Store issue data if provided (for viewing details later)
        if issue_data:
            # Store only essential fields to avoid bloating cache
            cache_entry["issue_data"] = {
                "title": issue_data.get("title"),
                "state": issue_data.get("state"),
                "web_url": issue_data.get("web_url"),
                "project_id": issue_data.get("project_id"),
                "labels": issue_data.get("labels", []),
                "author": issue_data.get("author"),
                "assignee": issue_data.get("assignee"),
                "created_at": issue_data.get("created_at"),
                "updated_at": issue_data.get("updated_at"),
            }

        # Check if this is a new entry (not updating existing)
        is_new_entry = cache_key not in self.cache

        self.cache[cache_key] = cache_entry

        # Update processed count if this is a new entry
        if is_new_entry:
            self.metadata["count_processed_issues"] = len(self.cache)

        # Persist to file
        self._save_cache()

        logger.info(
            f"✅ Cached analysis to data/analysis_cache.json for issue ID {issue_id} (IID: {issue_iid})"
        )

    def get_all_issues(self) -> List[Dict[str, Any]]:
        """
        Get all processed issues with their metadata.

        Returns:
            List of issue dictionaries with cached data
        """
        issues = []
        for cache_key, cache_entry in self.cache.items():
            if cache_key == "_metadata":
                continue
            issue_data = cache_entry.get("issue_data", {})
            issues.append(
                {
                    "issue_id": cache_entry.get("issue_id"),
                    "issue_iid": cache_entry.get("issue_iid"),
                    "title": issue_data.get("title", "Unknown"),
                    "state": issue_data.get("state", "unknown"),
                    "web_url": issue_data.get("web_url"),
                    "project_id": issue_data.get("project_id"),
                    "labels": issue_data.get("labels", []),
                    "created_at": issue_data.get("created_at"),
                    "updated_at": issue_data.get("updated_at"),
                    "has_report": "email_report" in cache_entry,
                    "has_error": "error" in cache_entry,
                    "error": cache_entry.get("error"),
                }
            )
        # Sort by issue_id descending (most recent first)
        issues.sort(key=lambda x: x.get("issue_id", 0), reverse=True)
        return issues

    def get_issue_with_report(
        self, issue_id: int, issue_iid: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached issue data including analysis and email report.

        Args:
            issue_id: GitLab issue ID
            issue_iid: Issue IID (optional)

        Returns:
            Dictionary with issue_data, analysis, email_report, and issue_iid, or None if not found
        """
        cache_key = self._get_cache_key(issue_id, issue_iid)
        cached = self.cache.get(cache_key)

        if cached:
            return {
                "issue_data": cached.get("issue_data", {}),
                "analysis": cached.get("analysis", {}),
                "email_report": cached.get("email_report", {}),
                "error": cached.get("error"),
                "issue_iid": cached.get(
                    "issue_iid"
                ),  # Include issue_iid from cache entry
            }
        return None

    def has(self, issue_id: int, issue_iid: Optional[int] = None) -> bool:
        """
        Check if analysis is cached for an issue.

        Args:
            issue_id: GitLab issue ID
            issue_iid: Issue IID (optional)

        Returns:
            True if cached, False otherwise
        """
        cache_key = self._get_cache_key(issue_id, issue_iid)
        return cache_key in self.cache

    def get_processed_count(self) -> int:
        """
        Get the count of processed issues.

        Returns:
            Number of processed issues in cache
        """
        # Return count from metadata or calculate from cache
        if "count_processed_issues" in self.metadata:
            return self.metadata["count_processed_issues"]
        else:
            # Fallback: count entries in cache
            return len(self.cache)

    def get_system_start_time(self) -> Optional[str]:
        """
        Get the system start time (ISO 8601 format).

        This is used to filter out old issues that existed before the system started.
        Only issues created after this time will be processed automatically.

        Returns:
            ISO 8601 timestamp string, or None if not set
        """
        return self.metadata.get("system_start_time")

    def delete(self, issue_id: int) -> bool:
        """
        Delete a specific issue from cache.

        Args:
            issue_id: GitLab issue ID to delete

        Returns:
            True if issue was found and deleted, False otherwise
        """
        cache_key = self._get_cache_key(issue_id)
        if cache_key in self.cache:
            del self.cache[cache_key]
            self._save_cache()
            logger.info(f"Deleted issue {issue_id} from cache")
            return True
        return False

    def clear(self) -> None:
        """Clear all cached analyses."""
        self.cache.clear()
        self.metadata["count_processed_issues"] = 0
        self._save_cache()
        logger.info("Cleared all cached issues")

    def _load_cache(self) -> None:
        """Load cache from file."""
        if not self.cache_file.exists():
            logger.debug(
                f"👉 Cache file {self.cache_file} does not exist, starting with empty cache"
            )
            return

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Handle different cache formats
                if isinstance(data, dict):
                    # Check if it's the new format with metadata
                    if "_metadata" in data:
                        # New format with metadata: { "_metadata": {...}, "issue_123": {...} }
                        self.metadata = data.get(
                            "_metadata", {"count_processed_issues": 0}
                        )
                        # Remove metadata from cache entries
                        self.cache = {k: v for k, v in data.items() if k != "_metadata"}
                        # Ensure count is correct
                        if "count_processed_issues" not in self.metadata:
                            self.metadata["count_processed_issues"] = len(self.cache)
                        # Ensure system_start_time is set (for filtering old issues)
                        if "system_start_time" not in self.metadata:
                            from datetime import datetime

                            self.metadata["system_start_time"] = (
                                datetime.utcnow().isoformat() + "Z"
                            )
                            self._save_cache()
                    elif any(k.startswith("issue_") for k in data.keys()):
                        # Format: { "issue_123": { "analysis": {...}, "issue_id": 123, ... } }
                        # Old format without metadata - migrate it
                        self.cache = data
                        # Calculate count from cache
                        self.metadata["count_processed_issues"] = len(self.cache)
                        # Set system start time for filtering old issues
                        from datetime import datetime

                        self.metadata["system_start_time"] = (
                            datetime.utcnow().isoformat() + "Z"
                        )
                        # Save with new format (with metadata)
                        self._save_cache()
                    else:
                        # Might be old format, try to parse
                        self.cache = data
                        self.metadata["count_processed_issues"] = len(self.cache)
                        # Set system start time for filtering old issues
                        from datetime import datetime

                        self.metadata["system_start_time"] = (
                            datetime.utcnow().isoformat() + "Z"
                        )
                        self._save_cache()
                elif isinstance(data, list):
                    # Legacy format: list of entries
                    self.cache = {}
                    for entry in data:
                        if isinstance(entry, dict) and "issue_id" in entry:
                            issue_id = entry["issue_id"]
                            cache_key = self._get_cache_key(issue_id)
                            self.cache[cache_key] = entry
                    self.metadata["count_processed_issues"] = len(self.cache)
                    # Set system start time for filtering old issues
                    from datetime import datetime

                    self.metadata["system_start_time"] = (
                        datetime.utcnow().isoformat() + "Z"
                    )
                    self._save_cache()
                else:
                    self.cache = {}
                    self.metadata["count_processed_issues"] = 0
                    # Set system start time for filtering old issues
                    from datetime import datetime

                    self.metadata["system_start_time"] = (
                        datetime.utcnow().isoformat() + "Z"
                    )
                    self._save_cache()
        except (json.JSONDecodeError, IOError):
            self.cache = {}
            self.metadata["count_processed_issues"] = 0
            # Set system start time for filtering old issues
            from datetime import datetime

            self.metadata["system_start_time"] = datetime.utcnow().isoformat() + "Z"

    def _save_cache(self) -> None:
        """Save cache to file."""
        try:
            # Ensure directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            # Update metadata with current count
            self.metadata["count_processed_issues"] = len(self.cache)

            # Save cache with metadata
            cache_data = {"_metadata": self.metadata, **self.cache}

            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Error saving analysis cache: {e}")
