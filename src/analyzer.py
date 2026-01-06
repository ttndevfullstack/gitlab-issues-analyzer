"""
Issue analyzer module for analyzing GitLab issues using AI.

This module integrates with AI providers (OpenRouter, OpenAI) via OpenAI-compatible APIs
to analyze issues using the WWWH-TR framework.
"""

import logging
import time
from typing import Any, Dict, Optional

import requests
from requests.exceptions import HTTPError, RequestException, Timeout

from src.exceptions import AnalysisError
from src.image_url_converter import convert_relative_image_urls
from src.reporter import get_fixed_html_template

logger = logging.getLogger(__name__)

# Vietnamese prompt template for AI analysis
SYSTEM_PROMPT = """Bạn là một chuyên gia phân tích dự án phần mềm. Nhiệm vụ của bạn là phân tích ticket dự án phần mềm theo khung tư duy WWWH-TR và đưa ra các insight có thể hành động được. Hãy xem xét tất cả thông tin có sẵn bao gồm comments, related issues, và attachments."""

USER_PROMPT_TEMPLATE = """Phân tích ticket dự án phần mềm sau đây theo khung tư duy WWWH-TR.



────────────────────────────────

1. THÔNG TIN ĐẦU VÀO (TICKET DATA)

────────────────────────────────



=== THÔNG TIN TICKET ===

Tiêu đề: {title}

Mô tả: {description}

Trạng thái: {state}

Độ ưu tiên: {priority}

Nhãn: {labels}

Người được giao: {assignee}

Người tạo: {author}

Ngày tạo: {created_at}

Ngày cập nhật: {updated_at}

Milestone: {milestone}

URL: {url}



=== COMMENTS ({comment_count} tổng cộng) ===

{comments}



=== RELATED ISSUES ===

{related_issues}



=== ATTACHMENTS & IMAGES ===

{attachments}



────────────────────────────────

2. VAI TRÒ & MỤC TIÊU

────────────────────────────────



Bạn là một chuyên gia phân tích và triển khai dự án phần mềm, đang làm việc với dự án phần mềm cho khách hàng Nhật.



Mục tiêu:

- Hiểu đúng và sâu yêu cầu của ticket

- Tránh hiểu nhầm với khách hàng

- Giúp toàn bộ team (Dev / QA / PM) có cùng nhận thức

- Biến yêu cầu thành hành động cụ thể, khả thi và kiểm chứng được



────────────────────────────────

3. KHUNG TƯ DUY PHÂN TÍCH (WWWH-TR)

────────────────────────────────



Phân tích theo từng phần sau:



- W1 — Why

  Tại sao phải làm điều này?

  → Làm rõ vấn đề gốc rễ và mục tiêu cuối cùng.



- W2 — What

  Cụ thể cần làm những gì?

  → Xác định yêu cầu, phạm vi và thông tin liên quan.



- W3 — Who

  Ai liên quan / ai bị ảnh hưởng?

  → Xác định stakeholder, người ra quyết định và người hỗ trợ.



- H — How

  Có những cách nào để thực hiện?

  → Đề xuất các phương án khả thi, so sánh ưu / nhược điểm và sự đánh đổi.



- T — Test

  Kiểm chứng thế nào?

  → Đề xuất thử nghiệm nhỏ, tiêu chí đo lường (thời gian, chi phí, chất lượng, rủi ro).



- R — Reflect

  Giải pháp tối ưu là gì?

  → Đánh giá, kết luận, bước tiếp theo và điều chỉnh cần thiết.



────────────────────────────────

4. YÊU CẦU NỘI DUNG BẮT BUỘC

────────────────────────────────



Trong phân tích, bắt buộc phải làm rõ:



1. Mong muốn thực sự của khách hàng (kể cả yêu cầu ẩn).

2. Các điểm chưa rõ, mâu thuẫn hoặc cần xác nhận lại với khách hàng.

3. Definition of Done cụ thể cho từng tính năng hoặc giai đoạn.

4. Các hành động cụ thể cần thực hiện để đáp ứng yêu cầu và tiến độ.

5. Phương pháp kiểm thử phù hợp để đảm bảo chất lượng sản phẩm.

6. Trình bày rõ ràng, dễ hiểu để cả team và khách hàng cùng nắm bắt.



────────────────────────────────

5. HƯỚNG DẪN TRÌNH BÀY

────────────────────────────────



- Viết bằng tiếng Việt

- Ngôn ngữ đơn giản, rõ ràng, chính xác

- Tránh thuật ngữ phức tạp không cần thiết

- Thuật ngữ kỹ thuật có thể giữ tiếng Anh / tiếng Nhật khi phù hợp

- Nhấn mạnh các điểm quan trọng, rủi ro và quyết định



────────────────────────────────

6. OUTPUT REQUIREMENTS (FIXED HTML TEMPLATE – BẮT BUỘC)

────────────────────────────────



⚠️ QUAN TRỌNG NHẤT:

Bạn PHẢI sử dụng template HTML cố định được cung cấp bên dưới và ĐIỀN ĐẦY ĐỦ tất cả các placeholder bằng nội dung phân tích của bạn.

KHÔNG được tạo HTML mới, KHÔNG được thay đổi cấu trúc template.

CHỈ được thay thế các placeholder sau bằng nội dung thực tế:

- {{TLDR_ITEMS}}: Danh sách <li> cho TL;DR (5-8 bullet points)
- {{ACTION_ITEMS}}: Danh sách <li> cho Action Items (checklist dạng [ ])
- {{OPEN_QUESTIONS}}: Danh sách <li> cho Open Questions (hoặc "Không có câu hỏi cần xác nhận")
- {{W1_ITEMS}}: Danh sách <li> cho W1 — Why
- {{W2_ITEMS}}: Danh sách <li> cho W2 — What
- {{W3_ITEMS}}: Danh sách <li> cho W3 — Who
- {{H_ITEMS}}: Danh sách <li> cho H — How
- {{T_ITEMS}}: Danh sách <li> cho T — Test
- {{R_ITEMS}}: Danh sách <li> cho R — Reflect



6.1. Yêu cầu điền template:

- Mỗi placeholder PHẢI được thay thế bằng danh sách <li>...</li> hợp lệ
- Mỗi <li> phải chứa nội dung phân tích cụ thể, không được để trống
- Nếu một section không có nội dung, vẫn phải có ít nhất 1 <li> với nội dung "Chưa có nội dung" hoặc tương tự
- TẤT CẢ nội dung trong <li> phải được escape HTML đúng cách (không chứa HTML không hợp lệ)
- KHÔNG được thêm bất kỳ tag HTML nào ngoài <li> trong các placeholder



6.2. Format output:

Output PHẢI nằm giữa hai marker sau:

<!-- AI_EMAIL_HTML_START -->

[Template HTML đã được điền đầy đủ]

<!-- AI_EMAIL_HTML_END -->



KHÔNG kèm bất kỳ giải thích nào ngoài HTML giữa hai marker này."""


