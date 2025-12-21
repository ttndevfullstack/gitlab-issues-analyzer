# Quick Start Guide

Get up and running with GitLab Issues Analyzer in 10 minutes.

## Prerequisites Checklist

- [ ] Python 3.9+ installed
- [ ] GitLab Personal Access Token (with `api` scope)
- [ ] DeepSeek API key
- [ ] SMTP credentials (Gmail/Outlook/etc.)
- [ ] GitLab project ID

## 5-Minute Setup

### Step 1: Clone and Install (2 min)

```bash
# Clone repository
git clone <your-repo-url>
cd gitlab-issues-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure (2 min)

Create `config.json`:

```json
{
  "gitlab": {
    "url": "https://gitlab.com",
    "token": "glpat-your-token-here",
    "project_id": "123456"
  },
  "deepseek": {
    "api_key": "sk-your-key-here"
  },
  "smtp": {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_email": "your-email@gmail.com",
    "to_email": "recipient@example.com"
  },
  "app": {
    "mode": "poll",
    "poll_interval": 900
  }
}
```

### Step 3: Test Run (1 min)

```bash
python main.py --mode poll --dry-run
```

### Step 4: Run (1 min)

```bash
# Polling mode
python main.py --mode poll

# Or webhook mode (requires webhook setup)
python main.py --mode webhook
```

## Getting Your Credentials

### GitLab Token
1. Go to GitLab → Settings → Access Tokens
2. Create token with `api` scope
3. Copy token (starts with `glpat-`)

### DeepSeek API Key
1. Sign up at [platform.deepseek.com](https://platform.deepseek.com/)
2. Go to API Keys section
3. Create new key
4. Copy key (starts with `sk-`)

### Gmail App Password
1. Enable 2-Factor Authentication
2. Go to Google Account → Security → App Passwords
3. Generate password for "Mail"
4. Use 16-character password (remove spaces)

## Common Issues

### "Missing required configuration"
→ Check all fields in `config.json` are filled

### "GitLab API authentication failed"
→ Verify token has `api` scope and is correct

### "SMTP authentication failed"
→ For Gmail, use App Password (not regular password)

### "DeepSeek API error"
→ Verify API key is valid and has credits

## Next Steps

- Read [Configuration Guide](./CONFIGURATION.md) for advanced options
- Check [Deployment Guide](./DEPLOYMENT.md) for production deployment
- Review [Architecture Document](./ARCHITECTURE.md) for system design

## Need Help?

- Check [Requirements Document](./REQUIREMENTS.md) for detailed specs
- Review [API Integration Guide](./API_INTEGRATION.md) for API details
- See [Project Rating](./PROJECT_RATING.md) for assessment


