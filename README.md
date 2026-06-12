# Ansible Maya

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**AI-powered Ansible playbook generator with validation and best practices**

माया (maya) means "creative power" in Sanskrit - perfectly capturing what this tool does: harnessing AI's creative power to generate production-ready Ansible playbooks.

Ansible Maya automatically **generates**, **validates**, and **publishes** Ansible playbooks with built-in linting and testing. Supports multiple LLM providers (Claude, OpenAI, Ollama) and follows Ansible best practices.

---

## ✨ Features

- 🤖 **AI-Powered Generation**: Leverages LLMs (Claude or custom) to generate production-ready playbooks
- 📝 **Event-Aware Generation**: Generates playbooks based on infrastructure event context (disk full, service down, high CPU, etc.)
- ✅ **Intelligent Validation**: Automatic ansible-lint checking with auto-fix capabilities
- 📊 **Confidence-Based Recommendations**: 
  - **High Confidence (≥80%)**: Production-ready for execution
  - **Medium Confidence (50-80%)**: Human review recommended
  - **Low Confidence (<50%)**: Testing required before execution
- 🎯 **Ansible Best Practices**: Built-in prompt engineering for FQCN-compliant, idempotent playbooks
- 🏗️ **BYOM (Bring Your Own Model)**: Pluggable LLM providers - use Claude or custom OpenAI-compatible models
- 🔌 **REST API & CLI**: Easy integration into your existing automation workflows
- 🔍 **Multi-Mode Classification**: Automatically categorizes events as known, complex, or unknown

---

## 🎯 Core Workflow

```
[Your Tool/Playbook] → API Call with Event Context → Classification → Generation (LLM) 
→ Validation (ansible-lint) → Confidence Scoring → Playbook Response
```

**Important**: Ansible Maya is a **playbook generation API**. Your tools call Maya's API with event context, receive generated playbooks, and then decide how to execute them. Maya does NOT:
- Listen to monitoring systems directly
- Execute playbooks
- Store playbooks (unless you implement that)

You integrate Maya into your existing automation pipeline (Event-Driven Ansible, AAP workflows, custom scripts, etc.).

See [WORKFLOW.md](WORKFLOW.md) for detailed workflow documentation.

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- API key for your chosen LLM provider (Claude or custom OpenAI-compatible)

### Run with Docker Compose

```bash
# Clone the repository
git clone https://github.com/iamgini/ansible-maya.git
cd ansible-maya

# Configure environment
cp .env.example .env
# Edit .env and configure:
#   - ANTHROPIC_API_KEY (for Claude)
#   - Or CUSTOM_LLM_ENDPOINT for custom providers

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f ansible-maya
```

The API will be available at `http://localhost:8000`

Access interactive API docs: `http://localhost:8000/docs`

### Generate Your First Playbook

```bash
curl -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "disk_full",
    "description": "Disk usage at 95% on /var partition",
    "host": "web-server-01.example.com",
    "severity": "high",
    "metadata": {
      "partition": "/var",
      "usage_percent": 95
    }
  }'
```

Response includes:
```json
{
  "event_id": "evt-123456",
  "playbook": "--- (playbook YAML content)",
  "confidence_score": 0.85,
  "confidence_level": "high",
  "validation_passed": true,
  "recommended_action": "✓ High confidence (85%). Production ready - safe to execute."
}
```

The generated playbook is returned in the response and can be saved, integrated into your automation pipeline, or executed directly!

---

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────┐
│            Your Event-Driven System                      │
│  (EDA Rulebook, AAP Workflow, Custom Script, etc.)     │
│  • Receives events from monitoring                      │
│  • Calls Maya API with event context                    │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP POST /api/v1/events/generate
                     │
┌────────────────────▼────────────────────────────────────┐
│            Ansible Maya API Service                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Event Classifier                                │  │
│  │  • Known vs Unknown event detection              │  │
│  │  • Automation mode selection                     │  │
│  │  • Confidence calculation                        │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                      │
│  ┌────────────────▼─────────────────────────────────┐  │
│  │  Playbook Generator                              │  │
│  │  • LLM provider (Claude or custom)               │  │
│  │  • Ansible-specific prompt engineering          │  │
│  │  • FQCN enforcement & best practices            │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                      │
│  ┌────────────────▼─────────────────────────────────┐  │
│  │  Validator                                       │  │
│  │  • ansible-lint (with auto-fix)                 │  │
│  │  • YAML syntax validation                       │  │
│  │  • Security checks                              │  │
│  │  • Confidence scoring                           │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                      │
│  ┌────────────────▼─────────────────────────────────┐  │
│  │  Response Builder                                │  │
│  │  • Generated playbook                           │  │
│  │  • Confidence level & score                     │  │
│  │  • Validation results                           │  │
│  │  • Execution recommendation                     │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ Returns JSON with playbook
                     │
