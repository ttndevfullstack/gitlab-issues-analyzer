# GitLab Issues Analyzer

An automated tool that analyzes GitLab issues using AI and sends structured email reports based on the WWWH-TR thinking framework.

## Overview

When a new GitLab issue is created, the system automatically:

1. Fetches comprehensive issue data (comments, related issues, attachments)
2. Analyzes the issue using AI via OpenRouter or OpenAI
3. Structures the analysis using the WWWH-TR framework
4. Sends an email notification with the analysis report

## WWWH-TR Framework

The analysis follows a structured thinking framework:

- **W1 — Why**: Root cause and ultimate goal
- **W2 — What**: Problem identification and information gathering
- **W3 — Who**: Stakeholders and people who can help
- **H — How**: Feasible solutions, comparison, and trade-offs
- **T — Test**: Quick experiments and measurement milestones
- **R — Reflect**: Evaluation, conclusion, and next steps

## Features

- **Automated Detection**: Webhook or polling mode for real-time or periodic issue monitoring
- **AI Analysis**: Supports OpenRouter (DeepSeek) and OpenAI with reasoning mode
- **Structured Reports**: WWWH-TR framework analysis in email format
- **Web Dashboard**: Manual triggers, statistics, and issue management
- **Lightweight**: No database required, minimal dependencies
- **Docker Ready**: Easy deployment with Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- GitLab Personal Access Token with `api` scope
- AI Provider API Key (OpenRouter or OpenAI)
- SMTP credentials for email delivery

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd gitlab-issues-analyzer
   ```

2. **Create `.env` file:**

   Copy `.env.example` to `.env` and configure:

   ```bash
   # GitLab Configuration
   GITLAB_URL=https://gitlab.com
   GITLAB_TOKEN=glpat-your-token-here
   GITLAB_ISSUE_SCOPE=all
   GITLAB_ISSUE_LABELS=label1,label2

   # AI Provider
   AI_PROVIDER=openrouter
   AI_API_KEY=sk-or-your-key-here
   AI_MODEL=tngtech/deepseek-r1t2-chimera:free
   AI_ENABLE_REASONING=true
   AI_MAX_TOKENS=16000

   # SMTP Configuration
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   SMTP_FROM_EMAIL=your-email@gmail.com
   SMTP_TO_EMAIL=recipient@example.com

   # Application Settings
   ENVIRONMENT=production
   ENABLE_AUTOMATION=true
   APP_MODE=poll
   POLL_INTERVAL=900
   LOG_LEVEL=INFO
   TIMEZONE=Asia/Ho_Chi_Minh
   APP_VERSION=1.0.0
   ```

3. **Start the application:**

   ```bash
   docker-compose up -d
   docker-compose logs -f
   ```

4. **Access the dashboard:**

   Open `http://localhost:8000` in your browser.

### Configuration Options

#### Environment Modes

- **`production`** (default): Full production settings, 15-minute poll interval
- **`development`**: Debug logging, shorter intervals, Flask auto-reload enabled
- **`testing`**: Processes 1 issue per poll, 1-minute interval, debug logging

#### Issue Start Time

Set `ISSUE_START_TIME` to process only issues created after a specific time:

- Format: `2026-01-05T00:00:00Z` (ISO 8601) or `2026-01-05 00:00:00` (space-separated)
- Default: Current time (only new issues after startup)
- Useful for local development to avoid reprocessing existing issues

#### Testing Mode

Set `MAX_ISSUES_PER_POLL=1` to process only one issue per polling cycle for testing.

## Documentation

- **[Configuration Guide](./docs/CONFIGURATION.md)** - Complete configuration reference
- **[Deployment Guide](./docs/DEPLOYMENT.md)** - Platform-specific deployment instructions
- **[API Integration](./docs/API_INTEGRATION.md)** - GitLab and AI API details
- **[Architecture](./docs/ARCHITECTURE.md)** - System design and components
- **[FAQ](./docs/FAQ.md)** - Troubleshooting and common questions

## Development

### Running Locally

For development with live code reloading:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Code changes are automatically picked up on the next poll cycle or Flask restart.

### Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ main.py tests/
isort src/ main.py tests/

# Lint
flake8 src/ main.py
```

### Rebuilding

```bash
docker-compose up -d --build
```

## License

MIT License

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass and code quality checks pass
5. Submit a pull request

---

For detailed documentation, see [docs/INDEX.md](./docs/INDEX.md)
