"""
Image URL converter module for converting relative image URLs to absolute URLs.

This module helps convert relative image paths in GitLab issue descriptions
to absolute URLs so that AI vision models can access and analyze the images.
"""

import re
from typing import Optional
from urllib.parse import urljoin


def convert_relative_image_urls(
    text: str, gitlab_url: str, project_id: Optional[int] = None
) -> str:
    """
    Convert relative image URLs in markdown/text to absolute URLs.

    GitLab issue descriptions often contain relative image paths like:
    - `/uploads/0bceec044dcc124c5136fc089b381884/image.png`
    - `![image](/uploads/0bceec044dcc124c5136fc089b381884/image.png)`

    These need to be converted to absolute URLs like:
    - `https://gitlab.unioss.jp/-/project/31/uploads/0bceec044dcc124c5136fc089b381884/image.png`

    Args:
        text: Text content (markdown or HTML) containing relative image URLs
        gitlab_url: Base GitLab instance URL (e.g., 'https://gitlab.unioss.jp')
        project_id: Optional project ID for constructing project-specific URLs

    Returns:
        Text with relative image URLs converted to absolute URLs
    """
    if not text:
        return text

    gitlab_url = gitlab_url.rstrip("/")

    def make_absolute_url(relative_path: str) -> str:
        """Convert relative path to absolute URL."""
        if relative_path.startswith("http://") or relative_path.startswith("https://"):
            return relative_path

        if project_id:
            return f"{gitlab_url}/-/project/{project_id}{relative_path}"
        else:
            return urljoin(gitlab_url, relative_path)

    # Use placeholder approach to avoid conflicts between markdown and standalone patterns
    placeholders = {}
    placeholder_counter = 0

    # First, replace markdown image syntax with placeholders
    def replace_markdown_with_placeholder(match: re.Match) -> str:
        nonlocal placeholder_counter
        alt_text = match.group(1)
        relative_path = match.group(2)
        absolute_url = make_absolute_url(relative_path)
        placeholder = f"__MARKDOWN_IMAGE_{placeholder_counter}__"
        placeholders[placeholder] = f"![{alt_text}]({absolute_url})"
        placeholder_counter += 1
        return placeholder

    # Replace markdown image syntax with placeholders
    text = re.sub(
        r"!\[([^\]]*)\]\((/uploads/[^\)]+)\)", replace_markdown_with_placeholder, text
    )

    # Now replace standalone relative upload paths
    def replace_standalone_upload(match: re.Match) -> str:
        """Replace standalone upload URL (not in markdown)."""
        relative_path = match.group(1)
        absolute_url = make_absolute_url(relative_path)
        return absolute_url

    # Match /uploads/ paths that are NOT inside parentheses
    text = re.sub(
        r'(?<!\]\()(?<!\()(/uploads/[^\s<>"\'\)]+)', replace_standalone_upload, text
    )

    # Restore markdown image placeholders
    for placeholder, replacement in placeholders.items():
        text = text.replace(placeholder, replacement)

    return text
