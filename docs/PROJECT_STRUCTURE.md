# Project Structure

Recommended project structure for GitLab Issues Analyzer.

## Directory Layout

```
gitlab-issues-analyzer/
├── README.md                 # Main project documentation
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── config.example.json      # Example configuration file
│
├── main.py                  # Entry point
│
├── src/                     # Source code
│   ├── __init__.py
│   ├── monitor.py           # Issue monitoring (webhook/polling)
│   ├── analyzer.py          # DeepSeek API integration
│   ├── reporter.py          # Email report generation
│   ├── gitlab_client.py     # GitLab API client
│   ├── email_sender.py      # SMTP email sender
│   └── config.py            # Configuration management
│
├── tests/                   # Unit tests
│   ├── __init__.py
│   ├── test_monitor.py
│   ├── test_analyzer.py
│   ├── test_reporter.py
│   └── test_integration.py
│
└── docs/                    # Documentation
    ├── ARCHITECTURE.md
    ├── REQUIREMENTS.md
    ├── DEPLOYMENT.md
    ├── CONFIGURATION.md
    ├── API_INTEGRATION.md
    ├── PROJECT_RATING.md
    ├── QUICK_START.md
    └── PROJECT_STRUCTURE.md (this file)
```

## File Descriptions

### Root Files

- **`README.md`**: Main project overview, features, quick start
- **`requirements.txt`**: Python package dependencies
- **`.gitignore`**: Files to exclude from version control
- **`config.example.json`**: Example configuration (safe to commit)
- **`main.py`**: Application entry point, CLI interface

### Source Files (`src/`)

- **`monitor.py`**: 
  - Webhook server (Flask/FastAPI)
  - Polling logic
  - Issue detection and filtering

- **`analyzer.py`**:
  - DeepSeek API integration
  - Prompt building
  - WWWH-TR analysis formatting

- **`reporter.py`**:
  - Email template generation
  - HTML/text formatting
  - Report structure

- **`gitlab_client.py`**:
  - GitLab API wrapper
  - Issue fetching
  - Webhook payload parsing

- **`email_sender.py`**:
  - SMTP connection
  - Email sending
  - Retry logic

- **`config.py`**:
  - Configuration loading
  - Environment variable handling
  - Validation

### Test Files (`tests/`)

- Unit tests for each component
- Integration tests
- Mock API responses

### Documentation (`docs/`)

- Comprehensive guides
- API references
- Deployment instructions

## Module Dependencies

```
main.py
  ├── src.monitor
  │     ├── src.gitlab_client
  │     └── src.config
  ├── src.analyzer
  │     ├── src.config
  │     └── (DeepSeek API)
  └── src.reporter
        ├── src.email_sender
        ├── src.config
        └── src.analyzer (for analysis data)
```

## Implementation Order

### Phase 1: Core Infrastructure
1. `config.py` - Configuration management
2. `gitlab_client.py` - GitLab API integration
3. `email_sender.py` - SMTP integration

### Phase 2: Core Functionality
4. `analyzer.py` - DeepSeek integration
5. `reporter.py` - Email formatting
6. `monitor.py` - Issue detection

### Phase 3: Integration
7. `main.py` - Entry point and orchestration
8. Tests - Unit and integration tests

### Phase 4: Deployment
9. Deployment configuration
10. Documentation updates

## Code Organization Principles

### Separation of Concerns
- Each module has a single responsibility
- Clear interfaces between modules
- Minimal coupling

### Error Handling
- Centralized error handling
- Consistent error messages
- Proper logging

### Configuration
- Externalized configuration
- Environment variable support
- Validation on startup

### Testing
- Unit tests for each module
- Integration tests for workflows
- Mock external APIs

## Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`
- **Variables**: `snake_case`

## Import Organization

```python
# Standard library
import os
import json
from typing import Dict, List

# Third-party
import requests
from flask import Flask

# Local
from src.gitlab_client import GitLabClient
from src.analyzer import DeepSeekAnalyzer
```

## Future Enhancements

If the project grows, consider:

- `src/utils/` - Utility functions
- `src/models/` - Data models
- `src/validators/` - Input validation
- `scripts/` - Deployment and utility scripts
- `templates/` - Email templates (if using Jinja2)


