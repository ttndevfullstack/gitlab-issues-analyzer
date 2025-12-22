# GitLab Issues Analyzer

A lightweight, automated tool that analyzes new GitLab issues using AI and sends structured email reports based on the WWWH-TR thinking framework.

## 🎯 Project Overview

This project automates the analysis of GitLab issues to save time on manual ticket review. When a new issue is created, the system:

1. Fetches comprehensive issue data from GitLab (including comments, related issues, attachments)
2. Analyzes the issue using AI (DeepSeek, ChatGPT, Claude, or other providers)
3. Structures the analysis using the WWWH-TR framework
4. Sends an email notification with the analysis report

## 🧭 WWWH-TR Framework

The analysis follows this structured thinking approach:

- **W1 — Why**: Why is this needed? → Understand root cause, identify ultimate goal
- **W2 — What**: What specifically? → Identify the problem, gather information
- **W3 — Who**: Who is involved/affected? → Identify people who can help
- **H — How**: What are the possible approaches? → Identify feasible solutions + comparison + trade-offs
- **T — Test**: How to test small? → Quick experiments + measurement milestones (feasibility, time, cost, etc.)
- **R — Reflect**: What is the best choice? → Evaluation + conclusion + next steps + adjustments

## ✨ Features

- **Automated Issue Detection**: Monitors GitLab for new issues via webhooks or polling
- **Comprehensive Data Collection**: Analyzes all issue information including comments, related issues, attachments, and images
- **Multi-Provider AI Support**: Supports DeepSeek, OpenAI ChatGPT, Anthropic Claude, and other OpenAI-compatible APIs
- **Dynamic Model Selection**: Easily switch between AI providers and models via configuration
- **Structured Reports**: Formats analysis using WWWH-TR framework
- **Email Notifications**: Sends formatted reports via SMTP
- **Lightweight**: No database, minimal dependencies
- **Zero Cost**: Uses free tiers and open-source tools
- **Easy Deployment**: Simple setup for various platforms

## 🏗️ Architecture

```
┌─────────────┐
│   GitLab    │
│   Issues    │
└──────┬──────┘
       │
       │ (Webhook/Polling)
       ▼
┌─────────────────────┐
│  Issue Monitor      │
│  (Webhook Handler/  │
│   Polling Service)  │
└──────┬──────────────┘
       │
       │ (Fetch Issue Data)
       ▼
┌─────────────────────┐
│  Issue Analyzer     │
│  (AI API: DeepSeek/ │
│   ChatGPT/Claude)   │
└──────┬──────────────┘
       │
       │ (WWWH-TR Analysis)
       ▼
┌─────────────────────┐
│  Report Generator   │
│  (Format Email)     │
└──────┬──────────────┘
       │
       │ (SMTP)
       ▼
┌─────────────┐
│   Email     │
│  Recipient  │
└─────────────┘
```

## 📋 Requirements

- Python 3.9+
- GitLab API access (Personal Access Token)
- AI Provider API key (DeepSeek, OpenAI, Anthropic, or compatible)
- SMTP server credentials
- Internet connection

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd gitlab-issues-analyzer
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration

Copy `config.example.json` to `config.json` and fill in your credentials:

```json
{
  "gitlab": {
    "url": "https://gitlab.com",
    "token": "your-gitlab-token",
    "project_id": "your-project-id"
  },
  "ai": {
    "provider": "deepseek",
    "api_key": "your-ai-api-key",
    "model": "deepseek-chat",
    "temperature": 0.7
  },
  "smtp": {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_email": "your-email@gmail.com",
    "to_email": "recipient@example.com"
  },
  "webhook": {
    "secret_token": "your-webhook-secret",
    "port": 8000
  }
}
```

### 3. Run

**Option A: Webhook Mode (Recommended)**
```bash
python main.py --mode webhook
```

**Option B: Polling Mode**
```bash
python main.py --mode poll --interval 300
```

## 📚 Documentation

- [Architecture Document](./docs/ARCHITECTURE.md) - Detailed system design
- [Requirements Document](./docs/REQUIREMENTS.md) - Complete requirements specification
- [Deployment Guide](./docs/DEPLOYMENT.md) - Deployment instructions for various platforms
- [Configuration Guide](./docs/CONFIGURATION.md) - Configuration options and examples
- [API Integration Guide](./docs/API_INTEGRATION.md) - GitLab and DeepSeek API integration details

## 🔧 Configuration Options

See [Configuration Guide](./docs/CONFIGURATION.md) for detailed options.

## 🚢 Deployment

See [Deployment Guide](./docs/DEPLOYMENT.md) for platform-specific instructions.

## 📝 License

MIT License

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!


