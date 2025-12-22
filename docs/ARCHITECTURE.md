# Architecture Document

## 1. System Overview

The GitLab Issues Analyzer is a lightweight, event-driven system that monitors GitLab issues, analyzes them using AI, and sends email notifications. The architecture is designed to be simple, stateless, and deployable on free platforms.

## 2. Architecture Principles

- **Stateless**: No database, minimal state management
- **Event-Driven**: Responds to GitLab webhooks or polling events
- **Modular**: Separate components for monitoring, analysis, and notification
- **Resilient**: Error handling and retry logic
- **Lightweight**: Minimal dependencies and resource usage

## 3. System Components

### 3.1 Component Diagram

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
│         │                      │                     │        │
└─────────┼──────────────────────┼─────────────────────┼────────┘
          │                      │                     │
          ▼                      ▼                     ▼
    ┌─────────┐          ┌─────────────┐        ┌──────────┐
    │ GitLab  │          │  DeepSeek   │        │   SMTP   │
    │   API   │          │     API     │        │  Server  │
    └─────────┘          └─────────────┘        └──────────┘
```

### 3.2 Component Details

#### 3.2.1 Monitor Component
**Responsibility**: Detect new GitLab issues

**Modes**:
- **Webhook Mode**: HTTP server that receives GitLab webhook events
- **Polling Mode**: Periodically checks GitLab API for new issues

**Key Functions**:
- `start_webhook_server()`: Start HTTP server for webhook events
- `poll_gitlab_issues()`: Periodically fetch new issues
- `validate_webhook()`: Verify webhook authenticity
- `extract_issue_data()`: Parse issue information from webhook/polling response

**State Management**:
- In-memory set of processed issue IDs (to avoid duplicates)
- Optional: File-based tracking for persistence across restarts

#### 3.2.2 Analyzer Component
**Responsibility**: Analyze issues using AI API (DeepSeek, ChatGPT, etc.)

**Key Functions**:
- `analyze_issue(issue_data)`: Main analysis function
- `fetch_comprehensive_issue_data(issue_iid)`: Fetch all issue data (comments, related issues, attachments)
- `prepare_prompt(issue_data)`: Format comprehensive issue data into AI prompt
- `call_ai_api(prompt, provider, model)`: Make API request to selected AI provider
- `parse_analysis(response)`: Extract structured analysis from API response
- `format_wwwh_tr(analysis)`: Structure analysis into WWWH-TR format

**Supported AI Providers**:
- DeepSeek (deepseek-chat, deepseek-reasoner)
- OpenAI ChatGPT (gpt-4, gpt-3.5-turbo)
- Anthropic Claude (claude-3-opus, claude-3-sonnet)
- Other OpenAI-compatible APIs

**Prompt Template**:
```
Analyze the following GitLab issue using the WWWH-TR framework:

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

=== COMMENTS ===
{comments}

=== RELATED ISSUES ===
{related_issues}

=== ATTACHMENTS & IMAGES ===
{attachments}

=== ADDITIONAL CONTEXT ===
{additional_context}

Please provide analysis structured as:
- W1 — Why: [root cause and ultimate goal]
- W2 — What: [problem identification]
- W3 — Who: [stakeholders]
- H — How: [feasible solutions and trade-offs]
- T — Test: [quick experiments and milestones]
- R — Reflect: [best choice and next steps]

Note: Consider all available information including comments, related issues, and attachments when analyzing.
```

**Error Handling**:
- Retry logic with exponential backoff
- Rate limit handling
- Fallback to basic summary if API fails

#### 3.2.3 Reporter Component
**Responsibility**: Generate and send email reports

**Key Functions**:
- `generate_email_report(issue_data, analysis)`: Create email content
- `format_html_email(issue_data, analysis)`: Generate HTML email
- `format_text_email(issue_data, analysis)`: Generate plain text email
- `send_email(report)`: Send via SMTP
- `retry_send_email(report, max_retries)`: Retry logic for email sending

**Email Template Structure**:
```
Subject: [GitLab Issue Analysis] {issue_title}

