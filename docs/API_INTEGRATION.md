# API Integration Guide

This document details the integration with GitLab API and AI APIs (OpenRouter, OpenAI).

## Table of Contents

1. [GitLab API Integration](#gitlab-api-integration)
2. [AI API Integration](#ai-api-integration)
3. [Comprehensive Issue Data Fetching](#comprehensive-issue-data-fetching)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Testing](#testing)

## GitLab API Integration

### Overview

The application uses GitLab REST API v4 to:
- Fetch issue details
- Monitor new issues (polling mode)
- Receive webhook events (webhook mode)

### Authentication

**Method**: Personal Access Token

**Headers**:
```http
PRIVATE-TOKEN: glpat-xxxxxxxxxxxx
```

**Token Scopes Required**:
- `api` - Full API access

### API Endpoints Used

#### 1. Get Issues (Global Endpoint - Recommended)

**Endpoint**: `GET /api/v4/issues`

**Purpose**: Fetch list of issues from all accessible projects (polling mode)

**When to Use**: When `project_id` is not configured (recommended for multi-project monitoring)

**Parameters**:
- `state`: `opened` (default) - Issue state filter
- `scope`: `all` (optional) - Scope filter (all, assigned_to_me, created_by_me, etc.)
- `labels`: `UNIOSS 3` (optional) - Comma-separated label names
- `order_by`: `created_at`
- `sort`: `desc`
- `per_page`: `20` (max 100)
- `created_after`: ISO 8601 timestamp (for filtering new issues)

**Example Request**:
```http
GET /api/v4/issues?scope=all&state=opened&labels=UNIOSS+3&order_by=created_at&sort=desc&per_page=20
Headers:
  PRIVATE-TOKEN: glpat-xxxxxxxxxxxx
```

**Example Response**:
```json
[
  {
    "id": 3664,
    "iid": 366,
    "project_id": 31,
    "title": "Issue title",
    "description": "Issue description...",
    "state": "opened",
    "created_at": "2025-12-23T12:00:03.030+09:00",
    "updated_at": "2025-12-23T17:23:23.249+09:00",
    "labels": ["UNIOSS 3", "優先度 中", "改修依頼"],
    "web_url": "https://gitlab.unioss.jp/unioss/FrontEnd/-/issues/366"
  }
]
```

#### 2. Get Project Issues (Legacy - Project-Specific)

**Endpoint**: `GET /api/v4/projects/{project_id}/issues`

**Purpose**: Fetch list of issues from a specific project (polling mode)

**When to Use**: When `project_id` is configured (single project monitoring)

**Parameters**:
- `state`: `opened` (default)
- `order_by`: `created_at`
- `sort`: `desc`
- `per_page`: `20` (max 100)
- `created_after`: ISO 8601 timestamp (for filtering new issues)

**Example Request**:
```http
GET /api/v4/projects/123456/issues?state=opened&order_by=created_at&sort=desc&per_page=20
Headers:
  PRIVATE-TOKEN: glpat-xxxxxxxxxxxx
```

**Example Response**:
```json
[
  {
    "id": 123,
    "iid": 5,
    "title": "Fix login bug",
    "description": "Users cannot login...",
    "state": "opened",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z",
    "labels": ["bug", "urgent"],
    "assignee": {
      "id": 1,
      "username": "developer"
    },
    "web_url": "https://gitlab.com/project/issues/5"
  }
]
```

#### 3. Get Single Issue

**Endpoint**: `GET /api/v4/projects/{project_id}/issues/{issue_iid}`

**Purpose**: Fetch detailed issue information

**Note**: When using global endpoint, `project_id` is extracted from the issue data returned by the list endpoint.

**Example Request**:
```http
GET /api/v4/projects/31/issues/366
Headers:
  PRIVATE-TOKEN: glpat-xxxxxxxxxxxx
```

**Example Response**:
```json
{
  "id": 123,
  "iid": 5,
  "title": "Fix login bug",
  "description": "Users cannot login with email...",
  "state": "opened",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z",
  "labels": ["bug", "urgent"],
  "assignee": {
    "id": 1,
    "username": "developer",
    "name": "Developer Name"
  },
  "author": {
    "id": 2,
    "username": "reporter",
    "name": "Reporter Name"
  },
  "milestone": null,
  "web_url": "https://gitlab.com/project/issues/5"
}
```

#### 3. Get Issue Notes (Comments)

**Endpoint**: `GET /api/v4/projects/{project_id}/issues/{issue_iid}/notes`

**Purpose**: Fetch all comments/notes for an issue

**Example Request**:
```http
GET /api/v4/projects/123456/issues/5/notes
Headers:
  PRIVATE-TOKEN: glpat-xxxxxxxxxxxx
```

**Example Response**:
```json
[
  {
    "id": 1,
    "body": "I've reproduced this issue...",
    "author": {
      "id": 1,
      "username": "developer",
      "name": "Developer Name"
    },
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z",
    "system": false,
    "noteable_type": "Issue"
  }
]
```

#### 4. Get Issue Links (Related Issues)

**Endpoint**: `GET /api/v4/projects/{project_id}/issues/{issue_iid}/links`

**Purpose**: Fetch related/linked issues

**Example Request**:
```http
GET /api/v4/projects/123456/issues/5/links
Headers:
  PRIVATE-TOKEN: glpat-xxxxxxxxxxxx
```

**Example Response**:
```json
[
  {
    "source_issue": {
      "id": 123,
      "iid": 5,
      "title": "Fix login bug"
    },
    "target_issue": {
      "id": 124,
      "iid": 6,
      "title": "Related authentication issue"
    },
    "link_type": "relates_to"
  }
]
```

#### 5. Get Issue Attachments

**Endpoint**: Issue description and notes may contain attachment references

**Purpose**: Extract attachment URLs from issue description and comments

**Note**: GitLab stores attachments in the issue description/notes as markdown links. Extract these for analysis.

#### 3. Webhook Events

**Event Type**: `Issue Hook`

**Payload Structure**:
```json
{
  "object_kind": "issue",
  "event_type": "issue",
  "user": {
    "name": "User Name",
    "username": "username"
  },
  "project": {
    "id": 123456,
    "name": "Project Name"
  },
  "object_attributes": {
    "id": 123,
    "iid": 5,
    "title": "Fix login bug",
    "description": "Users cannot login...",
    "state": "opened",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z",
    "labels": [
      {
        "id": 1,
        "title": "bug",
        "color": "#d9534f"
      }
    ],
    "assignee_id": 1,
    "url": "https://gitlab.com/project/issues/5"
  }
}
```

**Webhook Setup**:
1. Go to Project → Settings → Webhooks
2. URL: `https://your-app.com/webhook`
3. Secret token: Your webhook secret
4. Trigger: "Issue events"
5. Enable SSL verification (recommended)

### Implementation Example

```python
import requests
from typing import Dict, List, Optional

class GitLabClient:
    def __init__(self, url: str, token: str, project_id: str):
        self.url = url.rstrip('/')
        self.token = token
        self.project_id = project_id
        self.headers = {
            'PRIVATE-TOKEN': token,
            'Content-Type': 'application/json'
        }
    
    def get_issues(self, created_after: Optional[str] = None) -> List[Dict]:
        """Fetch issues from GitLab"""
        endpoint = f"{self.url}/api/v4/projects/{self.project_id}/issues"
        params = {
            'state': 'opened',
            'order_by': 'created_at',
            'sort': 'desc',
            'per_page': 20
        }
        
        if created_after:
            params['created_after'] = created_after
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_issue(self, issue_iid: int) -> Dict:
        """Fetch single issue details"""
        endpoint = f"{self.url}/api/v4/projects/{self.project_id}/issues/{issue_iid}"
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_issue_notes(self, issue_iid: int) -> List[Dict]:
        """Fetch all comments/notes for an issue"""
        endpoint = f"{self.url}/api/v4/projects/{self.project_id}/issues/{issue_iid}/notes"
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_issue_links(self, issue_iid: int) -> List[Dict]:
        """Fetch related/linked issues"""
        endpoint = f"{self.url}/api/v4/projects/{self.project_id}/issues/{issue_iid}/links"
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError:
            # Links API may not be available in all GitLab versions
            return []
    
    def get_comprehensive_issue_data(self, issue_iid: int) -> Dict:
        """Fetch all issue data including comments, links, and attachments"""
        issue = self.get_issue(issue_iid)
        notes = self.get_issue_notes(issue_iid)
        links = self.get_issue_links(issue_iid)
        
        # Extract attachments from description and notes
        attachments = self._extract_attachments(issue.get('description', ''), notes)
        
        return {
            **issue,
            'comments': notes,
            'related_issues': links,
            'attachments': attachments,
            'comment_count': len(notes)
        }
    
    def _extract_attachments(self, description: str, notes: List[Dict]) -> List[Dict]:
        """Extract attachment URLs from description and notes"""
        import re
        attachments = []
        
        # Extract markdown image links and file links
        pattern = r'!\[.*?\]\((.*?)\)|\[.*?\]\((.*?)\)'
        
        for match in re.finditer(pattern, description):
            url = match.group(1) or match.group(2)
            if url and ('uploads' in url or url.startswith('http')):
                attachments.append({'url': url, 'source': 'description'})
        
        for note in notes:
            body = note.get('body', '')
            for match in re.finditer(pattern, body):
                url = match.group(1) or match.group(2)
                if url and ('uploads' in url or url.startswith('http')):
                    attachments.append({
                        'url': url,
                        'source': 'comment',
                        'comment_id': note.get('id')
                    })
        
        return attachments
    
    def parse_webhook(self, payload: Dict) -> Dict:
        """Parse webhook payload"""
        return {
            'id': payload['object_attributes']['id'],
            'iid': payload['object_attributes']['iid'],
            'title': payload['object_attributes']['title'],
            'description': payload['object_attributes']['description'],
            'state': payload['object_attributes']['state'],
            'url': payload['object_attributes']['url'],
            'labels': [label['title'] for label in payload['object_attributes'].get('labels', [])],
            'created_at': payload['object_attributes']['created_at']
        }
```

### Rate Limits

- **GitLab.com**: 2000 requests/hour per user
- **Self-hosted**: Depends on instance configuration

**Handling**:
- Implement request throttling
- Cache responses when possible
- Use webhooks instead of polling when available

## Comprehensive Issue Data Fetching

### Overview

The system fetches comprehensive issue data including:
- Basic issue information (title, description, labels, etc.)
- **All comments and notes** (with author and timestamps)
- **Related/linked issues** (blocking, blocked by, duplicates, relates to)
- **Attachments and images** (extracted from description and comments)
- **Issue relationships** (epics, parent/child issues)

### Data Collection Strategy

```python
def get_comprehensive_issue_data(issue_iid: int) -> Dict:
    """Fetch all relevant issue data"""
    # 1. Get basic issue info
    issue = gitlab_client.get_issue(issue_iid)
    
    # 2. Get all comments
    comments = gitlab_client.get_issue_notes(issue_iid)
    
    # 3. Get related issues
    related_issues = gitlab_client.get_issue_links(issue_iid)
    
    # 4. Extract attachments from description and comments
    attachments = extract_attachments(issue['description'], comments)
    
    # 5. Combine all data
    return {
        **issue,
        'comments': comments,
        'related_issues': related_issues,
        'attachments': attachments,
        'comment_count': len(comments)
    }
```

### Comment Analysis

- **Include**: All user comments (exclude system notes)
- **Format**: Author, timestamp, and content
- **Purpose**: Understand discussion context, solutions proposed, status updates

### Related Issues Analysis

- **Types**: Blocking, blocked by, duplicates, relates to, closes
- **Purpose**: Understand issue dependencies and relationships
- **Usage**: Reference related issues in analysis for context

### Attachment Handling

- **Extraction**: Parse markdown links from description and comments
- **Types**: Images, files, screenshots
- **Purpose**: Reference visual information in analysis
- **Note**: URLs are included in prompt; actual file content not downloaded (to save tokens)

## AI API Integration

### Overview

The application supports multiple AI providers to analyze GitLab issues using the WWWH-TR framework. 

**Recommended Setup**: OpenRouter with DeepSeek v3.2 (with reasoning mode enabled)

Supported providers:
- **OpenRouter** (Recommended) - Access to DeepSeek v3.2 with reasoning/deepthink mode
- **OpenAI** - ChatGPT models (gpt-4, gpt-3.5-turbo, etc.)

The system uses an OpenAI-compatible API interface.

### Provider-Specific Configuration

#### OpenRouter (Recommended)
- **Base URL**: `https://openrouter.ai/api/v1`
- **Authentication**: API Key in `Authorization: Bearer` header
- **Models**: `deepseek/deepseek-v3.2` (recommended with reasoning mode)
- **Reasoning Mode**: Enabled by default when `enable_reasoning=true`
- **Request Format**: Includes `"reasoning": {"enabled": true}` in payload
- **How to Get API Key**: Sign up at [OpenRouter](https://openrouter.ai/)

**Example Request with Reasoning:**
```json
{
  "model": "deepseek/deepseek-v3.2",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "reasoning": {
    "enabled": true
  }
}
```

#### OpenAI ChatGPT
- **Base URL**: `https://api.openai.com/v1`
- **Authentication**: API Key in `Authorization: Bearer` header
- **Models**: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`

### Common API Endpoint

**Endpoint**: `POST {base_url}/chat/completions` (OpenAI-compatible)

### Request Format

**Standard Request (OpenRouter with Reasoning):**
```json
{
  "model": "deepseek/deepseek-v3.2",
  "messages": [
    {
      "role": "system",
      "content": "You are an expert software development analyst..."
    },
    {
      "role": "user",
      "content": "Analyze the following GitLab issue using WWWH-TR framework:\n\nTitle: Fix login bug\nDescription: Users cannot login..."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "stream": false,
  "reasoning": {
    "enabled": true
  }
}
```

**Standard Request (Other Providers):**
```json
{
  "model": "deepseek-chat",
  "messages": [
    {
      "role": "system",
      "content": "You are an expert software development analyst..."
    },
    {
      "role": "user",
      "content": "Analyze the following GitLab issue using WWWH-TR framework:\n\nTitle: Fix login bug\nDescription: Users cannot login..."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "stream": false
}
```

### Prompt Template

```python
SYSTEM_PROMPT = """You are an expert software development analyst. Analyze GitLab issues using the WWWH-TR thinking framework and provide structured, actionable insights. Consider all available information including comments, related issues, and attachments."""

USER_PROMPT_TEMPLATE = """Analyze the following GitLab issue using the WWWH-TR framework:

=== ISSUE INFORMATION ===
Title: {title}
Description: {description}
State: {state}
Priority: {priority}
Labels: {labels}
Assignee: {assignee}
Author: {author}
Created: {created_at}
Updated: {updated_at}
Milestone: {milestone}
URL: {url}

=== COMMENTS ({comment_count} total) ===
{comments}

=== RELATED ISSUES ===
{related_issues}

=== ATTACHMENTS & IMAGES ===
{attachments}

Please provide a comprehensive analysis structured as follows:

**W1 — Why**: Why is this needed? Understand the root cause and identify the ultimate goal. Consider context from comments and related issues.

**W2 — What**: What specifically? Identify the problem and gather relevant information. Reference any attachments or images if relevant.

**W3 — Who**: Who is involved or affected? Identify stakeholders and people who can help. Consider comment authors and assignees.

**H — How**: What are the possible approaches? Identify feasible solutions, compare them, and discuss trade-offs. Consider solutions mentioned in comments.

**T — Test**: How to test small? Suggest quick experiments and measurement milestones (feasibility, time, cost, etc.).

**R — Reflect**: What is the best choice? Provide evaluation, conclusion, next steps, and potential adjustments. Synthesize insights from all available information.

Be concise but thorough. Focus on actionable insights. If comments or related issues provide important context, reference them in your analysis."""
```

### Response Format

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "deepseek-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "**W1 — Why**: ...\n\n**W2 — What**: ...\n\n..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 800,
    "total_tokens": 950
  }
}
```

### Implementation Example

```python
import requests
from typing import Dict, List, Optional

class AIAnalyzer:
    """Universal AI analyzer supporting multiple providers"""
    
    PROVIDERS = {
        'openrouter': {
            'base_url': 'https://openrouter.ai/api/v1',
            'auth_header': 'Authorization',
            'auth_prefix': 'Bearer'
        },
        'openai': {
            'base_url': 'https://api.openai.com/v1',
            'auth_header': 'Authorization',
            'auth_prefix': 'Bearer'
        }
    }
    
    def __init__(self, provider: str, api_key: str, model: str, enable_reasoning: bool = False):
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
        
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.enable_reasoning = enable_reasoning
        self.config = self.PROVIDERS[provider]
        self.base_url = self.config['base_url']
        
        # Build headers
        auth_value = f"{self.config['auth_prefix']} {api_key}"
        self.headers = {
            self.config['auth_header']: auth_value,
            'Content-Type': 'application/json'
        }
    
    def analyze_issue(self, issue_data: Dict) -> str:
        """Analyze issue using configured AI provider"""
        prompt = self._build_prompt(issue_data)
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": False
        }
        
        # Add reasoning mode for OpenRouter
        if self.enable_reasoning and self.provider == 'openrouter':
            payload["reasoning"] = {"enabled": True}
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _build_prompt(self, issue_data: Dict) -> str:
        """Build comprehensive analysis prompt from issue data"""
        # Format comments
        comments_text = "No comments"
        if issue_data.get('comments'):
            comments_list = []
            for comment in issue_data['comments']:
                if not comment.get('system', False):  # Skip system notes
                    author = comment.get('author', {}).get('username', 'Unknown')
                    body = comment.get('body', '')
                    created = comment.get('created_at', '')
                    comments_list.append(f"[{author} @ {created}]: {body}")
            comments_text = "\n".join(comments_list) if comments_list else "No comments"
        
        # Format related issues
        related_text = "No related issues"
        if issue_data.get('related_issues'):
            related_list = []
            for link in issue_data['related_issues']:
                target = link.get('target_issue', {})
                related_list.append(f"- #{target.get('iid')}: {target.get('title')} ({link.get('link_type', 'related')})")
            related_text = "\n".join(related_list) if related_list else "No related issues"
        
        # Format attachments
        attachments_text = "No attachments"
        if issue_data.get('attachments'):
            attachments_list = []
            for att in issue_data['attachments']:
                attachments_list.append(f"- {att.get('url')} (from {att.get('source', 'unknown')})")
            attachments_text = "\n".join(attachments_list) if attachments_list else "No attachments"
        
        return USER_PROMPT_TEMPLATE.format(
            title=issue_data.get('title', ''),
            description=issue_data.get('description', ''),
            state=issue_data.get('state', 'unknown'),
            priority=issue_data.get('priority', 'not set'),
            labels=', '.join([l.get('name', l) if isinstance(l, dict) else l for l in issue_data.get('labels', [])]),
            assignee=issue_data.get('assignee', {}).get('username', 'Unassigned') if isinstance(issue_data.get('assignee'), dict) else 'Unassigned',
            author=issue_data.get('author', {}).get('username', 'Unknown') if isinstance(issue_data.get('author'), dict) else 'Unknown',
            created_at=issue_data.get('created_at', ''),
            updated_at=issue_data.get('updated_at', ''),
            milestone=issue_data.get('milestone', {}).get('title', 'None') if isinstance(issue_data.get('milestone'), dict) else 'None',
            url=issue_data.get('web_url', ''),
            comment_count=issue_data.get('comment_count', len(issue_data.get('comments', []))),
            comments=comments_text,
            related_issues=related_text,
            attachments=attachments_text
        )
```

### Rate Limits

**Provider-Specific Limits**:
- **DeepSeek**: Check DeepSeek documentation for current limits
- **OpenAI**: Varies by tier (free tier: 3 requests/minute, paid: higher)
- **Anthropic**: Varies by tier (check current limits)

**Handling**:
- Implement exponential backoff
- Queue requests if needed
- Monitor usage per provider
- Provider-specific rate limit handling

### Cost Considerations

**Provider Pricing** (check current pricing):
- **OpenRouter**: Varies by model (DeepSeek models generally lower cost, good for high volume)
- **OpenAI**: Higher cost, excellent quality

**Optimization**:
- Monitor `usage.total_tokens` in responses
- Adjust `max_tokens` based on needs
- Choose provider based on cost/quality trade-off
- Use cheaper models for simple issues, premium for complex ones

## Error Handling

### Common Errors

#### GitLab API Errors

**401 Unauthorized**:
- Invalid or expired token
- Solution: Verify token and regenerate if needed

**404 Not Found**:
- Invalid project ID
- Solution: Verify project ID/path

**429 Too Many Requests**:
- Rate limit exceeded
- Solution: Implement backoff, reduce polling frequency

**500 Internal Server Error**:
- GitLab server issue
- Solution: Retry with exponential backoff

#### AI API Errors

**401 Unauthorized**:
- Invalid API key
- Solution: Verify API key for selected provider

**429 Too Many Requests**:
- Rate limit exceeded
- Solution: Implement backoff, reduce request frequency, consider switching providers

**500 Internal Server Error**:
- AI provider server issue
- Solution: Retry with exponential backoff, consider fallback provider

**503 Service Unavailable**:
- Service temporarily unavailable
- Solution: Retry with exponential backoff, consider fallback provider

**Provider-Specific Errors**:
- **OpenRouter**: Check for model availability errors and regional restrictions
- **OpenAI**: Check for model availability errors

### Retry Strategy

```python
import time
from typing import Callable, Any

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0
) -> Any:
    """Retry function with exponential backoff"""
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            return func()
        except requests.HTTPError as e:
            if e.response.status_code in [429, 500, 503]:
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= backoff_factor
                    continue
            raise
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= backoff_factor
                continue
            raise
    
    raise Exception("Max retries exceeded")
```

## Rate Limiting

### Implementation

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Remove old requests outside time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # Wait if at limit
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.wait_if_needed()
            else:
                self.requests.popleft()
        
        self.requests.append(time.time())
```

## Testing

### Unit Tests

```python
import unittest
from unittest.mock import Mock, patch

class TestGitLabClient(unittest.TestCase):
    @patch('requests.get')
    def test_get_issues(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = [{'id': 1, 'title': 'Test'}]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = GitLabClient('https://gitlab.com', 'token', '123')
        issues = client.get_issues()
        
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]['title'], 'Test')
```

### Integration Tests

```python
# Test with real API (use test credentials)
def test_gitlab_integration():
    client = GitLabClient(
        url=os.getenv('GITLAB_URL'),
        token=os.getenv('GITLAB_TOKEN'),
        project_id=os.getenv('TEST_PROJECT_ID')
    )
    issues = client.get_issues()
    assert isinstance(issues, list)
```

## Best Practices

1. **Error Handling**: Always handle API errors gracefully
2. **Rate Limiting**: Implement rate limiting to avoid hitting limits
3. **Retries**: Use exponential backoff for retries
4. **Logging**: Log all API calls and errors
5. **Timeouts**: Set appropriate timeouts for API calls
6. **Validation**: Validate API responses before processing
7. **Caching**: Cache responses when appropriate
8. **Monitoring**: Monitor API usage and costs

## Next Steps

1. Implement API clients based on this guide
2. Add comprehensive error handling
3. Implement rate limiting
4. Add logging and monitoring
5. Write unit and integration tests


