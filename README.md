# GitLab Issues Analyzer

A lightweight, automated tool that analyzes new GitLab issues using AI and sends structured email reports based on the WWWH-TR thinking framework.

## 🎯 What It Does

When a new GitLab issue is created, the system:

1. Fetches comprehensive issue data (comments, related issues, attachments)
2. Analyzes the issue using AI via OpenRouter (DeepSeek v3.2 with reasoning mode)
3. Structures the analysis using the WWWH-TR framework
4. Sends an email notification with the analysis report

## 🧭 WWWH-TR Framework

- **W1 — Why**: Root cause and ultimate goal
- **W2 — What**: Problem identification and information gathering
- **W3 — Who**: Stakeholders and people who can help
- **H — How**: Feasible solutions, comparison, and trade-offs
- **T — Test**: Quick experiments and measurement milestones
- **R — Reflect**: Evaluation, conclusion, and next steps

## ✨ Features

- Automated issue detection (webhooks or polling)
- AI analysis via OpenRouter (DeepSeek v3.2 with reasoning mode) or OpenAI
- Structured WWWH-TR analysis reports
- Email notifications via SMTP
- **Web Dashboard** for manual triggers and statistics
- Lightweight (no database, minimal dependencies)
- Docker support for easy deployment

## 🚀 Quick Start

### Docker

1. **Clone and configure:**

   ```bash
   git clone <repository-url>
   cd gitlab-issues-analyzer
   ```

2. **Copy `.env` from `.env.example` file:**

   ```bash
   # GitLab
   GITLAB_URL=https://gitlab.unioss.jp
   GITLAB_TOKEN=<your-token-here>
   GITLAB_ISSUE_SCOPE=all
   GITLAB_ISSUE_LABELS=UNIOSS 3

   # AI Provider
   AI_PROVIDER=openrouter
   AI_API_KEY=<your-token-here>
   AI_MODEL=tngtech/deepseek-r1t2-chimera:free
   AI_ENABLE_REASONING=true
   AI_MAX_TOKENS=16000

   # SMTP
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=example@gmail.com
   SMTP_PASSWORD=password
   SMTP_FROM_EMAIL=example@gmail.com
   SMTP_TO_EMAIL=example@tpssoft.com

   # Application
   ENVIRONMENT=production
   ENABLE_AUTOMATION=true
   APP_MODE=poll
   POLL_INTERVAL=900
   LOG_LEVEL=INFO
   # MAX_ISSUES_PER_POLL=1
   # ISSUE_START_TIME=2026-01-01T00:00:00Z  # ISO 8601 timestamp - only process issues created after this time
   ```

   **Environment Modes:**

   - `production` (default): Full production settings
   - `development`: Debug logging, shorter poll intervals
   - `testing`: Processes only 1 issue, debug logging, 1-minute poll interval

   **Setting Environment:**

   - Use `ENVIRONMENT` variable
   - Example: `ENVIRONMENT=testing` or `ENVIRONMENT=development`

   **Testing Mode:**

   - Set `MAX_ISSUES_PER_POLL=1` to process only 1 issue per polling cycle
   - Useful for testing without processing all issues at once
   - Remove or set to empty to process all issues

   **Issue Start Time (for local development):**

   - Set `ISSUE_START_TIME` to a timestamp (ISO 8601 format recommended)
   - Supported formats:
     - `2026-01-05T00:00:00Z` (ISO 8601 with UTC - recommended)
     - `2026-01-05 00:00:00` (space-separated, will be normalized to ISO 8601 and assumed UTC)
     - `2026-01-05T00:00:00+07:00` (with timezone offset)
   - Only issues created after this time will be processed automatically
   - Useful when restarting the application locally to avoid missing issues created between restarts
   - If not set, the system uses the cache's system start time (first run time)

3. **Run:**

   ```bash
   docker-compose up -d
   docker-compose logs -f
   ```

4. **Access Dashboard:**
   - Open your browser and navigate to `http://localhost:8000` (or the port configured in `WEBHOOK_PORT`)
   - The dashboard provides:
     - **Statistics**: View processed issues count, app mode, and GitLab instance
     - **Manual Trigger**: Analyze specific issues by entering Project ID and Issue ID (IID)

## 📚 Documentation

- [Configuration Guide](./docs/CONFIGURATION.md) - All configuration options
- [Deployment Guide](./docs/DEPLOYMENT.md) - Platform-specific deployment
- [API Integration](./docs/API_INTEGRATION.md) - API details and examples
- [Architecture](./docs/ARCHITECTURE.md) - System design
- [Requirements](./docs/REQUIREMENTS.md) - Complete requirements
- [Documentation Index](./docs/INDEX.md) - All documentation

## 👨‍💻 For Developers

### Run Tests

### Code Quality

```bash
# Check formatting
black --check src/ main.py tests/
flake8 src/ main.py

# Auto-format
black src/ main.py tests/
isort src/ main.py tests/
```

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test
pytest tests/unit/test_config.py -v
```

### Development

**Using Docker with Live Code Mounting (Recommended):**

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Code changes will be picked up automatically (on next poll cycle or restart)
# No need to rebuild the container!
```

### Redeploy

**Docker Compose:**

```bash
docker-compose up -d --build
```

## 🔧 Configuration

Configuration is provided via environment variables (loaded from `.env` file or system environment).

See [Configuration Guide](./docs/CONFIGURATION.md) for all options.

## 🚢 Deployment

- **Docker**: See [Quick Start](#-quick-start) above
- **Other Platforms**: See [Deployment Guide](./docs/DEPLOYMENT.md) for deployment options

## 📝 License

MIT License

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Run code quality checks
6. Submit a pull request

---

For detailed documentation, see [docs/INDEX.md](./docs/INDEX.md)
