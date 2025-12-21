# Requirements Document

## 1. Project Overview

### 1.1 Purpose
Automate the analysis of GitLab issues to reduce manual review time. The system should analyze new issues using AI and send structured email reports.

### 1.2 Goals
- Save time on manual issue review
- Provide structured analysis using WWWH-TR framework
- Automate the entire workflow from issue creation to email notification
- Keep the solution lightweight, fast, and simple

### 1.3 Success Criteria
- Automatically detects new GitLab issues
- Generates meaningful analysis using WWWH-TR framework
- Sends email notifications within reasonable time (< 5 minutes)
- Operates with zero cost (free tiers only)
- Easy to deploy and maintain

## 2. Functional Requirements

### 2.1 Issue Detection (FR1)
**Priority: High**

- **FR1.1**: System must detect new GitLab issues
  - **Option A**: Webhook-based (real-time)
  - **Option B**: Polling-based (periodic checks)
  - **Preference**: Webhook for real-time, Polling as fallback

- **FR1.2**: System must handle issue updates (optional, future enhancement)
- **FR1.3**: System must filter issues (e.g., by labels, assignee, project)

### 2.2 Issue Analysis (FR2)
**Priority: High**

- **FR2.1**: System must fetch complete issue data from GitLab API
  - Issue title
  - Issue description
  - Labels
  - Assignee
  - Comments (optional)
  - Milestone (optional)
  - Priority (optional)

- **FR2.2**: System must send issue data to DeepSeek API for analysis
- **FR2.3**: System must structure analysis using WWWH-TR framework:
  - **W1 — Why**: Root cause and ultimate goal
  - **W2 — What**: Problem identification and information gathering
  - **W3 — Who**: Stakeholders and affected parties
  - **H — How**: Feasible solutions, comparisons, trade-offs
  - **T — Test**: Quick experiments and measurement milestones
  - **R — Reflect**: Best choice, evaluation, next steps

- **FR2.4**: System must handle API errors gracefully
- **FR2.5**: System must respect API rate limits

### 2.3 Report Generation (FR3)
**Priority: High**

- **FR3.1**: System must format analysis into readable email report
- **FR3.2**: Email must include:
  - Issue title and link
  - Issue metadata (labels, assignee, etc.)
  - WWWH-TR structured analysis
  - Timestamp
  - Issue URL for quick access

- **FR3.3**: Email format should be HTML (with plain text fallback)
- **FR3.4**: Email should be well-formatted and easy to read

### 2.4 Email Notification (FR4)
**Priority: High**

- **FR4.1**: System must send email via SMTP
- **FR4.2**: System must support multiple recipients (optional)
- **FR4.3**: System must handle email sending errors
- **FR4.4**: System must include retry logic for failed emails

## 3. Non-Functional Requirements

### 3.1 Performance (NFR1)
- **NFR1.1**: Issue analysis should complete within 2-5 minutes
- **NFR1.2**: System should handle at least 10 issues per hour
- **NFR1.3**: Minimal resource usage (CPU, memory)

### 3.2 Reliability (NFR2)
- **NFR2.1**: System should handle API failures gracefully
- **NFR2.2**: System should log errors for debugging
- **NFR2.3**: System should not crash on invalid data

### 3.3 Security (NFR3)
- **NFR3.1**: All credentials must be stored securely (environment variables, config files with .gitignore)
- **NFR3.2**: Webhook secret token validation (if using webhooks)
- **NFR3.3**: No hardcoded secrets in code

### 3.4 Maintainability (NFR4)
- **NFR4.1**: Code should be well-documented
- **NFR4.2**: Configuration should be externalized
- **NFR4.3**: Easy to update and modify

### 3.5 Cost (NFR5)
- **NFR5.1**: Zero cost requirement - use only free tiers
- **NFR5.2**: No paid services or databases

### 3.6 Deployment (NFR6)
- **NFR6.1**: Easy to deploy on free platforms
- **NFR6.2**: No complex infrastructure requirements
- **NFR6.3**: Minimal setup steps

## 4. Technical Constraints

### 4.1 No Database
- System must not use any database
- All state must be in-memory or file-based (if needed)
- Issue tracking can use GitLab API directly

### 4.2 Lightweight
- Minimal dependencies
- Fast startup time
- Low memory footprint

### 4.3 Free Deployment Options
- GitHub Actions (free tier)
- Railway (free tier)
- Render (free tier)
- Fly.io (free tier)
- Local cron job
- PythonAnywhere (free tier)

## 5. Integration Requirements

### 5.1 GitLab Integration
- **IR1**: GitLab API v4 or v4 compatibility
- **IR2**: Personal Access Token authentication
- **IR3**: Support for gitlab.com and self-hosted instances
- **IR4**: Webhook support (if available)

### 5.2 DeepSeek API Integration
- **IR5**: DeepSeek Chat API compatibility
- **IR6**: Support for thinking mode
- **IR7**: Proper error handling and retries

### 5.3 SMTP Integration
- **IR8**: Standard SMTP protocol support
- **IR9**: TLS/SSL support
- **IR10**: Support for common providers (Gmail, Outlook, etc.)

## 6. User Stories

### US1: As a developer, I want to receive email notifications when new issues are created, so I can stay informed without checking GitLab manually.

### US2: As a developer, I want the analysis to follow the WWWH-TR framework, so I can quickly understand the issue's context and requirements.

### US3: As a developer, I want the system to work automatically, so I don't need to manually trigger analysis.

### US4: As a developer, I want the system to be free to run, so I don't incur additional costs.

### US5: As a developer, I want easy deployment, so I can set it up quickly without complex infrastructure.

## 7. Out of Scope (Future Enhancements)

- Issue update notifications
- Comment analysis
- Multiple project support (can be added later)
- Dashboard or web interface
- Issue prioritization scoring
- Integration with other tools (Slack, Teams, etc.)
- Historical analysis or trends
- Custom analysis templates

## 8. Assumptions

1. User has access to GitLab project with API permissions
2. User has DeepSeek API key
3. User has SMTP credentials
4. User prefers email notifications over other channels
5. Issues are primarily in English (or language supported by DeepSeek)
6. Free tier limits are acceptable for usage volume

## 9. Dependencies

### External Services
- GitLab (API)
- DeepSeek (API)
- SMTP Server (Email provider)

### Technology Stack
- Python 3.9+
- HTTP client library (requests)
- SMTP library (smtplib)
- Web framework (if webhook mode: Flask/FastAPI)

## 10. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API rate limits | High | Medium | Implement rate limiting and retry logic |
| API downtime | High | Low | Implement retry with exponential backoff |
| Email delivery failure | Medium | Low | Implement retry logic, log failures |
| DeepSeek API costs | High | Low | Use free tier, monitor usage |
| Webhook security | Medium | Medium | Validate webhook secret tokens |
| Deployment platform limits | Medium | Medium | Support multiple deployment options |