class IssueAnalyzer:
    """
    Analyzer for GitLab issues using AI providers.

    Supports OpenRouter (recommended) and OpenAI with OpenAI-compatible API interface.
    """

    PROVIDERS = {
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "auth_header": "Authorization",
            "auth_prefix": "Bearer",
        },
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "auth_header": "Authorization",
            "auth_prefix": "Bearer",
        },
    }

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 120,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        enable_reasoning: bool = False,
    ):
        """
        Initialize issue analyzer.

        Args:
            provider: AI provider ('openrouter', 'openai')
            api_key: API key for the provider
            model: Model name to use (e.g., 'tngtech/deepseek-r1t2-chimera:free' for OpenRouter)
            base_url: Optional custom base URL (overrides provider default)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_backoff: Exponential backoff multiplier
            enable_reasoning: Enable reasoning/deepthink mode (for OpenRouter with DeepSeek)
        """
        if provider not in self.PROVIDERS:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported: {', '.join(self.PROVIDERS.keys())}"
            )

        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.enable_reasoning = enable_reasoning

        # Get provider configuration
        provider_config = self.PROVIDERS[provider].copy()

        # Use custom base_url if provided, otherwise use provider default
        if base_url:
            self.base_url = base_url.rstrip("/")
        elif provider_config["base_url"]:
            self.base_url = provider_config["base_url"]
        else:
            raise ValueError(f"base_url must be provided for provider '{provider}'")

        # Build authentication headers
        auth_header = provider_config["auth_header"]
        auth_prefix = provider_config["auth_prefix"]

        auth_value = f"{auth_prefix} {api_key}"
        self.headers = {auth_header: auth_value, "Content-Type": "application/json"}

    def analyze_issue(
        self, issue_data: Dict[str, Any], gitlab_url: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Analyze issue using AI and return WWWH-TR structured analysis.

        Args:
            issue_data: Comprehensive issue data dictionary

        Returns:
            Dictionary with WWWH-TR sections:
            - 'W1': Why section
            - 'W2': What section
            - 'W3': Who section
            - 'H': How section
            - 'T': Test section
            - 'R': Reflect section

        Raises:
            AnalysisError: If analysis fails
            ValueError: If issue_data is empty or invalid
        """
        if not issue_data:
            raise ValueError("issue_data cannot be empty")

        # Prepare prompt
        logger.info("👉 Preparing prompt for AI analysis...")
        prompt = self.prepare_prompt(issue_data, gitlab_url=gitlab_url)

        # Call AI API
        logger.info("👉 Calling to AI chat completion via API...")
        response = self.call_ai_api(prompt)

        # Parse response
        analysis = self.parse_analysis(response)

        return analysis

    def prepare_prompt(
        self, issue_data: Dict[str, Any], gitlab_url: Optional[str] = None
    ) -> str:
        """
        Format comprehensive issue data into analysis prompt.

        Args:
            issue_data: Comprehensive issue data dictionary
            gitlab_url: Optional GitLab instance URL for converting relative image URLs

        Returns:
            Formatted prompt string
        """
        # Get GitLab URL from issue_data if not provided
        if not gitlab_url:
            # Try to extract from web_url
            web_url = issue_data.get("web_url") or issue_data.get("url", "")
            if web_url:
                from urllib.parse import urlparse

                parsed = urlparse(web_url)
                gitlab_url = f"{parsed.scheme}://{parsed.netloc}"

        # Get project_id from issue_data
        project_id = issue_data.get("project_id")

        # Format description with converted image URLs
        description = issue_data.get("description", "")
        if description and gitlab_url:
            description = convert_relative_image_urls(
                description, gitlab_url, project_id
            )

        # Format comments
        comments_text = "Không có comments"
        if issue_data.get("comments"):
            comments_list = []
            for comment in issue_data["comments"]:
                if not comment.get("system", False):  # Skip system notes
                    author = comment.get("author", {})
                    if isinstance(author, dict):
                        author_name = author.get(
                            "username", author.get("name", "Unknown")
                        )
                    else:
                        author_name = "Unknown"

                    body = comment.get("body", "")
                    # Convert relative image URLs in comments too
                    if body and gitlab_url:
                        body = convert_relative_image_urls(body, gitlab_url, project_id)
                    created = comment.get("created_at", "")
                    comments_list.append(f"[{author_name} @ {created}]: {body}")

            comments_text = (
                "\n".join(comments_list) if comments_list else "Không có comments"
            )

        # Format related issues
        related_text = "Không có related issues"
        if issue_data.get("related_issues"):
            related_list = []
            for related in issue_data["related_issues"]:
                if isinstance(related, dict):
                    iid = related.get("iid", related.get("id", "?"))
                    title = related.get("title", "Unknown")
                    link_type = related.get("link_type", "related")
                    related_list.append(f"- #{iid}: {title} ({link_type})")
            related_text = (
                "\n".join(related_list) if related_list else "Không có related issues"
            )

        # Format attachments
        attachments_text = "Không có attachments"
        if issue_data.get("attachments"):
            attachments_list = []
            for att in issue_data["attachments"]:
                url = att.get("url", "")
                source = att.get("source", "unknown")
                attachments_list.append(f"- {url} (từ {source})")
            attachments_text = (
                "\n".join(attachments_list)
                if attachments_list
                else "Không có attachments"
            )

        # Format labels
        labels = issue_data.get("labels", [])
        if labels:
            labels_str = ", ".join(
                [
                    label.get("title", label.get("name", label)) if isinstance(label, dict) else str(label)
                    for label in labels
                ]
            )
        else:
            labels_str = "Không có"

        # Format assignee
        assignee = issue_data.get("assignee")
        if isinstance(assignee, dict):
            assignee_str = assignee.get("username", assignee.get("name", "Unassigned"))
        elif assignee:
            assignee_str = str(assignee)
        else:
            assignee_str = "Chưa được giao"

        # Format author
        author = issue_data.get("author")
        if isinstance(author, dict):
            author_str = author.get("username", author.get("name", "Unknown"))
        elif author:
            author_str = str(author)
        else:
            author_str = "Unknown"

        # Format milestone
        milestone = issue_data.get("milestone")
        if isinstance(milestone, dict):
            milestone_str = milestone.get("title", "None")
        elif milestone:
            milestone_str = str(milestone)
        else:
            milestone_str = "Không có"

        # Count comments
        comment_count = issue_data.get(
            "comment_count", len(issue_data.get("comments", []))
        )

        # Format the main prompt
        main_prompt = USER_PROMPT_TEMPLATE.format(
            title=issue_data.get("title", ""),
            description=description,
            state=issue_data.get("state", "unknown"),
            priority=issue_data.get("priority", "not set"),
            labels=labels_str,
            assignee=assignee_str,
            author=author_str,
            created_at=issue_data.get("created_at", ""),
            updated_at=issue_data.get("updated_at", ""),
            milestone=milestone_str,
            url=issue_data.get("web_url", issue_data.get("url", "")),
            comment_count=comment_count,
            comments=comments_text,
            related_issues=related_text,
            attachments=attachments_text,
        )

        # Get the fixed HTML template with issue metadata filled
        html_template = get_fixed_html_template(issue_data)

        # Append the fixed HTML template to the prompt
        full_prompt = f"""{main_prompt}


────────────────────────────────

7. HTML TEMPLATE (BẮT BUỘC PHẢI SỬ DỤNG)

────────────────────────────────

⚠️ BẠN PHẢI SỬ DỤNG TEMPLATE SAU ĐÂY:

Điền tất cả các placeholder {{TLDR_ITEMS}}, {{ACTION_ITEMS}}, {{OPEN_QUESTIONS}}, {{W1_ITEMS}}, {{W2_ITEMS}}, {{W3_ITEMS}}, {{H_ITEMS}}, {{T_ITEMS}}, {{R_ITEMS}} bằng nội dung phân tích của bạn.

KHÔNG được thay đổi cấu trúc HTML, KHÔNG được thêm/bớt tag nào.

CHỈ được thay thế các placeholder bằng danh sách <li>...</li> hợp lệ.


{html_template}


────────────────────────────────

NHẮC LẠI YÊU CẦU:

1. Phân tích ticket theo WWWH-TR framework
2. Điền đầy đủ tất cả placeholder trong template HTML trên
3. Output HTML đã điền phải nằm giữa <!-- AI_EMAIL_HTML_START --> và <!-- AI_EMAIL_HTML_END -->
4. KHÔNG kèm giải thích ngoài HTML
"""

        return full_prompt

    def call_ai_api(self, prompt: str) -> Dict[str, Any]:
        """
        Make API request to AI provider.

        Args:
            prompt: Formatted prompt string

        Returns:
            API response dictionary

        Raises:
            AnalysisError: If API request fails
        """
        url = f"{self.base_url}/chat/completions"

        # For reasoning mode, increase max_tokens to ensure complete responses
        # Reasoning mode can produce very long outputs, so we need more tokens
        effective_max_tokens = self.max_tokens
        if self.enable_reasoning:
            # Increase max_tokens for reasoning mode to handle longer outputs
            # Default is 2000, but reasoning mode may need 8000-16000 for complete HTML
            effective_max_tokens = max(self.max_tokens, 16000)
            logger.info("👉 Reasoning mode enabled, using max_tokens=16000")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": effective_max_tokens,
            "stream": False,
        }

        # Add reasoning/deepthink mode for OpenRouter
        if self.enable_reasoning and self.provider == "openrouter":
            payload["reasoning"] = {"enabled": True}

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"👉 AI API request attempt {attempt + 1}/{self.max_retries} to {url}"
                )
                response = requests.post(
                    url, headers=self.headers, json=payload, timeout=self.timeout
                )
                response.raise_for_status()
                response_data = response.json()
                logger.info(
                    f"✅ AI API request successful, response keys: {list(response_data.keys())}"
                )
                return response_data

            except Timeout as e:
                if attempt == self.max_retries - 1:
                    raise AnalysisError(
                        f"AI API request timeout after {self.max_retries} attempts: {e}",
                        timeout=True,
                    )
                wait_time = self.retry_backoff**attempt
                time.sleep(wait_time)

            except HTTPError as e:
                status_code = e.response.status_code if e.response else None

                # Don't retry on client errors (4xx), except 429 (rate limit)
                if status_code and 400 <= status_code < 500 and status_code != 429:
                    error_msg = f"AI API error: {e}"
                    if status_code == 401:
                        error_msg = "AI API authentication failed. Check your API key."
                    raise AnalysisError(error_msg, status_code=status_code)

                # Retry on server errors (5xx) and rate limits (429)
                if attempt == self.max_retries - 1:
                    raise AnalysisError(
                        f"AI API error after {self.max_retries} attempts: {e}",
                        status_code=status_code,
                    )

                if status_code == 429:
                    # Rate limited - check Retry-After header and wait
                    retry_after = int(e.response.headers.get("Retry-After", 60))
                    if attempt == self.max_retries - 1:
                        raise AnalysisError(
                            f"AI API rate limit exceeded. Retry after {retry_after} seconds.",
                            status_code=429,
                            retry_after=retry_after,
                        )
                    logger.warning(
                        f"Rate limited, waiting {retry_after} seconds before retry..."
                    )
                    time.sleep(retry_after)
                    continue

                wait_time = self.retry_backoff**attempt
                time.sleep(wait_time)

            except RequestException as e:
                if attempt == self.max_retries - 1:
                    raise AnalysisError(f"Network error: {e}")
                wait_time = self.retry_backoff**attempt
                time.sleep(wait_time)

        raise AnalysisError("AI API request failed after all retries")

    def parse_analysis(self, response: Dict[str, Any]) -> Dict[str, str]:
        """
        Parse AI API response and extract WWWH-TR sections.

        Args:
            response: API response dictionary

        Returns:
            Dictionary with WWWH-TR sections (W1, W2, W3, H, T, R)

        Raises:
            AnalysisError: If response cannot be parsed
        """
        # Extract content from OpenAI-compatible response (OpenRouter, OpenAI)
        content = None

        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            message = choice.get("message", {})

            # Get content from message (handle None explicitly)
            content = message.get("content")

            # Handle None or empty string
            if content is None:
                content = ""

            # If content is empty, check for alternative locations
            if not content:
                finish_reason = choice.get("finish_reason")
                logger.warning(
                    f"Content is empty. finish_reason: {finish_reason}, message keys: {list(message.keys())}"
                )

                # Check if there's a reasoning field in message
                if "reasoning" in message:
                    reasoning_val = message.get("reasoning")
                    if reasoning_val:
                        content = str(reasoning_val)

                # Check if content is in a different location (e.g., direct in choice)
                if not content and "content" in choice:
                    content = choice.get("content")

                # If still empty, try to find any string content in message as fallback
                if not content:
                    for key, value in message.items():
                        if (
                            isinstance(value, str) and len(value) > 50
                        ):  # Reasonable content length
                            content = value
                            break

                # If still empty, this is likely an API issue
                if not content:
                    raise AnalysisError(
                        f"Unable to extract content from AI API response. "
                        f"Response has 'choices' but content is empty. "
                        f"finish_reason: {finish_reason}, message keys: {list(message.keys())}"
                    )
        elif "text" in response:
            content = response["text"]
        else:
            raise AnalysisError(
                f"Unable to extract content from AI API response. Response keys: {list(response.keys())}"
            )

        if not content:
            raise AnalysisError(
                f"Content is empty after extraction. Response structure: {response}"
            )

        # Check if response was truncated (finish_reason == "length")
        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            finish_reason = choice.get("finish_reason")
            if finish_reason == "length":
                logger.warning(
                    f"AI response was truncated due to max_tokens limit! "
                    f"Content length: {len(content)}. "
                    f"Consider increasing max_tokens (current: {self.max_tokens})."
                )

        # Extract HTML from content (between markers)
        logger.info("👉 Prepare HTML template from AI response...")
        html_content = self._extract_html_from_content(content)

        # Validate that HTML is complete (has end marker)
        if html_content and "<!-- AI_EMAIL_HTML_END -->" not in content:
            logger.warning(
                f"HTML end marker not found in response! "
                f"This indicates the AI response was incomplete. "
                f"HTML length: {len(html_content)}, Raw content length: {len(content)}. "
                f"Consider increasing max_tokens (current: {self.max_tokens})."
            )

        if html_content:
            logger.info("✅ HTML template is available")

        return {"html": html_content, "raw": content}

    def _extract_html_from_content(self, content: str) -> str:
        """
        Extract HTML content from AI response between markers.

        Args:
            content: AI response text containing HTML between markers

        Returns:
            Extracted HTML string, or fallback if markers not found
        """
        # Look for HTML between markers
        start_marker = "<!-- AI_EMAIL_HTML_START -->"
        end_marker = "<!-- AI_EMAIL_HTML_END -->"

        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            # Extract HTML between markers
            html = content[start_idx + len(start_marker) : end_idx].strip()
            return html
        elif start_idx != -1 and end_idx == -1:
            # Start marker found but end marker missing - response might be truncated
            logger.warning(
                f"HTML start marker found but end marker missing! "
                f"This indicates the AI response was truncated. "
                f"Content length: {len(content)}, Start position: {start_idx}"
            )
            # Extract from start marker to end of content, but log warning
            html = content[start_idx + len(start_marker) :].strip()
            logger.warning(
                f"Extracted incomplete HTML (length: {len(html)}). "
                f"Consider increasing max_tokens or checking AI response limits."
            )
            return html
        else:
            # Fallback: try to find HTML tags in content
            # Look for any HTML-like content
            if "<table" in content or "<div" in content or "<p" in content:
                # Try to extract HTML block
                html_start = content.find("<")
                html_end = content.rfind(">")
                if html_start != -1 and html_end != -1 and html_end > html_start:
                    html = content[html_start : html_end + 1].strip()
                    return html

            # Last resort: return empty and let reporter handle fallback
            return ""