┌────────────────────▼────────────────────────────────────┐
│         Your Execution Logic                             │
│  • Save playbook (optional)                             │
│  • Review if needed (medium/low confidence)             │
│  • Execute via ansible-playbook, AAP, etc.              │
│  • You control when/how playbooks execute               │
└──────────────────────────────────────────────────────────┘
```

**Key Point**: Ansible Maya is a **REST API service**, not an event listener. Your automation calls Maya when needed.

---

## 🎛️ Configuration

### Environment Variables

```bash
# LLM Provider Configuration
LLM_PROVIDER=claude                    # claude, custom
ANTHROPIC_API_KEY=sk-ant-...           # For Claude
# For custom OpenAI-compatible providers:
# LLM_PROVIDER=custom
# CUSTOM_API_BASE_URL=http://your-api.com
# CUSTOM_API_KEY=your-key

# Optional: AAP Integration (architecture ready, implementation in progress)
# AAP_URL=https://aap.example.com
# AAP_TOKEN=your-aap-token
# AAP_VERIFY_SSL=true

# Service Configuration
MAYA_LOG_LEVEL=INFO
MAYA_ANSIBLE_LINT_AUTO_FIX=true        # Auto-fix lint issues
```

### Confidence Scoring

Confidence is calculated based on:

| Factor | Impact |
|--------|--------|
| Known event type | +20-30% |
| Validation passed (no errors) | +40% |
| Only warnings (no errors) | +20% |
| Low severity event | +10% |
| Known safe event | +20% |
| Each validation issue | -5% |

### Branch Strategy

| Confidence | Score | Recommendation |
|-----------|-------|----------------|
| High | ≥ 80% | Production-ready, safe to execute |
| Medium | 50-80% | Human review recommended |
| Low | < 50% | Testing required before execution |

---

## 📚 Usage Examples

### Example 1: CLI Usage

```bash
# Generate playbook for disk cleanup
ansible-maya generate \
  --event-type disk_full \
  --description "Disk usage at 95% on /var" \
  --host web-server-01 \
  --severity high \
  --output cleanup.yml

# Validate a playbook
ansible-maya validate cleanup.yml --fix

# List supported event types
ansible-maya list-events

# Start API server
ansible-maya serve --port 8000 --reload
```

### Example 2: Python API

```python
import asyncio
from ansible_maya.core.providers import get_provider
from ansible_maya.handlers.orchestrator import (
    AIOpsEvent, EventSeverity, PlaybookOrchestrator
)
from datetime import datetime

async def generate_playbook():
    # Initialize LLM provider
    provider = get_provider("claude", config={
        "api_key": "sk-ant-your-key"
    })
    
    # Create event
    event = AIOpsEvent(
        event_id="evt-001",
        event_type="disk_full",
        description="Disk usage at 95% on /var partition",
        host="web-server-01.example.com",
        severity=EventSeverity.HIGH,
        timestamp=datetime.now(),
        metadata={"partition": "/var", "usage_percent": 95}
    )
    
    # Generate playbook
    orchestrator = PlaybookOrchestrator(provider=provider)
    response = await orchestrator.handle_event(event)
    
    # Display results
    print(f"Confidence: {response.confidence_score:.0%}")
    print(f"Confidence Level: {response.confidence_level}")
    print(f"Validation: {'Passed' if response.validation_result.passed else 'Failed'}")
    print(f"\nPlaybook:\n{response.playbook}")
    
    return response

# Run
asyncio.run(generate_playbook())
```

### Example 3: REST API Integration

```bash
# 1. Generate playbook
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "service_down",
    "description": "Nginx service stopped",
    "host": "web-server-02",
    "severity": "critical"
  }')

# 2. Extract and display details
EVENT_ID=$(echo $RESPONSE | jq -r '.event_id')
PLAYBOOK=$(echo $RESPONSE | jq -r '.playbook')
CONFIDENCE=$(echo $RESPONSE | jq -r '.confidence_score')
CONFIDENCE_LEVEL=$(echo $RESPONSE | jq -r '.confidence_level')

