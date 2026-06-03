# Ansible Maya Examples

This directory contains examples demonstrating how to use Ansible Maya for event-driven playbook generation.

## Prerequisites

1. **Install Ansible Maya**:
   ```bash
   cd /path/to/ansible-maya
   pip install -e .
   ```

2. **Configure API Key**:
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```

3. **Optional: Start API Server** (for API examples):
   ```bash
   make run
   # Or: uvicorn sage.api.server:app --reload
   ```

## Examples

### 1. Basic Programmatic Usage

**File**: `basic_usage.py`

Demonstrates the core Python API:
- Creating an infrastructure event
- Generating a playbook using LLM
- Validating with ansible-lint
- Displaying results

**Run**:
```bash
python examples/basic_usage.py
```

**Output**: Generates a playbook and saves it to `generated_playbook_example-001.yml`

### 2. REST API Usage

**File**: `api_usage.sh`

Demonstrates the REST API endpoints:
- Health checks
- Listing supported event types
- Single event generation
- Batch event processing

**Run**:
```bash
# Start API server first
make run

# In another terminal:
./examples/api_usage.sh
```

**Requirements**: `curl`, `jq`

## Quick Start Examples

### CLI Usage

Generate a playbook for a disk full event:

```bash
ansible-maya generate \
  --event-type disk_full \
  --description "Disk usage at 95% on /var" \
  --host web-server-01 \
  --severity high \
  --output playbook.yml
```

Validate an existing playbook:

```bash
ansible-maya validate playbook.yml --fix
```

List supported event types:

```bash
ansible-maya list-events
```

Start the API server:

```bash
ansible-maya serve --host 0.0.0.0 --port 8000 --reload
```

### Python API

```python
import asyncio
from ansible_maya.core.providers import get_provider
from ansible_maya.handlers.orchestrator import handle_infrastructure_event, EventSeverity

async def main():
    # Get LLM provider
    provider = get_provider("claude", config={"api_key": "sk-ant-..."})
    
    # Handle event
    response = await handle_infrastructure_event(
        event_description="Disk usage at 95% on /var partition",
        event_type="disk_full",
        host="web-server-01",
        provider=provider,
        severity=EventSeverity.HIGH,
    )
    
    # Use the generated playbook
    print(response.playbook)
    print(f"Validation: {'Passed' if response.validation_result.passed else 'Failed'}")
    print(f"Recommendation: {response.recommended_action}")

asyncio.run(main())
```

### REST API (curl)

Generate playbook:

```bash
curl -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "disk_full",
    "description": "Disk usage at 95% on /var",
    "host": "web-server-01",
    "severity": "high"
  }'
```

## Example Event Types

### Known Safe Events (Auto Mode)

- `disk_cleanup_tmp` - Clean temporary files
- `service_restart_nginx` - Restart nginx service
- `package_cache_clear` - Clear package manager cache
- `log_rotation` - Rotate log files

### Approval Required Events

- `disk_full` - Disk space critical
- `service_down` - Service not running
- `high_cpu` - High CPU usage
- `high_memory` - High memory usage

### Example Metadata

**Disk Full Event**:
```json
{
  "partition": "/var",
  "usage_percent": 95,
  "available_mb": 500
}
```

**Service Down Event**:
```json
{
  "service": "nginx",
  "port": 80,
  "status": "inactive"
}
```

**High CPU Event**:
```json
{
  "cpu_percent": 92,
  "duration": "5m",
  "top_process": "java"
}
```

## Output Files

Examples will generate files in the current directory:

- `generated_playbook_*.yml` - Generated Ansible playbooks
- `generated_evt-*.yml` - Event-specific playbooks

## Troubleshooting

**Error: `ANTHROPIC_API_KEY not set`**

Set your API key:
```bash
export ANTHROPIC_API_KEY='sk-ant-your-key'
```

**Error: `ansible-lint not found`**

Install ansible-lint:
```bash
pip install ansible-lint
```

**Error: API connection refused**

Start the API server:
```bash
make run
# Or: uvicorn sage.api.server:app
```

**Error: Module not found**

Install Ansible Maya:
```bash
pip install -e .
```

## Next Steps

1. Review the generated playbooks
2. Customize event types in `sage/handlers/orchestrator.py`
3. Add custom prompt templates in `sage/core/prompt_templates.py`
4. Integrate with your monitoring system (Prometheus, EDA, etc.)
5. Deploy as a containerized service with `docker-compose up`

## Additional Resources

- **Documentation**: See `../docs/`
- **API Docs**: http://localhost:8000/docs (when server is running)
- **Tests**: See `../tests/` for more examples
- **CLAUDE.md**: Developer guidance for extending the system
