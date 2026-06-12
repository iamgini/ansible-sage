# Multi-Agent Review Example

## Standard Generation
```bash
curl -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "service_down",
    "description": "Nginx service stopped unexpectedly",
    "host": "web-server-01",
    "severity": "critical"
  }'
```

**Response:**
```json
{
  "playbook": "...",
  "confidence_score": 0.75
}
```

## With Multi-Agent Review (Higher Quality)
```bash
curl -X POST "http://localhost:8000/api/v1/events/generate?multi_agent_review=true" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "service_down",
    "description": "Nginx service stopped unexpectedly",
    "host": "web-server-01",
    "severity": "critical"
  }'
```

**Response:**
```json
{
  "playbook": "... (refined playbook)",
  "confidence_score": 0.85,
  "generation_metadata": {
    "multi_agent_review": {
      "security": {
        "agent": "security_reviewer",
        "findings": [],
        "overall_score": 95
      },
      "best_practices": {
        "agent": "best_practices_reviewer", 
        "findings": [
          {
            "category": "best-practices",
            "severity": "medium",
            "issue": "Using command module instead of systemd",
            "suggestion": "Use ansible.builtin.systemd module for service management"
          }
        ],
        "overall_score": 85
      }
    },
    "confidence_boost": 10
  }
}
```

## How It Works

1. **Draft Generation** - Initial playbook created
2. **Security Review** - Agent scans for security issues
3. **Best Practices Review** - Agent checks Ansible conventions  
4. **Auto-Refinement** - Playbook improved based on findings
5. **Return** - Refined playbook with +10% confidence

**Trade-off:** Slower (2-3x) but higher quality output.
