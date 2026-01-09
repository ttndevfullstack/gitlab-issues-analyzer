# Configuration Guide

Complete reference for all configuration options in GitLab Issues Analyzer.

## Configuration Method

Configuration is done via **environment variables** only. Load from `.env` file or system environment.

## GitLab Configuration

### Required

#### `GITLAB_URL`
- **Type**: String
- **Description**: GitLab instance URL
- **Examples**: 
  - `https://gitlab.com` (GitLab.com)
  - `https://gitlab.example.com` (Self-hosted)
- **Required**: Yes

#### `GITLAB_TOKEN`
- **Type**: String
- **Description**: GitLab Personal Access Token
- **How to Get**: 
  1. GitLab → Settings → Access Tokens
  2. Create token with `api` scope
  3. Copy token (starts with `glpat-` or `gl-`)
- **Security**: Never commit to version control
- **Required**: Yes

### Optional

#### `GITLAB_ISSUE_SCOPE`
- **Type**: String
- **Description**: Scope filter for global issues endpoint
- **Options**: `all`, `assigned_to_me`, `created_by_me`
- **Default**: `null` (no filter)
- **Example**: `GITLAB_ISSUE_SCOPE=all`

#### `GITLAB_ISSUE_LABELS`
- **Type**: String (comma-separated)
- **Description**: Filter issues by label names
- **Example**: `GITLAB_ISSUE_LABELS=UNIOSS 3,bug`
- **Default**: `null` (no filter)

## AI Provider Configuration

### Required

#### `AI_PROVIDER`
- **Type**: String
- **Description**: AI provider to use
- **Options**: `openrouter` (recommended), `openai`
- **Default**: `openrouter`
- **Required**: Yes

