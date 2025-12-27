# Frequently Asked Questions

## General Questions

### Q: What is this project?
**A**: An automated tool that analyzes GitLab issues using AI and sends structured email reports using the WWWH-TR framework.

### Q: Why WWWH-TR framework?
**A**: It provides a structured approach to understanding issues:
- **W1 — Why**: Root cause and goal
- **W2 — What**: Problem identification
- **W3 — Who**: Stakeholders
- **H — How**: Solutions and trade-offs
- **T — Test**: Quick experiments
- **R — Reflect**: Best choice and next steps

### Q: Is this free?
**A**: Yes, designed to use free tiers:
- Free deployment platforms (Docker, local deployment)
- OpenRouter/OpenAI free tiers (check current limits)
- No database or paid services required

### Q: How long does analysis take?
**A**: Typically 2-5 minutes per issue:
- Issue fetching: < 1 second
- AI analysis: 30-120 seconds
- Email sending: 1-5 seconds

## Technical Questions

### Q: Do I need a database?
**A**: No. The project is designed to be stateless. Optional file-based tracking for processed issues.

### Q: Webhook vs Polling mode?
**A**: 
- **Webhook**: Real-time, no rate limit concerns, requires public URL
- **Polling**: Simpler setup, works everywhere, may hit rate limits

### Q: Can I use other AI providers?
**A**: The architecture supports it, but DeepSeek is recommended for thinking mode. You'd need to modify `analyzer.py` to use other providers.

### Q: What Python version?
**A**: Python 3.9 or higher.

### Q: Can I analyze multiple projects?
**A**: Yes, the system uses the global GitLab issues API endpoint which can return issues from multiple projects. Filter by labels using `GITLAB_ISSUE_LABELS` to target specific issues.

## Configuration Questions

### Q: How do I get a GitLab token?
**A**: 
1. GitLab → Settings → Access Tokens
2. Create token with `api` scope
3. Copy token (starts with `glpat-`)

### Q: How do I get an OpenRouter API key?
**A**: 
1. Sign up at [openrouter.ai](https://openrouter.ai/)
2. Go to API Keys section
3. Create new key
4. Copy key (starts with `sk-or-`)

### Q: Can I use Gmail for SMTP?
**A**: Yes, but you need an App Password:
1. Enable 2FA on Google account
2. Generate App Password for "Mail"
3. Use the 16-character password (remove spaces)

### Q: Can I send to multiple recipients?
**A**: Yes, use an array in `smtp.to_email`:
```json
{
  "smtp": {
    "to_email": ["email1@example.com", "email2@example.com"]
  }
}
```

## Deployment Questions

### Q: Which deployment platform is best?
**A**: Depends on needs:
- **Docker/Docker Compose**: Recommended, easy setup, supports both polling and webhook modes
- **Local**: Full control, requires always-on machine
- **Cloud platforms**: Can deploy Docker containers to various cloud providers

### Q: How do I set up GitLab webhook?
**A**: 
1. Deploy app and get public URL
2. GitLab → Settings → Webhooks
3. URL: `https://your-app.com/webhook`
4. Secret: Your webhook secret
5. Trigger: "Issue events"

### Q: Will it work on self-hosted GitLab?
**A**: Yes, just set `GITLAB_URL` to your instance URL.

### Q: Can I run it locally?
**A**: Yes, use polling mode with cron (Linux/Mac) or Task Scheduler (Windows).

## Usage Questions

### Q: Will it analyze all issues?
**A**: By default, yes. You can filter by labels, assignee, etc. in configuration.

### Q: What if an issue is updated?
**A**: Currently only processes new issues. Update notifications can be added as enhancement.

### Q: What if the AI analysis fails?
**A**: The system will retry (with backoff). If it fails completely, an error is logged. You can check logs and manually review the issue.

### Q: Can I customize the email format?
**A**: Yes, modify `reporter.py` to change email templates.

### Q: How do I avoid duplicate emails?
**A**: The system tracks processed issue IDs. In polling mode, use file-based tracking to persist across restarts.

## Troubleshooting

### Q: "Missing required configuration" error
**A**: Check all required environment variables are set in your `.env` file or system environment.

### Q: "GitLab API authentication failed"
**A**: 
- Verify token is correct
- Check token has `api` scope
- Verify GitLab URL is correct

### Q: "SMTP authentication failed"
**A**: 
- For Gmail, use App Password (not regular password)
- Check SMTP host and port
- Verify firewall isn't blocking

### Q: "AI API error"
**A**: 
- Verify API key is valid (OpenRouter or OpenAI)
- Check API key has credits
- Verify model name is correct (e.g., `deepseek/deepseek-v3.2` for OpenRouter)

### Q: Webhook not receiving events
**A**: 
- Check webhook URL is accessible
- Verify secret token matches
- Check GitLab webhook logs
- Ensure "Issue events" trigger is enabled

### Q: Rate limit errors
**A**: 
- Reduce polling frequency
- Use webhook mode instead
- Implement rate limiting in code

## Cost Questions

### Q: How much will AI API cost?
**A**: Check OpenRouter or OpenAI pricing. Free tiers usually have limits. Monitor usage in the provider dashboard.

### Q: Are there any hidden costs?
**A**: No, if you stay within free tiers:
- Deployment: Free (Docker, local deployment)
- GitLab: Free (API access included)
- SMTP: Free (Gmail/Outlook free tier)
- AI API: Free tier (check OpenRouter/OpenAI limits)

### Q: What if I exceed free tier limits?
**A**: 
- AI API: Upgrade to paid tier or reduce usage (OpenRouter/OpenAI)
- Deployment: Some platforms have paid tiers, but free tier usually sufficient
- GitLab: API limits are generous (2000 req/hour)

## Security Questions

### Q: Are my credentials safe?
**A**: 
- Never commit `.env` file to git (it's in `.gitignore`)
- Use environment variables in production
- Use App Passwords (not main passwords)
- Rotate credentials periodically

### Q: How secure are webhooks?
**A**: 
- Webhook secret token validation
- HTTPS required for production
- Request signature verification (if available)

### Q: Should I expose my API keys?
**A**: Never. Use environment variables or secure config files. Never commit to version control.

## Enhancement Questions

### Q: Can I add Slack notifications?
**A**: Yes, modify `reporter.py` to add Slack webhook integration.

### Q: Can I analyze comments?
**A**: Currently only issue title/description. Comments can be added by fetching issue comments from GitLab API.

### Q: Can I prioritize issues?
**A**: Not currently, but you can filter by labels. Priority scoring can be added as enhancement.

### Q: Can I get a dashboard?
**A**: Not in current scope. Can be added as future enhancement with a simple web interface.

## Still Have Questions?

- Check [Configuration Guide](./CONFIGURATION.md) for config questions
- Review [Deployment Guide](./DEPLOYMENT.md) for deployment issues
- See [API Integration Guide](./API_INTEGRATION.md) for API details
- Read [Architecture Document](./ARCHITECTURE.md) for system design


