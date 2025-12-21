# API Integration Guide

This document details the integration with GitLab API and DeepSeek API.

## Table of Contents

1. [GitLab API Integration](#gitlab-api-integration)
2. [DeepSeek API Integration](#deepseek-api-integration)
3. [Error Handling](#error-handling)
4. [Rate Limiting](#rate-limiting)
5. [Testing](#testing)

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

#### 1. Get Project Issues

**Endpoint**: `GET /api/v4/projects/{project_id}/issues`

**Purpose**: Fetch list of issues (polling mode)

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

#### 2. Get Single Issue

**Endpoint**: `GET /api/v4/projects/{project_id}/issues/{issue_iid}`

**Purpose**: Fetch detailed issue information

**Example Request**:
```http
GET /api/v4/projects/123456/issues/5
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

## DeepSeek API Integration

### Overview

The application uses DeepSeek Chat API to analyze GitLab issues using the WWWH-TR framework.

### Authentication

**Method**: API Key

**Headers**:
```http
Authorization: Bearer sk-xxxxxxxxxxxx
Content-Type: application/json
```

### API Endpoint

**Endpoint**: `POST https://api.deepseek.com/v1/chat/completions`

### Request Format

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
SYSTEM_PROMPT = """You are an expert software development analyst. Analyze GitLab issues using the WWWH-TR thinking framework and provide structured, actionable insights."""

USER_PROMPT_TEMPLATE = """Analyze the following GitLab issue using the WWWH-TR framework:

Title: {title}
Description: {description}
Labels: {labels}
Assignee: {assignee}
URL: {url}

Please provide a comprehensive analysis structured as follows:

**W1 — Why**: Why is this needed? Understand the root cause and identify the ultimate goal.

**W2 — What**: What specifically? Identify the problem and gather relevant information.

**W3 — Who**: Who is involved or affected? Identify stakeholders and people who can help.

**H — How**: What are the possible approaches? Identify feasible solutions, compare them, and discuss trade-offs.

**T — Test**: How to test small? Suggest quick experiments and measurement milestones (feasibility, time, cost, etc.).

**R — Reflect**: What is the best choice? Provide evaluation, conclusion, next steps, and potential adjustments.

Be concise but thorough. Focus on actionable insights."""
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
from typing import Dict

class DeepSeekAnalyzer:
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def analyze_issue(self, issue_data: Dict) -> str:
        """Analyze issue using DeepSeek API"""
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
        """Build analysis prompt from issue data"""
        return USER_PROMPT_TEMPLATE.format(
            title=issue_data.get('title', ''),
            description=issue_data.get('description', ''),
            labels=', '.join(issue_data.get('labels', [])),
            assignee=issue_data.get('assignee', {}).get('username', 'Unassigned'),
            url=issue_data.get('web_url', '')
        )
```

### Rate Limits

- **Free Tier**: Check DeepSeek documentation for current limits
- **Paid Tier**: Higher limits available

**Handling**:
- Implement exponential backoff
- Queue requests if needed
- Monitor usage

### Cost Considerations

- **Pricing**: Check DeepSeek pricing page
- **Token Usage**: Monitor `usage.total_tokens` in responses
- **Optimization**: Adjust `max_tokens` based on needs

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

#### DeepSeek API Errors

**401 Unauthorized**:
- Invalid API key
- Solution: Verify API key

**429 Too Many Requests**:
- Rate limit exceeded
- Solution: Implement backoff, reduce request frequency

**500 Internal Server Error**:
- DeepSeek server issue
- Solution: Retry with exponential backoff

**503 Service Unavailable**:
- Service temporarily unavailable
- Solution: Retry with exponential backoff

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


