# Deployment Guide

This guide covers deployment options for the GitLab Issues Analyzer on various free platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [GitHub Actions Deployment](#github-actions-deployment)
4. [Railway Deployment](#railway-deployment)
5. [Render Deployment](#render-deployment)
6. [Fly.io Deployment](#flyio-deployment)
7. [Local Deployment](#local-deployment)
8. [Configuration for Deployment](#configuration-for-deployment)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying, ensure you have:

1. **GitLab Access**
   - Personal Access Token with `api` scope
   - Project ID or project path
   - Webhook secret (if using webhook mode)

2. **DeepSeek API Key**
   - Sign up at [DeepSeek](https://platform.deepseek.com/)
   - Generate API key
   - Note your API key

3. **SMTP Credentials**
   - Email account with SMTP access
   - App password (for Gmail/Outlook)
   - SMTP server details

4. **Git Repository**
   - Code pushed to GitHub/GitLab
   - Repository access for deployment platform

## Deployment Options

### Comparison Table

| Platform | Mode | Cost | Setup Complexity | Best For |
|----------|------|------|------------------|----------|
| GitHub Actions | Polling | Free | Easy | Automated scheduling |
| Railway | Webhook/Polling | Free tier | Medium | Real-time webhooks |
| Render | Webhook/Polling | Free tier | Medium | Simple web services |
| Fly.io | Webhook/Polling | Free tier | Medium | Global distribution |
| Local Cron | Polling | Free | Easy | Personal use |

## GitHub Actions Deployment

### Overview
GitHub Actions runs on a schedule (polling mode). Webhook mode is not supported as GitLab webhooks cannot reach GitHub Actions.

### Steps

1. **Create GitHub Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/gitlab-issues-analyzer.git
   git push -u origin main
   ```

2. **Set Up Secrets**
   - Go to repository → Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `GITLAB_URL`: Your GitLab instance URL
     - `GITLAB_TOKEN`: Your GitLab Personal Access Token
     - `GITLAB_PROJECT_ID`: Your project ID
     - `DEEPSEEK_API_KEY`: Your DeepSeek API key
     - `SMTP_HOST`: SMTP server host
     - `SMTP_PORT`: SMTP port (usually 587)
     - `SMTP_USERNAME`: SMTP username
     - `SMTP_PASSWORD`: SMTP password/app password
     - `SMTP_FROM_EMAIL`: Sender email
     - `SMTP_TO_EMAIL`: Recipient email

3. **Create Workflow File**
   Create `.github/workflows/analyze-issues.yml`:
   ```yaml
   name: Analyze GitLab Issues
   
   on:
     schedule:
       - cron: '*/15 * * * *'  # Every 15 minutes
     workflow_dispatch:  # Manual trigger
   
   jobs:
     analyze:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         
         - name: Install dependencies
           run: |
             pip install -r requirements.txt
         
         - name: Run analyzer
           env:
             GITLAB_URL: ${{ secrets.GITLAB_URL }}
             GITLAB_TOKEN: ${{ secrets.GITLAB_TOKEN }}
             GITLAB_PROJECT_ID: ${{ secrets.GITLAB_PROJECT_ID }}
             DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
             SMTP_HOST: ${{ secrets.SMTP_HOST }}
             SMTP_PORT: ${{ secrets.SMTP_PORT }}
             SMTP_USERNAME: ${{ secrets.SMTP_USERNAME }}
             SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
             SMTP_FROM_EMAIL: ${{ secrets.SMTP_FROM_EMAIL }}
             SMTP_TO_EMAIL: ${{ secrets.SMTP_TO_EMAIL }}
             APP_MODE: poll
             POLL_INTERVAL: 900
           run: |
             python main.py
   ```

4. **Verify Deployment**
   - Go to Actions tab in GitHub
   - Check workflow runs
   - Review logs for errors

### Pros
- ✅ Free tier: 2000 minutes/month
- ✅ Easy setup
- ✅ Integrated with GitHub
- ✅ Scheduled execution

### Cons
- ❌ No webhook support
- ❌ Limited to polling mode
- ❌ May hit rate limits with frequent polling

## Railway Deployment

### Overview
Railway supports both webhook and polling modes. Free tier includes 500 hours/month.

### Steps

1. **Create Railway Account**
   - Sign up at [Railway](https://railway.app/)
   - Connect GitHub account

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Environment Variables**
   - Go to project → Variables
   - Add all required environment variables (same as GitHub Actions secrets)

4. **Configure Service**
   - Set start command: `python main.py --mode webhook`
   - Railway will auto-detect Python and install dependencies

5. **Set Up GitLab Webhook** (if using webhook mode)
   - Get Railway public URL from project settings
   - In GitLab: Project → Settings → Webhooks
   - URL: `https://your-app.railway.app/webhook`
   - Secret token: Your webhook secret
   - Trigger: "Issue events"

6. **Deploy**
   - Railway auto-deploys on git push
   - Check logs for deployment status

### Pros
- ✅ Free tier available
- ✅ Webhook support
- ✅ Auto-deployment
- ✅ Easy configuration

### Cons
- ❌ Free tier limited hours
- ❌ May sleep after inactivity

## Render Deployment

### Overview
Similar to Railway, supports webhook and polling modes. Free tier available.

### Steps

1. **Create Render Account**
   - Sign up at [Render](https://render.com/)
   - Connect GitHub account

2. **Create Web Service**
   - Click "New" → "Web Service"
   - Connect your repository
   - Settings:
     - **Name**: gitlab-issues-analyzer
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python main.py --mode webhook`
     - **Plan**: Free

3. **Add Environment Variables**
   - Go to Environment section
   - Add all required variables

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy
   - Get public URL from dashboard

5. **Set Up GitLab Webhook** (if using webhook mode)
   - Use Render public URL
   - Configure in GitLab (same as Railway)

### Pros
- ✅ Free tier available
- ✅ Webhook support
- ✅ Auto-deployment
- ✅ Simple interface

### Cons
- ❌ Free tier may sleep after inactivity
- ❌ Slower cold starts

## Fly.io Deployment

### Overview
Fly.io offers global distribution. Free tier includes 3 shared VMs.

### Steps

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login to Fly.io**
   ```bash
   fly auth login
   ```

3. **Create Fly App**
   ```bash
   fly launch
   ```
   - Follow prompts
   - Select region
   - Don't deploy yet

4. **Configure Secrets**
   ```bash
   fly secrets set GITLAB_URL=your-url
   fly secrets set GITLAB_TOKEN=your-token
   # ... set all other secrets
   ```

5. **Create `fly.toml`**
   ```toml
   app = "gitlab-issues-analyzer"
   primary_region = "iad"
   
   [build]
   
   [http_service]
     internal_port = 8000
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0
   
   [[services]]
     protocol = "tcp"
     internal_port = 8000
   ```

6. **Deploy**
   ```bash
   fly deploy
   ```

7. **Set Up GitLab Webhook**
   - Get app URL: `https://gitlab-issues-analyzer.fly.dev`
   - Configure in GitLab

### Pros
- ✅ Free tier available
- ✅ Global distribution
- ✅ Webhook support
- ✅ Fast deployment

### Cons
- ❌ CLI required
- ❌ More complex setup

## Local Deployment

### Overview
Run on your local machine using cron (Linux/Mac) or Task Scheduler (Windows).

### Steps

1. **Install Dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Create Config File**
   - Copy `config.example.json` to `config.json`
   - Fill in all credentials

3. **Test Run**
   ```bash
   python main.py --mode poll
   ```

4. **Set Up Cron Job** (Linux/Mac)
   ```bash
   crontab -e
   ```
   Add:
   ```cron
   */15 * * * * cd /path/to/gitlab-issues-analyzer && /path/to/venv/bin/python main.py --mode poll >> /tmp/gitlab-analyzer.log 2>&1
   ```

5. **Set Up Task Scheduler** (Windows)
   - Open Task Scheduler
   - Create Basic Task
   - Trigger: Daily/On a schedule
   - Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `main.py --mode poll`
   - Start in: Project directory

### Pros
- ✅ Full control
- ✅ No platform limits
- ✅ Free
- ✅ Can run webhook mode with port forwarding

### Cons
- ❌ Requires always-on machine
- ❌ Manual setup
- ❌ No automatic updates

## Configuration for Deployment

### Environment Variables

All platforms use environment variables. Here's the complete list:

```bash
# GitLab
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=glpat-xxxxx
GITLAB_PROJECT_ID=123456
GITLAB_WEBHOOK_SECRET=your-secret

# DeepSeek
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TEMPERATURE=0.7

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_TO_EMAIL=recipient@example.com

# App
APP_MODE=webhook|poll
POLL_INTERVAL=900
WEBHOOK_PORT=8000
LOG_LEVEL=INFO
```

### Config File Alternative

For local deployment, you can use `config.json` instead of environment variables.

## Troubleshooting

### Common Issues

1. **Webhook Not Receiving Events**
   - Check webhook URL is accessible
   - Verify secret token matches
   - Check GitLab webhook logs
   - Ensure webhook is enabled for "Issue events"

2. **API Rate Limits**
   - Reduce polling frequency
   - Implement rate limiting in code
   - Check API usage limits

3. **Email Not Sending**
   - Verify SMTP credentials
   - Check firewall/network restrictions
   - Use app password for Gmail
   - Check SMTP server logs

4. **DeepSeek API Errors**
   - Verify API key is valid
   - Check API rate limits
   - Verify model name is correct
   - Check API status page

5. **Deployment Failures**
   - Check build logs
   - Verify Python version compatibility
   - Ensure all dependencies are in `requirements.txt`
   - Check environment variables are set

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python main.py
```

### Health Check

Test individual components:
```bash
# Test GitLab connection
python -c "from src.gitlab_client import GitLabClient; print(GitLabClient().test_connection())"

# Test SMTP
python -c "from src.email_sender import EmailSender; EmailSender().test_connection()"
```

## Next Steps

After deployment:

1. Monitor logs for first few issues
2. Verify email delivery
3. Check analysis quality
4. Adjust configuration as needed
5. Set up monitoring/alerts (optional)


