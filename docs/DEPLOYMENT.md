# Deployment Guide

This guide covers deployment options for GitLab Issues Analyzer.

## Table of Contents

- [Docker Deployment](#docker-deployment)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Docker Deployment

### Prerequisites

- Docker installed
- Docker Compose

### Production Docker Deployment

For production, use Docker Compose (recommended) or direct Docker commands:

**Using Docker Compose (Recommended):**

```bash
# Create .env file from .env.example and add your config
# Then start:
docker-compose up -d
```

**Using Docker directly:**

```bash
# Build production image
docker build -t gitlab-issues-analyzer:latest .

# Run with environment variables from .env file
docker run -d \
  --name gitlab-analyzer \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -p 8000:8000 \
  gitlab-issues-analyzer:latest
```

**Required Environment Variables:**

See `.env.example` for the complete list. Minimum required:
- `GITLAB_URL`, `GITLAB_TOKEN`
- `GITLAB_ISSUE_SCOPE`, `GITLAB_ISSUE_LABELS`
- `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_TO_EMAIL`

## Docker Compose Deployment

### Quick Start with Docker Compose

The easiest way to deploy is using `docker-compose.yml`:

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### Docker Compose Configuration

The `docker-compose.yml` file includes:
- Automatic restart policy
- Data volume persistence (`./data`)
- Health checks
- Environment variable loading from `.env` file
- Port mapping for dashboard/webhook (default: 8000)

### Development with Live Code Mounting

For development, use `docker-compose.dev.yml` to mount code for live updates:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

This mounts the source code, so changes are picked up automatically without rebuilding.

## Health Checks

### Docker Health Check

The Dockerfile includes a health check that verifies Python is working:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1
```

### Health Endpoint

The application exposes a health endpoint (available in both poll and webhook modes):

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "healthy",
  "service": "GitLab Issues Analyzer",
  "version": "0.1.0"
}
```

The health endpoint is always available when the Flask server is running (which starts automatically for the dashboard).

## Troubleshooting

### Common Issues

**Issue**: Container exits immediately

- **Solution**: Check logs with `docker logs gitlab-analyzer`
- **Solution**: Verify all required environment variables are set

**Issue**: Cannot connect to GitLab API

- **Solution**: Verify `GITLAB_URL` and `GITLAB_TOKEN` are correct
- **Solution**: Check network connectivity

**Issue**: Email sending fails

- **Solution**: Verify SMTP credentials
- **Solution**: Check firewall rules for SMTP port
- **Solution**: For Gmail, use App Password instead of regular password

**Issue**: Dashboard not accessible

- **Solution**: Verify port is exposed (default: 8000)
- **Solution**: Check firewall rules
- **Solution**: Verify `WEBHOOK_PORT` environment variable matches exposed port

### Debugging

1. **View logs:**

   ```bash
   # Using Docker Compose
   docker-compose logs -f
   
   # Using Docker directly
   docker logs -f gitlab-analyzer
   ```

2. **Execute commands in container:**

   ```bash
   # Using Docker Compose
   docker-compose exec gitlab-analyzer /bin/bash
   
   # Using Docker directly
   docker exec -it gitlab-analyzer /bin/bash
   ```

3. **Test configuration:**
   ```bash
   docker run --rm --env-file .env gitlab-issues-analyzer:latest python3 -c "from src.config import load_config, validate_config; config = load_config(); validate_config(config); print('✓ Config valid')"
   ```

4. **Check dashboard:**
   - Open browser to `http://localhost:8000` (or configured port)
   - View statistics and configuration
   - Test manual trigger

## Best Practices

1. **Security**:

   - Use secrets management (Docker secrets, Kubernetes secrets, etc.)
   - Never commit credentials to version control
   - Use non-root user in containers
   - Enable TLS/SSL for SMTP

2. **Monitoring**:

   - Set up log aggregation
   - Monitor container health
   - Set up alerts for failures

3. **Backup**:

   - Backup `data/analysis_cache.json` (contains processed issues and analysis results)
   - Keep `.env` file backups (securely stored)
   - Document deployment procedures

4. **Updates**:
   - Use version tags for Docker images
   - Test updates in staging first
   - Have rollback procedures ready

---

**Last Updated**: See document header for last update date.

**Documentation Version**: 1.0
