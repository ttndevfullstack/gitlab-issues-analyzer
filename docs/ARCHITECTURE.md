# Architecture Document

System design and architecture overview for GitLab Issues Analyzer.

## System Overview

A lightweight, event-driven system that monitors GitLab issues, analyzes them using AI, and sends email notifications. Designed to be simple, stateless, and deployable with minimal infrastructure.

## Architecture Principles

- **Stateless**: No database, minimal state management
- **Event-Driven**: Responds to GitLab webhooks or polling events
- **Modular**: Separate components for monitoring, analysis, and notification
- **Resilient**: Error handling and retry logic
- **Lightweight**: Minimal dependencies and resource usage

## System Components

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    GitLab Issues Analyzer                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌────────────┐ │
│  │   Monitor    │─────▶│   Analyzer   │─────▶│  Reporter  │ │
│  │  Component   │      │  Component   │      │ Component  │ │
│  └──────────────┘      └──────────────┘      └────────────┘ │
│         │                      │                     │        │
└─────────┼──────────────────────┼─────────────────────┼────────┘
          │                      │                     │
          ▼                      ▼                     ▼
    ┌─────────┐          ┌─────────────┐        ┌──────────┐
    │ GitLab  │          │  OpenRouter │        │   SMTP   │
    │   API   │          │     API     │        │  Server  │
    └─────────┘          └─────────────┘        └──────────┘
