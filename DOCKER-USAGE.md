# Docker Usage Guide

## Published Docker Images

After v1.0.0 release, images will be available at:

```
ghcr.io/iamgini/ansible-maya:latest
ghcr.io/iamgini/ansible-maya:1.0.0
ghcr.io/iamgini/ansible-maya:1.0
ghcr.io/iamgini/ansible-maya:1
```

## Quick Start with Docker

### Pull and Run

```bash
# Pull latest image
docker pull ghcr.io/iamgini/ansible-maya:latest

# Run with API key
docker run -d \
  --name ansible-maya \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-your-key-here \
  ghcr.io/iamgini/ansible-maya:latest

# Check health
curl http://localhost:8000/health

# View logs
docker logs ansible-maya

# Stop
docker stop ansible-maya
docker rm ansible-maya
```

### Using Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/iamgini/ansible-maya.git
cd ansible-maya

# Configure environment
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Configuration

### Environment Variables

Required:
- `ANTHROPIC_API_KEY` - Your Claude API key (for Claude provider)

Optional:
- `LLM_PROVIDER` - Provider to use (default: `claude`)
- `CUSTOM_API_BASE_URL` - For custom OpenAI-compatible providers
- `CUSTOM_API_KEY` - API key for custom provider
- `SAGE_LOG_LEVEL` - Log level (default: `INFO`)
- `SAGE_ANSIBLE_LINT_AUTO_FIX` - Auto-fix lint issues (default: `true`)

### Volume Mounts

```bash
docker run -d \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-your-key \
  -v /path/to/generated:/app/generated_playbooks \
  -v /path/to/logs:/app/logs \
  ghcr.io/iamgini/ansible-maya:latest
```

## Testing the API

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs

# Generate playbook
curl -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "disk_full",
    "description": "Disk usage at 95% on /var",
    "host": "web-server-01",
    "severity": "high",
    "metadata": {
      "partition": "/var",
      "usage_percent": 95
    }
  }'
```

## Building Locally

```bash
# Build from source
docker build -t ansible-maya:local .

# Run local build
docker run -d -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-your-key \
  ansible-maya:local
```

## Multi-Architecture Support

Images are built for both AMD64 and ARM64:

```bash
# Pull specific architecture (automatic based on your system)
docker pull ghcr.io/iamgini/ansible-maya:latest

# Verify architecture
docker inspect ghcr.io/iamgini/ansible-maya:latest | grep Architecture
```

## Production Deployment

### Docker Swarm

```yaml
# docker-stack.yml
version: '3.8'

services:
  ansible-maya:
    image: ghcr.io/iamgini/ansible-maya:1.0.0
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
    networks:
      - maya-network

networks:
  maya-network:
    driver: overlay
```

Deploy:
```bash
docker stack deploy -c docker-stack.yml ansible-maya
```

### Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ansible-maya
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ansible-maya
  template:
    metadata:
      labels:
        app: ansible-maya
    spec:
      containers:
      - name: ansible-maya
        image: ghcr.io/iamgini/ansible-maya:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: maya-secrets
              key: anthropic-api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: ansible-maya-service
spec:
  selector:
    app: ansible-maya
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy:
```bash
# Create secret
kubectl create secret generic maya-secrets \
  --from-literal=anthropic-api-key=sk-ant-your-key

# Deploy
kubectl apply -f deployment.yaml
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs ansible-maya

# Common issues:
# 1. Missing ANTHROPIC_API_KEY
# 2. Port 8000 already in use
# 3. Insufficient memory
```

### Health check failing

```bash
# Check from inside container
docker exec ansible-maya curl http://localhost:8000/health

# Check Python process
docker exec ansible-maya ps aux | grep uvicorn
```

### Permission issues

```bash
# Container runs as non-root user (UID 1000)
# Ensure volume mount directories have correct permissions
chown -R 1000:1000 /path/to/generated_playbooks
```

## Security Best Practices

1. **Never commit API keys** - Use environment variables or secrets management
2. **Use specific version tags** - Avoid `latest` in production
3. **Scan images** - `docker scan ghcr.io/iamgini/ansible-maya:1.0.0`
4. **Limit resources** - Use Docker resource constraints
5. **Network isolation** - Use Docker networks for service communication
6. **Regular updates** - Keep images up to date with security patches

## Image Details

```bash
# View image details
docker inspect ghcr.io/iamgini/ansible-maya:1.0.0

# Check image size
docker images ghcr.io/iamgini/ansible-maya

# View layers
docker history ghcr.io/iamgini/ansible-maya:1.0.0
```

## Support

- 🐛 **Issues**: https://github.com/iamgini/ansible-maya/issues
- 💬 **Discussions**: https://github.com/iamgini/ansible-maya/discussions
- 📚 **Documentation**: https://github.com/iamgini/ansible-maya#readme
