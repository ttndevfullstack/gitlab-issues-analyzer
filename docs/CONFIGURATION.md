# Configuration Guide

This guide explains all configuration options for the GitLab Issues Analyzer.

## Table of Contents

1. [Configuration Methods](#configuration-methods)
2. [GitLab Configuration](#gitlab-configuration)
3. [AI Provider Configuration](#ai-provider-configuration)
4. [SMTP Configuration](#smtp-configuration)
5. [Application Configuration](#application-configuration)
6. [Configuration Examples](#configuration-examples)
7. [Security Best Practices](#security-best-practices)

## Configuration Methods

The application uses **environment variables only** for configuration.

1. **Environment Variables** (from `.env` file or system environment)

   - Best for deployment platforms (Docker, cloud services)
   - Secure and flexible
   - Recommended for all environments (production, development, testing)
   - Use `.env` file for local development (automatically loaded by `python-dotenv`)

2. **Default Values**
   - Fallback for optional settings only
   - Required settings must be provided via environment variables

## GitLab Configuration

### Required Settings

#### `GITLAB_URL` / `gitlab.url`

- **Type**: String
- **Description**: GitLab instance URL
- **Examples**:
  - `https://gitlab.com` (GitLab.com)
  - `https://gitlab.example.com` (Self-hosted)
- **Default**: None (required)

#### `GITLAB_TOKEN` / `gitlab.token`

- **Type**: String
- **Description**: GitLab Personal Access Token
- **How to Get**:
  1. Go to GitLab → Settings → Access Tokens
  2. Create token with `api` scope
  3. Copy token (starts with `glpat-` or `gl-`)
- **Security**: Never commit to version control
- **Default**: None (required)

### Optional Settings

#### `GITLAB_ISSUE_SCOPE` / `gitlab.issue_filter.scope`

- **Type**: String (Optional)
- **Description**: Scope filter for global endpoint
- **Options**: `"all"`, `"assigned_to_me"`, `"created_by_me"`, etc.
- **Example**: `"all"` - Get all issues you have access to
- **Environment Variable**: `GITLAB_ISSUE_SCOPE=all`
- **Default**: `null` (optional)

#### `GITLAB_ISSUE_LABELS` / `gitlab.issue_filter.labels`

- **Type**: String (Comma-separated) or Array
- **Description**: Filter issues by label names when using global endpoint
- **Example**: `"UNIOSS 3"` or `"UNIOSS 3,bug"` for multiple labels
- **Environment Variable**: `GITLAB_ISSUE_LABELS=UNIOSS 3` or `GITLAB_ISSUE_LABELS=UNIOSS 3,bug`
- **Note**: Comma-separated values are automatically split into an array
- **Default**: `null` (optional)

## AI Provider Configuration

### Required Settings

#### `AI_PROVIDER` / `ai.provider`

- **Type**: String
- **Description**: AI provider to use for analysis
- **Options**:
  - `openrouter` (Default, recommended for DeepSeek v3.2 with reasoning mode)
  - `openai` (OpenAI ChatGPT)
- **Default**: `openrouter`
- **Note**: Only `openrouter` and `openai` are supported. Deprecated providers (deepseek, anthropic, custom) are automatically migrated to `openrouter`.

#### `AI_API_KEY` / `ai.api_key`

- **Type**: String
- **Description**: API key for selected AI provider
- **How to Get**:
  - **OpenRouter**: Sign up at [OpenRouter](https://openrouter.ai/) and get API key
  - **OpenAI**: Sign up at [OpenAI Platform](https://platform.openai.com/) and get API key
- **Security**: Never commit to version control
- **Default**: None (required)

### Optional Settings

#### `AI_MODEL` / `ai.model`

- **Type**: String
- **Description**: AI model to use (provider-specific)
- **Options by Provider**:
  - **OpenRouter**: `deepseek/deepseek-v3.2` (recommended, default), `openai/gpt-4`, `anthropic/claude-3-opus`, etc.
  - **OpenAI**: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`
- **Default**: `deepseek/deepseek-v3.2` (when using OpenRouter)
- **Note**: For OpenRouter, use format `provider/model-name` (e.g., `deepseek/deepseek-v3.2`)

#### `AI_MAX_TOKENS` / `ai.max_tokens`

- **Type**: Integer
- **Description**: Maximum tokens in response
- **Range**: 1 to 16000+ (varies by provider and model)
- **Recommended**:
  - `2000` (standard analysis)
  - `16000` (when `AI_ENABLE_REASONING=true` for complete HTML output)
- **Default**: `2000`
- **Note**: When reasoning mode is enabled, `max_tokens` is automatically increased to 16000 to prevent truncation

#### `AI_ENABLE_REASONING` / `ai.enable_reasoning`

- **Type**: Boolean
- **Description**: Enable reasoning/deepthink mode for OpenRouter with DeepSeek models
- **When to Use**: Enable for better analysis quality with DeepSeek v3.2+ via OpenRouter
- **Default**: `true` (when using OpenRouter)
- **Environment Variable**: `AI_ENABLE_REASONING=true` or `AI_ENABLE_REASONING=false`
- **Note**: Adds `"reasoning": {"enabled": true}` to API request payload. Only works with OpenRouter and compatible providers.

## SMTP Configuration

### Required Settings

#### `SMTP_HOST` / `smtp.host`

- **Type**: String
- **Description**: SMTP server hostname
- **Common Values**:
  - Gmail: `smtp.gmail.com`
  - Outlook: `smtp-mail.outlook.com`
  - Yahoo: `smtp.mail.yahoo.com`
  - Custom: Check your email provider
- **Default**: None (required)

#### `SMTP_PORT` / `smtp.port`

- **Type**: Integer
- **Description**: SMTP server port
- **Common Values**:
  - TLS: `587` (recommended)
  - SSL: `465`
  - Plain: `25` (not recommended)
- **Default**: `587`

#### `SMTP_USERNAME` / `smtp.username`

- **Type**: String
- **Description**: SMTP username (usually your email)
- **Example**: `your-email@gmail.com`
- **Default**: None (required)

#### `SMTP_PASSWORD` / `smtp.password`

- **Type**: String
- **Description**: SMTP password or app password
- **Note**: For Gmail, use App Password (not regular password)
- **Security**: Never commit to version control
- **Default**: None (required)

#### `SMTP_FROM_EMAIL` / `smtp.from_email`

- **Type**: String
- **Description**: Sender email address
- **Example**: `your-email@gmail.com`
- **Note**: Usually same as `SMTP_USERNAME`
- **Default**: None (required)

#### `SMTP_TO_EMAIL` / `smtp.to_email`

- **Type**: String or Array
- **Description**: Recipient email address(es)
- **Examples**:
  - Single: `recipient@example.com`
  - Multiple: `["email1@example.com", "email2@example.com"]`
- **Default**: None (required)

## Application Configuration

### Required Settings

None - all application settings are optional with sensible defaults.

### Optional Settings

#### `APP_MODE` / `app.mode`

- **Type**: String
- **Description**: Application mode
- **Options**:
  - `webhook`: Receive GitLab webhook events (real-time)
  - `poll`: Periodically check for new issues (default)
- **Environment Variable**: `APP_MODE=poll` or `APP_MODE=webhook`
- **Default**: `poll`

#### `ENVIRONMENT` / `app.environment`

- **Type**: String
- **Description**: Application environment mode
- **Options**:
  - `production` (default): Full production settings
  - `development`: Debug logging, shorter poll intervals
  - `testing`: Processes only 1 issue, debug logging, 1-minute poll interval
- **Environment Variable**: `ENVIRONMENT=production`
- **Default**: `production`

#### `ENABLE_AUTOMATION` / `app.enable_automation`

- **Type**: Boolean
- **Description**: Enable/disable automated polling and webhook processing
- **Options**: `true` or `false`
- **Environment Variable**: `ENABLE_AUTOMATION=true`
- **Default**: `true`
- **Note**:
  - When `false`, automatic polling/webhook processing is disabled
  - Dashboard and manual triggers remain available

#### `MAX_ISSUES_PER_POLL` / `app.max_issues_per_poll`

- **Type**: Integer (Optional)
- **Description**: Limit number of issues to process per polling cycle
- **Use Case**: Testing mode - process only 1 issue at a time
- **Example**: `1` - Process only 1 issue per poll
- **Environment Variable**: `MAX_ISSUES_PER_POLL=1`
- **Default**: `null` (unlimited, processes all new issues)
- **Note**: In `testing` environment, automatically set to `1` if not specified

#### `POLL_INTERVAL` / `app.poll_interval`

- **Type**: Integer
- **Description**: Polling interval in seconds (polling mode only)
- **Examples**:
  - `300` (5 minutes)
  - `900` (15 minutes, default)
  - `3600` (1 hour)
- **Environment Variable**: `POLL_INTERVAL=900`
- **Note**: Lower intervals may hit rate limits
- **Default**: `900` (15 minutes)

#### `LOG_LEVEL` / `app.log_level`

- **Type**: String
- **Description**: Logging level
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Environment Variable**: `LOG_LEVEL=INFO`
- **Default**: `INFO`

## Environment-Specific Behavior

### Production Mode (`ENVIRONMENT=production`)

- Default settings
- Poll interval: 900 seconds (15 minutes)
- Log level: INFO
- Processes all new issues

### Development Mode (`ENVIRONMENT=development`)

- Debug logging enabled
- Shorter poll intervals
- More verbose output

### Testing Mode (`ENVIRONMENT=testing`)

- Automatically limits to 1 issue per poll
- Debug logging enabled
- Poll interval reduced to 60 seconds (1 minute)
- Useful for testing without processing all issues

## Next Steps

After configuration:

1. Check logs for configuration errors on startup
2. Verify all connections work
3. Test with manual trigger via dashboard
4. Monitor first few issue analyses