#### `AI_API_KEY`
- **Type**: String
- **Description**: API key for selected provider
- **How to Get**:
  - **OpenRouter**: Sign up at [openrouter.ai](https://openrouter.ai/)
  - **OpenAI**: Sign up at [platform.openai.com](https://platform.openai.com/)
- **Security**: Never commit to version control
- **Required**: Yes

### Optional

#### `AI_MODEL`
- **Type**: String
- **Description**: AI model identifier
- **Default**: `tngtech/deepseek-r1t2-chimera:free`
- **Examples**:
  - OpenRouter: `tngtech/deepseek-r1t2-chimera:free`, `deepseek/deepseek-v3.2`
  - OpenAI: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`
- **Note**: Format is `provider/model-name` for OpenRouter

#### `AI_MAX_TOKENS`
- **Type**: Integer
- **Description**: Maximum tokens in AI response
- **Default**: `2000`
- **Recommended**: `16000` when `AI_ENABLE_REASONING=true`
- **Range**: 1-16000+ (varies by provider/model)

#### `AI_ENABLE_REASONING`
- **Type**: Boolean
- **Description**: Enable reasoning/deepthink mode (OpenRouter only)
- **Default**: `true`
- **Note**: Adds `"reasoning": {"enabled": true}` to API request. Only works with compatible models.

## SMTP Configuration

### Required

#### `SMTP_HOST`
- **Type**: String
- **Description**: SMTP server hostname
- **Common Values**:
  - Gmail: `smtp.gmail.com`
  - Outlook: `smtp-mail.outlook.com`
  - Yahoo: `smtp.mail.yahoo.com`
- **Required**: Yes

#### `SMTP_PORT`
- **Type**: Integer
- **Description**: SMTP server port
- **Common Values**: `587` (TLS, recommended), `465` (SSL), `25` (not recommended)
- **Default**: `587`
- **Required**: Yes

#### `SMTP_USERNAME`
- **Type**: String
- **Description**: SMTP username (usually your email)
- **Example**: `your-email@gmail.com`
- **Required**: Yes

#### `SMTP_PASSWORD`
- **Type**: String
- **Description**: SMTP password or app password
- **Note**: For Gmail, use App Password (not regular password)
- **Security**: Never commit to version control
- **Required**: Yes

#### `SMTP_FROM_EMAIL`
- **Type**: String
- **Description**: Sender email address
- **Example**: `your-email@gmail.com`
- **Note**: Usually same as `SMTP_USERNAME`
- **Required**: Yes

#### `SMTP_TO_EMAIL`
- **Type**: String or comma-separated list
- **Description**: Recipient email address(es)
- **Examples**: 
  - Single: `recipient@example.com`
  - Multiple: `email1@example.com,email2@example.com`
- **Required**: Yes

## Application Configuration

### Optional Settings

#### `APP_MODE`
- **Type**: String
- **Description**: Application operation mode
- **Options**: `poll` (periodic checks), `webhook` (real-time events)
- **Default**: `poll`
- **Example**: `APP_MODE=poll`

#### `ENVIRONMENT`
- **Type**: String
- **Description**: Application environment
- **Options**: `production`, `development`, `testing`
- **Default**: `production`
- **Behavior**:
  - `production`: Standard settings, 15-minute poll interval
  - `development`: Debug logging, shorter intervals, Flask auto-reload
  - `testing`: 1 issue per poll, 1-minute interval, debug logging

#### `ENABLE_AUTOMATION`
- **Type**: Boolean
- **Description**: Enable automated polling/webhook processing
- **Default**: `true`
- **Note**: When `false`, automatic processing is disabled but dashboard and manual triggers remain available

#### `POLL_INTERVAL`
- **Type**: Integer
- **Description**: Polling interval in seconds (polling mode only)
- **Default**: `900` (15 minutes)
- **Examples**: `300` (5 min), `900` (15 min), `3600` (1 hour)
- **Note**: Lower intervals may hit rate limits

#### `MAX_ISSUES_PER_POLL`
- **Type**: Integer
- **Description**: Limit number of issues processed per polling cycle
- **Default**: `null` (unlimited)
- **Use Case**: Testing mode - process only 1 issue at a time
- **Example**: `MAX_ISSUES_PER_POLL=1`
- **Note**: Automatically set to `1` in `testing` environment if not specified

#### `ISSUE_START_TIME`
- **Type**: String (ISO 8601 timestamp)
- **Description**: Only process issues created after this time
- **Formats**:
  - `2026-01-05T00:00:00Z` (ISO 8601 with UTC - recommended)
  - `2026-01-05 00:00:00` (space-separated, normalized to UTC)
  - `2026-01-05T00:00:00+07:00` (with timezone offset)
- **Default**: Current time (only new issues after startup)
- **Use Case**: Local development to avoid reprocessing existing issues

#### `LOG_LEVEL`
- **Type**: String
- **Description**: Logging verbosity level
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Default**: `INFO`

#### `TIMEZONE`
- **Type**: String
- **Description**: Timezone for log timestamps
- **Default**: `Asia/Ho_Chi_Minh`
- **Example**: `TIMEZONE=UTC`, `TIMEZONE=America/New_York`
- **Format**: IANA timezone identifier

#### `APP_VERSION`
- **Type**: String
- **Description**: Application version displayed in UI
- **Default**: `1.0.0`
- **Example**: `APP_VERSION=1.2.3`

#### `WEBHOOK_PORT`
- **Type**: Integer
- **Description**: Port for webhook server and dashboard
- **Default**: `8000`
- **Example**: `WEBHOOK_PORT=8080`

## Configuration Examples

### Minimal Production Setup

```bash
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=glpat-xxxxx
GITLAB_ISSUE_SCOPE=all
GITLAB_ISSUE_LABELS=bug,feature

AI_PROVIDER=openrouter
AI_API_KEY=sk-or-xxxxx
AI_MODEL=tngtech/deepseek-r1t2-chimera:free

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=user@gmail.com
SMTP_PASSWORD=app-password
SMTP_FROM_EMAIL=user@gmail.com
SMTP_TO_EMAIL=recipient@example.com

APP_MODE=poll
ENVIRONMENT=production
```

### Development Setup

```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
POLL_INTERVAL=300
MAX_ISSUES_PER_POLL=1
ISSUE_START_TIME=2026-01-01T00:00:00Z
```

### Testing Setup

```bash
ENVIRONMENT=testing
LOG_LEVEL=DEBUG
# MAX_ISSUES_PER_POLL automatically set to 1
# POLL_INTERVAL automatically set to 60
```

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use App Passwords** for Gmail/Outlook instead of regular passwords
3. **Rotate credentials** periodically
4. **Use environment variables** in production (not `.env` files)
5. **Validate configuration** on startup (automatic)

## Validation

Configuration is validated on startup. The application will fail fast with clear error messages if required settings are missing or invalid.

## Next Steps

After configuration:

1. Check logs for configuration errors on startup
2. Verify connections (GitLab API, AI API, SMTP)
3. Test with manual trigger via dashboard (`http://localhost:8000`)
4. Monitor first few issue analyses