echo "Event ID: $EVENT_ID"
echo "Confidence: $(echo $CONFIDENCE | jq '. * 100')%"
echo "Level: $CONFIDENCE_LEVEL"
echo "Recommended: $(echo $RESPONSE | jq -r '.recommended_action')"

# 3. Save playbook to file
echo "$PLAYBOOK" > "playbook_${EVENT_ID}.yml"
echo "Playbook saved to playbook_${EVENT_ID}.yml"
```

### Example 4: Integration with AAP

After generating a playbook with Ansible Maya, you can execute it via AAP:

```bash
# 1. Generate playbook via Ansible Maya
# 2. Save playbook to your AAP project repository
# 3. Execute via AAP job template or awx CLI

# Example: Execute via awx CLI
awx job_template launch \
  --name "Execute Generated Playbook" \
  --extra_vars "{\"playbook_content\": \"$(cat playbook.yml)\"}" \
  --inventory Production
```

---

## 🔌 Integration Examples

**Important**: Ansible Maya doesn't listen to monitoring systems directly. Your automation calls Maya's API.

### Event-Driven Ansible (EDA)

Use EDA to receive monitoring events and call Maya's API:

```yaml
# eda-rulebook.yml
- name: Generate playbooks via Maya on alerts
  hosts: all
  sources:
    - ansible.eda.prometheus
      host: 0.0.0.0
      port: 8001
  
  rules:
    - name: Disk space critical - call Maya
      condition: event.alert_name == "DiskSpaceCritical"
      action:
        run_playbook:
          name: call_maya_api.yml
          extra_vars:
            event_type: "disk_full"
            host: "{{ event.instance }}"
            severity: "high"
            description: "{{ event.annotations.description }}"
```

```yaml
# call_maya_api.yml
- name: Call Ansible Maya to generate remediation playbook
  hosts: localhost
  tasks:
    - name: Call Maya API
      uri:
        url: "http://ansible-maya:8000/api/v1/events/generate"
        method: POST
        body_format: json
        body:
          event_type: "{{ event_type }}"
          host: "{{ host }}"
          severity: "{{ severity }}"
          description: "{{ description }}"
      register: maya_response
    
    - name: Save generated playbook
      copy:
        content: "{{ maya_response.json.playbook }}"
        dest: "/tmp/generated-{{ event_type }}.yml"
    
    - name: Execute if high confidence
      when: maya_response.json.confidence_level == "high"
      shell: ansible-playbook /tmp/generated-{{ event_type }}.yml
```

### AAP Workflow Template

Call Maya from an AAP workflow:

```yaml
# AAP Workflow Template
- name: Incident Response via Maya
  workflow_nodes:
    - name: Call Maya API
      unified_job_template: "Call API Job Template"
      extra_data:
        maya_url: "http://ansible-maya:8000/api/v1/events/generate"
        event_data:
          event_type: "{{ event_type }}"
          host: "{{ target_host }}"
          severity: "{{ severity }}"
      
    - name: Review Generated Playbook
      unified_job_template: "Manual Approval"
      when: "{{ confidence_level != 'high' }}"
      
    - name: Execute Remediation
      unified_job_template: "Execute Dynamic Playbook"
      when: approved
```

---

## 🔧 Development

### Local Setup

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run with hot-reload
uvicorn ansible_maya.api.server:app --reload
```

### Project Structure

```
ansible-maya/
├── ansible_maya/               # Main application package
│   ├── core/                   # Core business logic
│   │   ├── ansible_context.py  # Ansible context processing
│   │   ├── session_context.py  # Session management
│   │   ├── providers/          # LLM provider implementations
│   │   │   ├── base.py         # Base provider interface
│   │   │   ├── claude.py       # Claude/Anthropic (implemented)
│   │   │   └── custom.py       # Custom OpenAI-compatible providers
│   │   ├── prompt_templates.py # System prompts
│   │   └── exceptions.py       # Custom exceptions
│   ├── handlers/               # Event handlers
│   │   └── orchestrator.py     # Main orchestration logic
│   ├── validation/             # Validation tools
│   │   └── ansible_lint.py     # ansible-lint integration
│   ├── integrations/           # External integrations (AAP, etc.)
│   ├── api/                    # FastAPI application
│   │   ├── server.py           # Main FastAPI app
│   │   └── routes/
│   │       └── events.py       # Event endpoints
│   ├── workers/                # Background workers
│   ├── utils/                  # Utility functions
│   └── cli.py                  # Command-line interface
├── tests/                      # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── examples/                   # Usage examples
│   ├── basic_usage.py
│   ├── api_usage.sh
│   └── README.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── QUICKSTART.md              # 5-minute quick start
├── WORKFLOW.md                # Detailed workflow documentation
├── CLAUDE.md                  # Developer guidance
├── CONTRIBUTING.md
└── README.md
```

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests (requires API key)
make test-integration

