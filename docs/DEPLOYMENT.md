# Deployment Guide

Deployment instructions for GitLab Issues Analyzer.

## Docker Deployment (Recommended)

### Prerequisites

- Docker and Docker Compose installed
- `.env` file configured with all required variables

### Quick Start

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### Production Deployment

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Restart
docker-compose restart
```

### Development Deployment

For development with live code reloading:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Code changes are automatically picked up without rebuilding the container.

### Docker Compose Configuration

The `docker-compose.yml` includes:

- Automatic restart policy
- Data volume persistence (`./data`)
- Health checks
- Environment variable loading from `.env`
- Port mapping for dashboard/webhook (default: 8000)

## Health Checks

### Health Endpoint

The application exposes a health endpoint:

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "healthy",
  "service": "GitLab Issues Analyzer",
  "version": "1.0.0"
}
```

### Docker Health Check

The Dockerfile includes a health check that verifies the application is running:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1
```

## Troubleshooting

### Container Exits Immediately

- Check logs: `docker-compose logs`
- Verify all required environment variables are set
- Check for configuration errors in logs

### Cannot Connect to GitLab API

- Verify `GITLAB_URL` and `GITLAB_TOKEN` are correct
- Check token has `api` scope
- Verify network connectivity

### Email Sending Fails

- Verify SMTP credentials
- For Gmail, use App Password (not regular password)
- Check firewall rules for SMTP port (587 or 465)
- Verify `SMTP_HOST` and `SMTP_PORT` are correct

### Dashboard Not Accessible

- Verify port is exposed (default: 8000)
- Check `WEBHOOK_PORT` matches exposed port
- Check firewall rules
- Verify container is running: `docker-compose ps`

### Debugging

1. **View logs:**
   ```bash
   docker-compose logs -f
   ```

2. **Execute commands in container:**
   ```bash
   docker-compose exec gitlab-issues-analyzer /bin/bash
   ```

3. **Test configuration:**
   ```bash
   docker run --rm --env-file .env gitlab-issues-analyzer:latest \
     python3 -c "from src.config import load_config, validate_config; \
     config = load_config(); validate_config(config); print('✓ Config valid')"
   ```

4. **Check dashboard:**
   - Open `http://localhost:8000` in browser
   - View statistics and test manual trigger

## Best Practices

### Security

1. **Use secrets management** (Docker secrets, Kubernetes secrets, etc.)
2. **Never commit `.env` files** to version control
3. **Use non-root user** in containers (already configured)
4. **Enable TLS/SSL** for SMTP

### Monitoring

1. **Set up log aggregation** for production
2. **Monitor container health** via health checks
3. **Set up alerts** for failures
4. **Monitor API usage** and costs

### Backup

1. **Backup `data/analysis_cache.json`** (contains processed issues and analysis results)
2. **Keep `.env` backups** (securely stored, never in version control)
3. **Document deployment procedures**

### Updates

1. **Use version tags** for Docker images
2. **Test updates** in staging first
3. **Have rollback procedures** ready
4. **Review changelog** before updating

## Platform-Specific Deployment

### Docker on Linux/Mac/Windows

Follow the standard Docker deployment instructions above. Works identically across platforms.

### Cloud Platforms

The application can be deployed to any platform that supports Docker:

- **AWS ECS/Fargate**: Use Docker image
- **Google Cloud Run**: Use Docker image
- **Azure Container Instances**: Use Docker image
- **DigitalOcean App Platform**: Use Docker image
- **Heroku**: Use Docker buildpack

### Kubernetes

Deploy using standard Kubernetes manifests:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gitlab-issues-analyzer
spec:
  replicas: 1
  selector:
    matchLabels:
      app: gitlab-issues-analyzer
  template:
    metadata:
      labels:
        app: gitlab-issues-analyzer
    spec:
      containers:
      - name: analyzer
        image: gitlab-issues-analyzer:latest
        envFrom:
        - secretRef:
            name: gitlab-analyzer-secrets
        ports:
        - containerPort: 8000
```

## Next Steps

After deployment:

1. Verify health endpoint responds
2. Test manual trigger via dashboard
3. Monitor logs for first few issue analyses
4. Set up monitoring and alerts
5. Configure backups
