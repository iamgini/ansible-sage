# Ansible Maya - Quick Start Guide

Get started with Ansible Maya in 5 minutes!

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized deployment)
- Anthropic API key (for Claude) or other LLM provider

## Installation

### Option 1: Local Development

```bash
# Clone or navigate to the repository
cd /path/to/ansible-maya

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
# Or: make install-dev  # For development

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Option 2: Docker (Recommended)

**Using published image:**
```bash
# Pull from Quay.io
docker pull quay.io/iamgini/ansible-maya:0.2.0

# Run container
docker run -d \
  --name ansible-maya \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-your-key-here \
  quay.io/iamgini/ansible-maya:0.2.0

# Check health
curl http://localhost:8000/health
```

**Using docker-compose (local development):**
```bash
cd /path/to/ansible-maya

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f ansible-maya
```

## Quick Examples

### 1. CLI: Generate a Playbook

```bash
# Simple disk cleanup playbook
ansible-maya generate \
  --event-type disk_full \
  --description "Disk usage at 95% on /var partition" \
  --host web-server-01 \
  --severity high \
  --output cleanup.yml

# Review the generated playbook
cat cleanup.yml

# Validate it
ansible-maya validate cleanup.yml
```

### 2. Python API

```python
import asyncio
from ansible_maya.core.providers import get_provider
from ansible_maya.handlers.orchestrator import handle_infrastructure_event, EventSeverity

async def main():
    # Initialize provider
    provider = get_provider("claude", config={
        "api_key": "your-api-key"
    })
    
    # Generate playbook
    response = await handle_infrastructure_event(
        event_description="Nginx service is down on web-server-01",
        event_type="service_down",
        host="web-server-01",
        provider=provider,
        severity=EventSeverity.CRITICAL,
    )
    
    # Print results
    print(response.playbook)
    print(f"\nValidation: {'✓ Passed' if response.validation_result.passed else '✗ Failed'}")
    print(f"Recommendation: {response.recommended_action}")

asyncio.run(main())
```

### 3. REST API

```bash
# Start the API server
ansible-maya serve

# In another terminal, generate a playbook
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
  }' | jq .

# Access interactive API docs
open http://localhost:8000/docs
```

### 4. Two-Phase Generation (Spec-Kit)

```bash
# Phase 1: Get execution plan
curl -X POST http://localhost:8000/api/v1/specs/plan \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "service_down",
    "description": "Nginx service stopped",
    "host": "web-01"
  }' | jq .

# Review plan, then approve with spec_id
curl -X POST http://localhost:8000/api/v1/specs/{spec_id}/generate \
  -d '{"approved": true}'
```

### 5. Multi-Agent Review (Higher Quality)

```bash
# Enable multi-agent review for better quality
curl -X POST "http://localhost:8000/api/v1/events/generate?multi_agent_review=true" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "disk_full",
    "description": "Disk at 95%",
    "host": "web-server-01"
  }' | jq .

# Response includes security + best practices review
# Confidence score boosted by +5% to +15%
```

## Common Event Types

### Disk Issues
```bash
ansible-maya generate \
  --event-type disk_full \
  --description "Disk at 95% on /var, logs consuming space" \
  --host db-server-01 \
  --severity high
```

### Service Management
```bash
ansible-maya generate \
  --event-type service_down \
  --description "Apache httpd service stopped unexpectedly" \
  --host web-server-02 \
  --severity critical
```

### Resource Alerts
```bash
ansible-maya generate \
  --event-type high_cpu \
  --description "CPU usage at 98% for 10 minutes" \
  --host app-server-01 \
  --severity high
```

### Memory Issues
```bash
ansible-maya generate \
  --event-type high_memory \
  --description "Memory usage at 92%, swap heavily used" \
  --host cache-server-01 \
  --severity medium
```

## Testing the System

### Run Tests
```bash
# Unit tests
make test-unit

# Integration tests (requires API key)
make test-integration

# All tests with coverage
make test-cov
```

### Validate a Generated Playbook
```bash
# Generate and validate in one go
ansible-maya generate \
  --event-type disk_cleanup_tmp \
  --description "Clean /tmp directory" \
  --host localhost \
  --output test.yml && \
ansible-maya validate test.yml --fix
```

## Project Structure

```
ansible-maya/
├── ansible_maya/                      # Main package
│   ├── core/                  # Core business logic
│   │   ├── providers/         # LLM providers (Claude, OpenAI, etc.)
│   │   ├── ansible_context.py # Ansible-specific processing
│   │   ├── prompt_templates.py# System prompts
│   │   └── exceptions.py      # Custom exceptions
│   ├── handlers/              # Event handling
│   │   └── orchestrator.py    # Main orchestration logic
│   ├── validation/            # Validation tools
│   │   └── ansible_lint.py    # ansible-lint integration
│   ├── api/                   # REST API
│   │   ├── server.py          # FastAPI application
│   │   └── routes/            # API endpoints
│   └── cli.py                 # Command-line interface
├── examples/                  # Usage examples
├── tests/                     # Test suite
├── docker-compose.yml         # Container orchestration
└── Makefile                   # Common commands
```

## Next Steps

1. **Explore Examples**: Check out `examples/` directory for detailed usage
2. **Read Documentation**: See `README.md` for comprehensive guide
3. **Review CLAUDE.md**: Developer guidance for extending the system
4. **Configure Integrations**: Set up AAP, Prometheus, or EDA integrations
5. **Customize Prompts**: Edit `ansible_maya/core/prompt_templates.py` for your needs
6. **Add Providers**: Implement new LLM providers in `ansible_maya/core/providers/`

## Troubleshooting

### "Module not found" errors
```bash
pip install -e .
```

### "API key not configured"
```bash
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
# Or add to .env file
```

### "ansible-lint not found"
```bash
pip install ansible-lint
# Or use Docker: docker-compose up
```

### API won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Use different port
ansible-maya serve --port 8080
```

## Getting Help

- **Documentation**: See `README.md` and `docs/`
- **Examples**: Check `examples/` directory
- **API Docs**: http://localhost:8000/docs (when server is running)
- **Issues**: Report bugs at GitHub Issues
- **Contributing**: See `CONTRIBUTING.md`

## Production Deployment

For production deployment:

1. **Use published container images** from Quay.io
   ```bash
   docker pull quay.io/iamgini/ansible-maya:0.2.0
   ```

2. **Configure environment variables**
   - `ANTHROPIC_API_KEY` (required for Claude)
   - `LLM_PROVIDER` (claude, openai, or custom)
   - `MAYA_LOG_LEVEL` (INFO, DEBUG, WARNING)

3. **Enable authentication** on API endpoints (reverse proxy recommended)

4. **Use production-grade LLM settings**
   - Temperature: 0.2 for consistency
   - Rate limiting for cost control

5. **Configure monitoring** with Prometheus/Grafana

6. **Set up log aggregation** (ELK, Loki, etc.)

**Note:** Ansible Maya is **stateless** - no PostgreSQL or Redis required!

See `README.md` and `DOCKER-USAGE.md` for detailed deployment guide.

---

**You're all set!** Start generating intelligent Ansible playbooks from infrastructure events. 🚀