# With coverage
make test-cov

# Specific test
pytest tests/unit/core/test_ansible_context.py -v
```

### Code Quality

```bash
# Format code
make format
# Or: black ansible_maya/ tests/ && isort ansible_maya/ tests/

# Lint
make lint
# Or: ruff check ansible_maya/ tests/ && mypy ansible_maya/

# Run all pre-commit hooks
pre-commit run --all-files
```

---

## 🔒 Security

- **Never commit secrets**: Use environment variables or secret management
- **API key security**: Store LLM API keys securely, rotate regularly
- **Input validation**: All event payloads validated with Pydantic
- **Audit trail**: All generations logged with full metadata
- **Code review**: Medium/low confidence playbooks require human review before execution
- **Validation**: Always validate generated playbooks before execution

For security issues, please report them via [GitHub Security Advisories](https://github.com/iamgini/ansible-maya/security/advisories/new) instead of using the public issue tracker.

---

## 📖 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[WORKFLOW.md](WORKFLOW.md)** - Detailed workflow and integration guide
- **[CLAUDE.md](CLAUDE.md)** - Developer guidance for extending Ansible Maya
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[DOCKER-USAGE.md](DOCKER-USAGE.md)** - Docker deployment and production guide
- **[examples/](examples/)** - Usage examples and templates
- **[ansible-aiops](https://github.com/iamgini/ansible-aiops)** - Complete AIOps integration examples

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make check`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

This product incorporates concepts from [vscode-ansible](https://github.com/ansible/vscode-ansible) (MIT License). See [NOTICE](NOTICE) file for attributions.

---

## 🙏 Acknowledgments

- Ansible community for the incredible ecosystem
- [vscode-ansible](https://github.com/ansible/vscode-ansible) project for Lightspeed prompt engineering patterns
- Anthropic, OpenAI, and Ollama teams for LLM capabilities
- All contributors and supporters

---

## 📞 Support

- 💬 **Discussions**: [GitHub Discussions](https://github.com/iamgini/ansible-maya/discussions)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/iamgini/ansible-maya/issues)
- 📚 **Documentation**: See docs in this repository
- 🌐 **Author**: [@iamgini](https://github.com/iamgini)

---

## 📦 Example Integrations

**[ansible-aiops](https://github.com/iamgini/ansible-aiops)** - Complete AIOps workflow demonstrating Ansible Maya integration with Event-Driven Ansible (EDA), MCP, and AAP. Includes intelligent job template matching, automated playbook generation, and Git integration workflows.

---

## 🎯 Roadmap

### In Progress
- [ ] Integration tests suite expansion
- [ ] AAP catalog search before generation

### Planned Features
- [ ] **Spec-Kit Integration**: Generate execution plan/specification before playbook for review
  - Lightweight mode: Add `execution_plan` field to response showing steps in plain English
  - Full mode: Two-phase generation (spec approval → playbook generation)
  - Conditional: Use spec-driven approach for high-risk/unknown events only
- [ ] OpenAI provider (native implementation)
- [ ] Ollama (local LLM) provider
- [ ] Molecule testing integration for generated playbooks
- [ ] Metrics and observability dashboard
- [ ] Multi-language support for event descriptions
- [ ] Custom prompt template editor UI

### Current Status
- ✅ Claude provider fully implemented
- ✅ Custom OpenAI-compatible provider support
- ✅ Confidence-based recommendations
- ✅ ansible-lint validation with auto-fix
- ✅ Event context classification
- ✅ CLI and REST API
- ✅ Session context management
- 🔄 Comprehensive integration tests
- 🔄 Example integration playbooks

---

**Made with ❤️ by the Ansible Maya team**

**Remember**: Ansible Maya is a **generation API**, not an event listener. Your automation (EDA rulebooks, AAP workflows, custom scripts) calls Maya's API when it detects events. Maya generates playbooks with confidence scoring and validation, then returns them. You control when and how to execute them. This separation ensures safety, flexibility, and integration with your existing workflows.