Body:
- Issue Information (title, link, metadata)
- WWWH-TR Analysis (structured sections)
- Footer (timestamp, issue URL)
```

## 4. Data Flow

### 4.1 Webhook Mode Flow

```
1. GitLab → Webhook Event → Monitor Component
2. Monitor → Validate & Extract Issue Data
3. Monitor → Fetch Comprehensive Issue Data (comments, related issues, attachments)
4. Monitor → Analyzer Component (with comprehensive issue data)
5. Analyzer → AI API (DeepSeek/ChatGPT/Claude) → Analysis Response
6. Analyzer → Reporter Component (with issue data + analysis)
7. Reporter → Generate Email → SMTP Server
8. Reporter → Email Delivered
```

### 4.2 Polling Mode Flow

```
1. Monitor → Poll GitLab API (every N minutes)
2. GitLab API → List of Issues
3. Monitor → Filter New Issues (compare with processed set)
4. Monitor → Fetch Comprehensive Issue Data (comments, related issues, attachments)
5. Monitor → Analyzer Component (for each new issue with comprehensive data)
6. Analyzer → AI API (DeepSeek/ChatGPT/Claude) → Analysis Response
7. Analyzer → Reporter Component (with issue data + analysis)
8. Reporter → Generate Email → SMTP Server
9. Reporter → Email Delivered
```

## 5. Technology Stack

### 5.1 Core Technologies
- **Language**: Python 3.9+
- **HTTP Client**: `requests` library
- **SMTP**: `smtplib` (built-in) or `email` library
- **Web Framework** (Webhook mode): `Flask` or `FastAPI` (lightweight)
- **Configuration**: JSON files or environment variables

### 5.2 External APIs
- **GitLab API**: REST API v4
- **DeepSeek API**: Chat API with thinking mode
- **SMTP**: Standard SMTP protocol

### 5.3 Dependencies
```
requests>=2.31.0
flask>=2.3.0  # Only if webhook mode
python-dotenv>=1.0.0  # For environment variables
```

## 6. Configuration Management

### 6.1 Configuration Sources (Priority Order)
1. Environment variables (highest priority)
2. `config.json` file
3. Default values

### 6.2 Configuration Structure
```json
{
  "gitlab": {
    "url": "string",
    "token": "string",
    "project_id": "string|int",
    "webhook_secret": "string"
  },
  "deepseek": {
    "api_key": "string",
    "model": "string",
    "temperature": "float",
    "max_tokens": "int"
  },
  "smtp": {
    "host": "string",
    "port": "int",
    "username": "string",
    "password": "string",
    "from_email": "string",
    "to_email": "string|array"
  },
  "app": {
    "mode": "webhook|poll",
    "poll_interval": "int",
    "webhook_port": "int",
    "log_level": "string"
  }
}
```

## 7. Error Handling Strategy

### 7.1 Error Categories

1. **API Errors** (GitLab, DeepSeek)
   - Retry with exponential backoff
   - Log error details
   - Continue processing other issues

2. **Email Errors** (SMTP)
   - Retry with exponential backoff
   - Log error details
   - Store failed emails for manual review (optional)

3. **Configuration Errors**
   - Validate on startup
   - Fail fast with clear error messages

4. **Network Errors**
   - Retry logic
   - Timeout handling

### 7.2 Retry Strategy
- **Max Retries**: 3 attempts
- **Backoff**: Exponential (1s, 2s, 4s)
- **Timeout**: 30 seconds per request

## 8. Logging Strategy

### 8.1 Log Levels
- **INFO**: Normal operations (issue detected, email sent)
- **WARNING**: Recoverable errors (retry attempts)
- **ERROR**: Critical errors (API failures, email failures)
- **DEBUG**: Detailed debugging information

### 8.2 Log Format
```
[TIMESTAMP] [LEVEL] [COMPONENT] MESSAGE
```

### 8.3 Log Output
- Console output (stdout)
- Optional: File logging for production

## 9. Security Considerations

### 9.1 Credential Management
- Never commit credentials to version control
- Use environment variables or secure config files
- `.gitignore` for config files with secrets

### 9.2 Webhook Security
- Validate webhook secret tokens
- Verify request signatures (if available)
- Rate limiting on webhook endpoint

### 9.3 API Security
- Store API keys securely
- Use HTTPS for all API calls
- Rotate credentials periodically

## 10. Scalability Considerations

### 10.1 Current Design (Single Instance)
- Handles moderate volume (10-50 issues/hour)
- In-memory state (lost on restart)
- Suitable for personal use

### 10.2 Future Enhancements (If Needed)
- File-based state persistence
- Batch processing for multiple issues
- Queue system for high volume
- Multiple project support

## 11. Deployment Architecture

### 11.1 Deployment Options

#### Option A: GitHub Actions (Recommended for Free)
- Scheduled workflow (polling mode)
- No webhook support (GitLab webhooks can't reach GitHub Actions)
- Free tier: 2000 minutes/month

#### Option B: Railway/Render/Fly.io
- Webhook mode supported
- Free tier available
- Continuous running service

#### Option C: Local Cron Job
- Polling mode
- Runs on local machine
- No external dependencies

### 11.2 Deployment Diagram

```
┌─────────────────┐
│  Deployment     │
│  Platform       │
│  (GitHub Actions│
│   / Railway /   │
│   Render / etc) │
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
│GitLab  │ │ DeepSeek │
│  API   │ │   API    │
└────────┘ └──────────┘
```

## 12. State Management

### 12.1 Stateless Design
- No database required
- Minimal state in memory
- Process issues independently

### 12.2 Issue Tracking (Avoid Duplicates)
- **In-Memory Set**: Track processed issue IDs
- **Optional File-Based**: `processed_issues.json` for persistence
- **Reset Strategy**: Clear on restart or maintain across restarts

## 13. Performance Considerations

### 13.1 Response Times
- Webhook processing: < 1 second
- Issue analysis: 30-120 seconds (DeepSeek API)
- Email sending: 1-5 seconds
- **Total**: 2-5 minutes per issue

### 13.2 Resource Usage
- Memory: < 100MB
- CPU: Low (mostly I/O bound)
- Network: Minimal (API calls only)

## 14. Monitoring and Observability

### 14.1 Logging
- All operations logged
- Error tracking
- Performance metrics (optional)

### 14.2 Health Checks
- Webhook endpoint health check
- Configuration validation
- API connectivity checks

## 15. Future Enhancements

- Issue update notifications
- Multiple project support
- Custom analysis templates
- Dashboard/UI
- Integration with other notification channels (Slack, Teams)