```

### Component Details

#### Monitor Component

**Responsibility**: Detect new GitLab issues

**Modes**:
- **Webhook Mode**: HTTP server that receives GitLab webhook events (real-time)
- **Polling Mode**: Periodically checks GitLab API for new issues

**Key Functions**:
- `start_webhook_server()`: Start HTTP server for webhook events
- `poll_gitlab_issues()`: Periodically fetch new issues
- `validate_webhook()`: Verify webhook authenticity
- `extract_issue_data()`: Parse issue information

**State Management**: File-based cache (`analysis_cache.json`) for processed issues

#### Analyzer Component

**Responsibility**: Analyze issues using AI API

**Key Functions**:
- `analyze_issue(issue_data)`: Main analysis function
- `fetch_comprehensive_issue_data(issue_iid)`: Fetch all issue data
- `prepare_prompt(issue_data)`: Format issue data into AI prompt
- `call_ai_api(prompt, provider, model)`: Make API request
- `parse_analysis(response)`: Extract structured analysis

**Supported AI Providers**:
- OpenRouter (supports multiple models including DeepSeek with reasoning mode)
- OpenAI (gpt-4, gpt-4-turbo, gpt-3.5-turbo)

**Analysis Framework**: WWWH-TR (Why, What, Who, How, Test, Reflect)

#### Reporter Component

**Responsibility**: Generate and send email reports

**Key Functions**:
- `generate_email_report(issue_data, analysis)`: Create email content
- `format_html_email(issue_data, analysis)`: Generate HTML email
- `format_text_email(issue_data, analysis)`: Generate plain text email
- `send_email(report)`: Send via SMTP

**Email Template**: Includes issue information, WWWH-TR analysis, and footer

## Data Flow

### Webhook Mode Flow

```
1. GitLab → Webhook Event → Monitor Component
2. Monitor → Validate & Extract Issue Data
3. Monitor → Fetch Comprehensive Issue Data
4. Monitor → Analyzer Component
5. Analyzer → AI API → Analysis Response
6. Analyzer → Reporter Component
7. Reporter → Generate Email → SMTP Server
8. Reporter → Email Delivered
```

### Polling Mode Flow

```
1. Monitor → Poll GitLab API (every N minutes)
2. GitLab API → List of Issues
3. Monitor → Filter New Issues (check cache)
4. Monitor → Fetch Comprehensive Issue Data
5. Monitor → Analyzer Component
6. Analyzer → AI API → Analysis Response
7. Analyzer → Reporter Component
8. Reporter → Generate Email → SMTP Server
9. Reporter → Email Delivered
```

## Technology Stack

### Core Technologies

- **Language**: Python 3.9+
- **HTTP Client**: `requests` library
- **SMTP**: `smtplib` (built-in)
- **Web Framework**: `Flask` (for webhook mode and dashboard)
- **Configuration**: Environment variables via `python-dotenv`

### External APIs

- **GitLab API**: REST API v4
- **OpenRouter API**: Unified API for multiple AI models
- **OpenAI API**: ChatGPT models
- **SMTP**: Standard SMTP protocol

### Dependencies

```
requests>=2.31.0
flask>=2.3.0
python-dotenv>=1.0.0
pytz>=2023.3
```

## Configuration Management

### Configuration Sources

1. Environment variables (from `.env` file or system environment)
2. Default values (for optional settings)

### Configuration Structure

All configuration via environment variables. See [Configuration Guide](./CONFIGURATION.md) for details.

## Error Handling Strategy

### Error Categories

1. **API Errors** (GitLab, AI Provider)
   - Retry with exponential backoff (3 attempts: 1s, 2s, 4s)
   - Log error details
   - Continue processing other issues

2. **Email Errors** (SMTP)
   - Retry with exponential backoff
   - Log error details
   - Store error in cache for manual review

3. **Configuration Errors**
   - Validate on startup
   - Fail fast with clear error messages

4. **Network Errors**
   - Retry logic with exponential backoff
   - Timeout handling (30 seconds default)

## Logging Strategy

### Log Levels

- **INFO**: Normal operations (issue detected, email sent)
- **WARNING**: Recoverable errors (retry attempts)
- **ERROR**: Critical errors (API failures, email failures)
- **DEBUG**: Detailed debugging information

### Log Format

```
[TIMESTAMP] [LEVEL] [COMPONENT] MESSAGE
```

### Log Output

- Console output (stdout)
- Timezone-aware timestamps (configurable via `TIMEZONE`)

## Security Considerations

### Credential Management

- Never commit credentials to version control
- Use environment variables for sensitive data
- `.gitignore` for config files with secrets

### Webhook Security

- Validate webhook secret tokens
- Verify request signatures (if available)
- Rate limiting on webhook endpoint

### API Security

- Store API keys securely (environment variables)
- Use HTTPS for all API calls
- Rotate credentials periodically

## State Management

### Stateless Design

- No database required
- Minimal state in memory
- Process issues independently

### Issue Tracking (Avoid Duplicates)

- **File-Based Cache**: `data/analysis_cache.json` for persistence
- Tracks processed issue IDs and analysis results
- Persists across restarts

## Performance Considerations

### Response Times

- Webhook processing: < 1 second
- Issue analysis: 30-120 seconds (AI API, depends on model)
- Email sending: 1-5 seconds
- **Total**: 2-5 minutes per issue

### Resource Usage

- Memory: < 100MB
- CPU: Low (mostly I/O bound)
- Network: Minimal (API calls only)

## Deployment Architecture

### Deployment Options

- **Docker/Docker Compose**: Recommended, easy setup
- **Cloud Platforms**: Any platform supporting Docker
- **Local**: Direct Python execution

### Deployment Diagram

```
┌─────────────────┐
│  Deployment     │
│  Platform       │
│  (Docker /      │
│   Cloud /       │
│   Local)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GitLab Issues   │
│     Analyzer     │
│   Application    │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│GitLab  │ │OpenRouter│
│  API   │ │   API    │
└────────┘ └──────────┘
```

## Monitoring and Observability

### Logging

- All operations logged
- Error tracking
- Performance metrics (optional)

### Health Checks

- Health endpoint (`/health`)
- Configuration validation
- API connectivity checks

## Future Enhancements

- Issue update notifications
- Multiple project support (already supported via global endpoint)
- Custom analysis templates
- Integration with other notification channels (Slack, Teams)
- Dashboard enhancements
