# Frequently Asked Questions

Common questions and troubleshooting for GitLab Issues Analyzer.

## General

### What is this project?

An automated tool that analyzes GitLab issues using AI and sends structured email reports using the WWWH-TR framework.

### Why WWWH-TR framework?

It provides a structured approach to understanding issues:
- **W1 — Why**: Root cause and goal
- **W2 — What**: Problem identification
- **W3 — Who**: Stakeholders
- **H — How**: Solutions and trade-offs
- **T — Test**: Quick experiments
- **R — Reflect**: Best choice and next steps

### Is this free?

Yes, designed to use free tiers:
- Free deployment (Docker, local)
- OpenRouter/OpenAI free tiers (check current limits)
- No database or paid services required

### How long does analysis take?

Typically 2-5 minutes per issue:
- Issue fetching: < 1 second
- AI analysis: 30-120 seconds
- Email sending: 1-5 seconds

## Technical

### Do I need a database?

No. The project is stateless. Uses file-based cache (`analysis_cache.json`) for processed issues.

### Webhook vs Polling mode?

- **Webhook**: Real-time, no rate limit concerns, requires public URL
- **Polling**: Simpler setup, works everywhere, may hit rate limits

### Can I use other AI providers?

Currently supports OpenRouter and OpenAI. The architecture supports adding more providers.

### What Python version?

Python 3.9 or higher.

### Can I analyze multiple projects?

Yes, the system uses the global GitLab issues API endpoint which can return issues from multiple projects. Filter by labels using `GITLAB_ISSUE_LABELS`.

## Configuration

### How do I get a GitLab token?

1. GitLab → Settings → Access Tokens
2. Create token with `api` scope
3. Copy token (starts with `glpat-`)

### How do I get an OpenRouter API key?

1. Sign up at [openrouter.ai](https://openrouter.ai/)
2. Go to API Keys section
3. Create new key
4. Copy key (starts with `sk-or-`)

### Can I use Gmail for SMTP?

Yes, but you need an App Password:
1. Enable 2FA on Google account
2. Generate App Password for "Mail"
3. Use the 16-character password (remove spaces)

### Can I send to multiple recipients?

Yes, use comma-separated list in `SMTP_TO_EMAIL`:
```
SMTP_TO_EMAIL=email1@example.com,email2@example.com
```

## Deployment

### Which deployment platform is best?

**Docker/Docker Compose** is recommended for easy setup and supports both polling and webhook modes.

### How do I set up GitLab webhook?

1. Deploy app and get public URL
2. GitLab → Project → Settings → Webhooks
3. URL: `https://your-app.com/webhook`
4. Secret: Your webhook secret (set in `GITLAB_WEBHOOK_SECRET`)
5. Trigger: "Issue events"

### Will it work on self-hosted GitLab?

Yes, just set `GITLAB_URL` to your instance URL.

### Can I run it locally?

Yes, use Docker Compose or run directly with Python. Polling mode works without public URL.

## Usage

### Will it analyze all issues?

By default, yes. You can filter by labels, scope, etc. using configuration variables.

### What if an issue is updated?

Currently only processes new issues. Update notifications can be added as enhancement.

### What if the AI analysis fails?

The system will retry with exponential backoff (3 attempts). If it fails completely, an error is logged and stored in cache. Check logs and manually review the issue.

### Can I customize the email format?

Yes, modify `src/reporter.py` to change email templates.

### How do I avoid duplicate emails?

The system tracks processed issue IDs in `analysis_cache.json`. Issues are only processed once.

## Troubleshooting

### "Missing required configuration" error

Check all required environment variables are set in your `.env` file or system environment. See [Configuration Guide](./CONFIGURATION.md).

### "GitLab API authentication failed"

- Verify token is correct
- Check token has `api` scope
- Verify GitLab URL is correct

### "SMTP authentication failed"

- For Gmail, use App Password (not regular password)
- Check SMTP host and port
- Verify firewall isn't blocking port 587 or 465

### "AI API error"

- Verify API key is valid (OpenRouter or OpenAI)
- Check API key has credits/balance
- Verify model name is correct (e.g., `tngtech/deepseek-r1t2-chimera:free` for OpenRouter)

### Webhook not receiving events

- Check webhook URL is accessible
- Verify secret token matches
- Check GitLab webhook logs
- Ensure "Issue events" trigger is enabled

### Rate limit errors

- Reduce polling frequency (`POLL_INTERVAL`)
- Use webhook mode instead
- Check API provider rate limits

## Cost

### How much will AI API cost?

Check OpenRouter or OpenAI pricing. Free tiers usually have limits. Monitor usage in the provider dashboard.

### Are there any hidden costs?

No, if you stay within free tiers:
- Deployment: Free (Docker, local deployment)
- GitLab: Free (API access included)
- SMTP: Free (Gmail/Outlook free tier)
- AI API: Free tier (check OpenRouter/OpenAI limits)

### What if I exceed free tier limits?

- AI API: Upgrade to paid tier or reduce usage
- Deployment: Some platforms have paid tiers, but free tier usually sufficient
- GitLab: API limits are generous (2000 req/hour)

## Security

### Are my credentials safe?

- Never commit `.env` file to git (it's in `.gitignore`)
- Use environment variables in production
- Use App Passwords (not main passwords)
- Rotate credentials periodically

### How secure are webhooks?

- Webhook secret token validation
- HTTPS required for production
- Request signature verification (if available)

### Should I expose my API keys?

Never. Use environment variables or secure config files. Never commit to version control.

## Still Have Questions?

- Check [Configuration Guide](./CONFIGURATION.md) for config questions
- Review [Deployment Guide](./DEPLOYMENT.md) for deployment issues
- See [API Integration Guide](./API_INTEGRATION.md) for API details
- Read [Architecture Document](./ARCHITECTURE.md) for system design
