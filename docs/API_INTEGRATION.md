# API Integration Guide

Integration details for GitLab API and AI provider APIs.

## GitLab API Integration

### Authentication

**Method**: Personal Access Token

**Headers**:
```http
PRIVATE-TOKEN: glpat-xxxxxxxxxxxx
```

**Token Scopes Required**: `api` (Full API access)

### Endpoints Used

#### 1. Get Issues (Global Endpoint)

**Endpoint**: `GET /api/v4/issues`

**Purpose**: Fetch list of issues from all accessible projects

**Parameters**:
- `state`: `opened` (default)
- `scope`: `all` (optional)
- `labels`: Comma-separated label names (optional)
- `order_by`: `created_at`
- `sort`: `desc`
- `per_page`: `20` (max 100)
- `created_after`: ISO 8601 timestamp

**Example**:
```http
GET /api/v4/issues?scope=all&state=opened&labels=UNIOSS+3&order_by=created_at&sort=desc&per_page=20
Headers:
  PRIVATE-TOKEN: glpat-xxxxxxxxxxxx
```

#### 2. Get Single Issue

**Endpoint**: `GET /api/v4/projects/{project_id}/issues/{issue_iid}`

**Purpose**: Fetch detailed issue information

**Example**:
```http
GET /api/v4/projects/31/issues/366
Headers:
  PRIVATE-TOKEN: glpat-xxxxxxxxxxxx
```

#### 3. Get Issue Notes (Comments)

**Endpoint**: `GET /api/v4/projects/{project_id}/issues/{issue_iid}/notes`

**Purpose**: Fetch all comments/notes for an issue

#### 4. Get Issue Links (Related Issues)

**Endpoint**: `GET /api/v4/projects/{project_id}/issues/{issue_iid}/links`

**Purpose**: Fetch related/linked issues

#### 5. Webhook Events

**Event Type**: `Issue Hook`

**Setup**:
1. GitLab → Project → Settings → Webhooks
2. URL: `https://your-app.com/webhook`
3. Secret token: Your webhook secret
4. Trigger: "Issue events"
5. Enable SSL verification (recommended)

### Rate Limits

- **GitLab.com**: 2000 requests/hour per user
- **Self-hosted**: Depends on instance configuration

**Handling**: Implement request throttling, cache responses when possible, use webhooks instead of polling when available.

## AI API Integration

### Supported Providers

- **OpenRouter** (Recommended): Access to multiple models including DeepSeek with reasoning mode
- **OpenAI**: ChatGPT models (gpt-4, gpt-3.5-turbo, etc.)

### OpenRouter Configuration

**Base URL**: `https://openrouter.ai/api/v1`

**Authentication**: API Key in `Authorization: Bearer` header

**Models**: `tngtech/deepseek-r1t2-chimera:free` (default), `deepseek/deepseek-v3.2`, etc.

**Reasoning Mode**: Enabled by default when `AI_ENABLE_REASONING=true`

**Request Format**:
```json
{
  "model": "tngtech/deepseek-r1t2-chimera:free",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.7,
  "max_tokens": 16000,
  "reasoning": {
    "enabled": true
  }
}
```

### OpenAI Configuration

**Base URL**: `https://api.openai.com/v1`

**Authentication**: API Key in `Authorization: Bearer` header

**Models**: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`

**Request Format**:
```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### Common Endpoint

**Endpoint**: `POST {base_url}/chat/completions` (OpenAI-compatible)

### Prompt Structure

The system sends comprehensive issue data including:

- Issue title, description, metadata
- All comments with authors and timestamps
- Related issues (linked, blocking, blocked by)
- Attachments and images (URLs)
- Additional context

The AI analyzes this data using the WWWH-TR framework and returns structured analysis.

### Error Handling

**Common Errors**:

- **401 Unauthorized**: Invalid API key
- **429 Too Many Requests**: Rate limit exceeded
- **500/503**: Server errors

**Retry Strategy**: Exponential backoff (3 attempts: 1s, 2s, 4s)

### Rate Limits

**Provider-Specific**:
- **OpenRouter**: Varies by model (check current limits)
- **OpenAI**: Varies by tier (free tier: 3 requests/minute, paid: higher)

**Handling**: Implement exponential backoff, queue requests if needed, monitor usage per provider.

### Cost Considerations

**Provider Pricing** (check current pricing):
- **OpenRouter**: Varies by model (DeepSeek models generally lower cost)
- **OpenAI**: Higher cost, excellent quality

**Optimization**:
- Monitor `usage.total_tokens` in responses
- Adjust `max_tokens` based on needs
- Choose provider based on cost/quality trade-off

## Comprehensive Issue Data Fetching

The system fetches comprehensive issue data including:

- Basic issue information (title, description, labels, etc.)
- **All comments and notes** (with author and timestamps)
- **Related/linked issues** (blocking, blocked by, duplicates, relates to)
- **Attachments and images** (extracted from description and comments)
- **Issue relationships** (epics, parent/child issues)

### Data Collection Strategy

1. Get basic issue info
2. Get all comments
3. Get related issues
4. Extract attachments from description and comments
5. Combine all data for AI analysis

### Comment Analysis

- **Include**: All user comments (exclude system notes)
- **Format**: Author, timestamp, and content
- **Purpose**: Understand discussion context, solutions proposed, status updates

### Related Issues Analysis

- **Types**: Blocking, blocked by, duplicates, relates to, closes
- **Purpose**: Understand issue dependencies and relationships

### Attachment Handling

- **Extraction**: Parse markdown links from description and comments
- **Types**: Images, files, screenshots
- **Purpose**: Reference visual information in analysis
- **Note**: URLs are included in prompt; actual file content not downloaded (to save tokens)

## Error Handling

### GitLab API Errors

- **401 Unauthorized**: Invalid or expired token → Verify token and regenerate
- **404 Not Found**: Invalid project ID → Verify project ID/path
- **429 Too Many Requests**: Rate limit exceeded → Implement backoff, reduce polling frequency
- **500 Internal Server Error**: GitLab server issue → Retry with exponential backoff

### AI API Errors

- **401 Unauthorized**: Invalid API key → Verify API key for selected provider
- **429 Too Many Requests**: Rate limit exceeded → Implement backoff, reduce request frequency
- **500/503**: Server errors → Retry with exponential backoff, consider fallback provider

### Retry Strategy

```python
def retry_with_backoff(func, max_retries=3, backoff_factor=2.0, initial_delay=1.0):
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
    raise Exception("Max retries exceeded")
```

## Best Practices

1. **Error Handling**: Always handle API errors gracefully
2. **Rate Limiting**: Implement rate limiting to avoid hitting limits
3. **Retries**: Use exponential backoff for retries
4. **Logging**: Log all API calls and errors
5. **Timeouts**: Set appropriate timeouts for API calls (default: 30 seconds)
6. **Validation**: Validate API responses before processing
7. **Caching**: Cache responses when appropriate (analysis cache for processed issues)
8. **Monitoring**: Monitor API usage and costs

## Next Steps

1. Configure GitLab API token
2. Configure AI provider API key
3. Test API connectivity
4. Monitor API usage and costs
5. Set up error alerts
