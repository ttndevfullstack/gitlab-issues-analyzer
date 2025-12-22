# Configuration Guide

This guide explains all configuration options for the GitLab Issues Analyzer.

## Table of Contents

1. [Configuration Methods](#configuration-methods)
2. [GitLab Configuration](#gitlab-configuration)
3. [DeepSeek Configuration](#deepseek-configuration)
4. [SMTP Configuration](#smtp-configuration)
5. [Application Configuration](#application-configuration)
6. [Configuration Examples](#configuration-examples)
7. [Security Best Practices](#security-best-practices)

## Configuration Methods

The application supports three configuration methods (in priority order):

1. **Environment Variables** (Highest Priority)
   - Best for deployment platforms
   - Secure and flexible
   - Recommended for production

2. **Config File** (`config.json`)
   - Convenient for local development
   - Easy to manage
   - Must be in `.gitignore`

3. **Default Values**
   - Fallback for optional settings
   - Not recommended for production

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

#### `GITLAB_PROJECT_ID` / `gitlab.project_id`
- **Type**: String or Integer
- **Description**: GitLab project ID or path
- **Examples**:
  - `123456` (Project ID)
  - `username/project-name` (Project path)
- **How to Find**: Project → Settings → General → Project ID
- **Default**: None (required)

### Optional Settings

#### `GITLAB_WEBHOOK_SECRET` / `gitlab.webhook_secret`
- **Type**: String
- **Description**: Secret token for webhook validation
- **Usage**: Must match GitLab webhook secret token
- **Security**: Use strong random string
- **Default**: None (required if using webhook mode)

#### `GITLAB_ISSUE_FILTER` / `gitlab.issue_filter`
- **Type**: Object
- **Description**: Filter issues by criteria
- **Example**:
  ```json
  {
    "labels": ["bug", "enhancement"],
    "assignee_id": null,
    "state": "opened"
  }
  ```
- **Default**: Process all new issues

## AI Provider Configuration

### Required Settings

#### `AI_PROVIDER` / `ai.provider`
- **Type**: String
- **Description**: AI provider to use for analysis
- **Options**:
  - `deepseek` (Default, cost-effective)
  - `openai` (OpenAI ChatGPT)
  - `anthropic` (Anthropic Claude)
  - `custom` (Custom OpenAI-compatible API)
- **Default**: `deepseek`

#### `AI_API_KEY` / `ai.api_key`
- **Type**: String
- **Description**: API key for selected AI provider
- **How to Get**:
  - **DeepSeek**: Sign up at [DeepSeek Platform](https://platform.deepseek.com/)
  - **OpenAI**: Sign up at [OpenAI Platform](https://platform.openai.com/)
  - **Anthropic**: Sign up at [Anthropic Console](https://console.anthropic.com/)
- **Security**: Never commit to version control
- **Default**: None (required)

### Optional Settings

#### `AI_MODEL` / `ai.model`
- **Type**: String
- **Description**: AI model to use (provider-specific)
- **Options by Provider**:
  - **DeepSeek**: `deepseek-chat` (default), `deepseek-reasoner`
  - **OpenAI**: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo` (default)
  - **Anthropic**: `claude-3-opus-20240229`, `claude-3-sonnet-20240229` (default), `claude-3-haiku-20240307`
- **Default**: Provider-specific (see above)

#### `AI_BASE_URL` / `ai.base_url`
- **Type**: String
- **Description**: Custom API base URL (for custom providers or self-hosted)
- **Defaults by Provider**:
  - DeepSeek: `https://api.deepseek.com/v1`
  - OpenAI: `https://api.openai.com/v1`
  - Anthropic: `https://api.anthropic.com/v1`
- **Use Case**: Custom providers, local AI servers (Ollama, LocalAI)
- **Default**: Provider-specific (see above)

#### `AI_TEMPERATURE` / `ai.temperature`
- **Type**: Float
- **Description**: Sampling temperature (0.0 to 2.0)
- **Range**: 0.0 (deterministic) to 2.0 (creative)
- **Recommended**: 0.7 (balanced)
- **Default**: `0.7`

#### `AI_MAX_TOKENS` / `ai.max_tokens`
- **Type**: Integer
- **Description**: Maximum tokens in response
- **Range**: 1 to 4096 (varies by provider)
- **Recommended**: 2000 (for detailed analysis)
- **Default**: `2000`

#### `AI_FALLBACK_PROVIDER` / `ai.fallback_provider`
- **Type**: String
- **Description**: Fallback provider if primary provider fails
- **Options**: Same as `AI_PROVIDER`
- **Default**: None (no fallback)

#### `AI_FALLBACK_API_KEY` / `ai.fallback_api_key`
- **Type**: String
- **Description**: API key for fallback provider
- **Default**: None

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

### Optional Settings

#### `SMTP_USE_TLS` / `smtp.use_tls`
- **Type**: Boolean
- **Description**: Use TLS encryption
- **Default**: `true`

#### `SMTP_USE_SSL` / `smtp.use_ssl`
- **Type**: Boolean
- **Description**: Use SSL encryption
- **Note**: Usually for port 465
- **Default**: `false`

#### `SMTP_SUBJECT_PREFIX` / `smtp.subject_prefix`
- **Type**: String
- **Description**: Prefix for email subject
- **Example**: `[GitLab Analysis]`
- **Default**: `[GitLab Issue Analysis]`

## Application Configuration

### Required Settings

#### `APP_MODE` / `app.mode`
- **Type**: String
- **Description**: Application mode
- **Options**:
  - `webhook`: Receive GitLab webhook events (real-time)
  - `poll`: Periodically check for new issues
- **Default**: `poll`

### Optional Settings

#### `POLL_INTERVAL` / `app.poll_interval`
- **Type**: Integer
- **Description**: Polling interval in seconds (polling mode only)
- **Examples**:
  - `300` (5 minutes)
  - `900` (15 minutes)
  - `3600` (1 hour)
- **Note**: Lower intervals may hit rate limits
- **Default**: `900` (15 minutes)

#### `WEBHOOK_PORT` / `app.webhook_port`
- **Type**: Integer
- **Description**: HTTP server port (webhook mode only)
- **Range**: 1-65535
- **Default**: `8000`

#### `WEBHOOK_HOST` / `app.webhook_host`
- **Type**: String
- **Description**: HTTP server host (webhook mode only)
- **Options**:
  - `0.0.0.0` (all interfaces, recommended for deployment)
  - `127.0.0.1` (localhost only)
- **Default**: `0.0.0.0`

#### `LOG_LEVEL` / `app.log_level`
- **Type**: String
- **Description**: Logging level
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Default**: `INFO`

#### `PROCESSED_ISSUES_FILE` / `app.processed_issues_file`
- **Type**: String
- **Description**: File path to store processed issue IDs
- **Purpose**: Avoid duplicate processing across restarts
- **Example**: `processed_issues.json`
- **Default**: None (in-memory only)

#### `MAX_RETRIES` / `app.max_retries`
- **Type**: Integer
- **Description**: Maximum retry attempts for API calls
- **Default**: `3`

#### `RETRY_BACKOFF` / `app.retry_backoff`
- **Type**: Float
- **Description**: Exponential backoff multiplier
- **Default**: `2.0`

## Configuration Examples

### Example 1: Environment Variables (Production)

```bash
# GitLab
export GITLAB_URL="https://gitlab.com"
export GITLAB_TOKEN="glpat-xxxxxxxxxxxx"
export GITLAB_PROJECT_ID="123456"
export GITLAB_WEBHOOK_SECRET="my-secret-token"

# AI Provider
export AI_PROVIDER="deepseek"
export AI_API_KEY="sk-xxxxxxxxxxxx"
export AI_MODEL="deepseek-chat"
export AI_TEMPERATURE="0.7"

# SMTP
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_FROM_EMAIL="your-email@gmail.com"
export SMTP_TO_EMAIL="recipient@example.com"

# App
export APP_MODE="webhook"
export WEBHOOK_PORT="8000"
export LOG_LEVEL="INFO"
```

### Example 2: Config File (Local Development)

```json
{
  "gitlab": {
    "url": "https://gitlab.com",
    "token": "glpat-xxxxxxxxxxxx",
    "project_id": "123456",
    "webhook_secret": "my-secret-token"
  },
  "ai": {
    "provider": "deepseek",
    "api_key": "sk-xxxxxxxxxxxx",
    "model": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "smtp": {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_email": "your-email@gmail.com",
    "to_email": "recipient@example.com",
    "use_tls": true
  },
  "app": {
    "mode": "poll",
    "poll_interval": 900,
    "log_level": "INFO",
    "max_retries": 3
  }
}
```

### Example 3: Gmail SMTP Setup

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to Google Account → Security
   - 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Copy the 16-character password
3. **Use in Configuration**:
   ```json
   {
     "smtp": {
       "host": "smtp.gmail.com",
       "port": 587,
       "username": "your-email@gmail.com",
       "password": "xxxx xxxx xxxx xxxx",  // App password
       "from_email": "your-email@gmail.com",
       "to_email": "recipient@example.com"
     }
   }
   ```

### Example 4: Multiple Recipients

```json
{
  "smtp": {
    "to_email": [
      "recipient1@example.com",
      "recipient2@example.com",
      "recipient3@example.com"
    ]
  }
}
```

### Example 5: Using OpenAI ChatGPT

```json
{
  "ai": {
    "provider": "openai",
    "api_key": "sk-xxxxxxxxxxxx",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

### Example 6: Using Anthropic Claude

```json
{
  "ai": {
    "provider": "anthropic",
    "api_key": "sk-ant-xxxxxxxxxxxx",
    "model": "claude-3-sonnet-20240229",
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

### Example 7: Using Custom/OpenAI-Compatible API (e.g., Ollama)

```json
{
  "ai": {
    "provider": "custom",
    "api_key": "not-required",
    "model": "llama2",
    "base_url": "http://localhost:11434/v1",
    "temperature": 0.7
  }
}
```

### Example 8: Self-Hosted GitLab

```json
{
  "gitlab": {
    "url": "https://gitlab.company.com",
    "token": "glpat-xxxxxxxxxxxx",
    "project_id": "company/project-name"
  }
}
```

## Security Best Practices

### 1. Never Commit Secrets

**`.gitignore` should include**:
```
config.json
*.env
.env*
secrets/
```

### 2. Use Environment Variables in Production

- Platform-specific secrets management
- No config files with secrets
- Rotate credentials regularly

### 3. Use Strong Webhook Secrets

```bash
# Generate strong secret
openssl rand -hex 32
```

### 4. Limit API Token Scopes

- GitLab token: Only `api` scope (minimum required)
- DeepSeek: Use API key with appropriate limits
- SMTP: Use app passwords (not main password)

### 5. Validate Webhook Requests

- Always validate webhook secret
- Verify request signatures if available
- Rate limit webhook endpoint

### 6. Secure File Permissions

```bash
# Config file permissions (local only)
chmod 600 config.json
```

### 7. Monitor API Usage

- Track API calls
- Set up alerts for unusual activity
- Monitor rate limits

## Configuration Validation

The application validates configuration on startup:

1. **Required fields**: All required settings must be present
2. **Format validation**: URLs, emails, ports are validated
3. **Connection tests**: Optional connection tests for APIs
4. **Error messages**: Clear error messages for missing/invalid config

## Troubleshooting Configuration

### Issue: "Missing required configuration"

**Solution**: Check all required environment variables or config file fields are set.

### Issue: "Invalid SMTP credentials"

**Solution**: 
- Verify username/password
- For Gmail, use App Password
- Check SMTP server and port

### Issue: "GitLab API authentication failed"

**Solution**:
- Verify token is valid
- Check token has `api` scope
- Verify GitLab URL is correct

### Issue: "AI API error"

**Solution**:
- Verify API key is valid for selected provider
- Check API key has credits/balance
- Verify model name is correct for provider
- Check provider-specific requirements (e.g., Anthropic requires version header)

## Next Steps

After configuration:

1. Test configuration with: `python main.py --test-config`
2. Run in test mode: `python main.py --mode poll --dry-run`
3. Check logs for configuration errors
4. Verify all connections work


