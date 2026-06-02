# Ansible Sage 🧙‍♂️

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Self-healing Ansible Generation Engine** - AI-powered playbook generation and GitOps publishing for AIOps workflows.

Ansible Sage automatically **generates**, **validates**, and **publishes** Ansible playbooks to Git repositories in response to infrastructure events. It does **NOT** execute playbooks - execution is handled by your existing automation pipeline (AAP, CI/CD, etc.).

---

## ✨ Features

- 🤖 **AI-Powered Generation**: Leverages LLMs (Claude, GPT-4, Ollama) to generate production-ready playbooks
- 🔄 **Event-Driven Architecture**: Responds to infrastructure events (disk full, service down, high CPU, etc.)
- ✅ **Intelligent Validation**: Automatic ansible-lint checking with auto-fix capabilities
- 📊 **Confidence-Based Publishing**: 
  - **High Confidence (≥80%)**: Push to `main` branch - production-ready
  - **Medium Confidence (50-80%)**: Push to `review` branch - needs human approval
  - **Low Confidence (<50%)**: Push to `draft` branch - experimental/testing required
- 🔌 **GitOps Workflow**: Commits generated playbooks to Git for your pipeline to execute
- 🎯 **Ansible Best Practices**: Built-in prompt engineering for FQCN-compliant, idempotent playbooks
- 🏗️ **BYOM (Bring Your Own Model)**: Pluggable LLM providers - use Claude, OpenAI, Ollama, or custom models
- 🏢 **AAP Integration**: Optional queries to check existing job templates before generation
- 🔍 **Multi-Mode Classification**: Automatically categorizes events as known, complex, or unknown

---

## 🎯 Core Workflow

```
Infrastructure Event → Classification → Generation (LLM) → Validation (ansible-lint) 
→ Confidence Scoring → Git Publishing (branch based on confidence) → [Your Pipeline Executes]
```

**Important**: Ansible Sage is a **generation and publishing service**. It does NOT execute playbooks. After publishing to Git, your existing automation pipeline (AAP, GitLab CI, Jenkins, etc.) handles execution with appropriate controls and approvals.

See [WORKFLOW.md](WORKFLOW.md) for detailed workflow documentation.

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Git repository for storing generated playbooks
- API key for your chosen LLM provider (Claude, OpenAI, etc.)

### Run with Docker Compose

```bash
# Clone the repository
git clone https://github.com/your-org/ansible-sage.git
cd ansible-sage

# Configure environment
cp .env.example .env
# Edit .env and configure:
#   - ANTHROPIC_API_KEY or OPENAI_API_KEY
#   - GIT_REPO_URL (your playbooks repository)
#   - GIT_TOKEN (GitHub/GitLab Personal Access Token)

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f ansible-sage
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
  "target_branch": "main",
  "validation_passed": true,
  "recommended_action": "✓ High confidence (85%). Safe to push to 'main' branch."
}
```

### Publish to Git

```bash
# Automatically publish (if GIT_AUTO_PUBLISH=true in .env)
# OR manually via API:

curl -X POST http://localhost:8000/api/v1/events/publish-to-git \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-123456",
    "playbook": "...(playbook content)...",
    "confidence_score": 0.85,
    "metadata": {"event_type": "disk_full", "host": "web-01"},
    "git_repo_url": "https://github.com/your-org/playbooks.git",
    "git_token": "ghp_YourToken"
  }'
```

The playbook is now committed to your Git repository and ready for your pipeline to execute!

---

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Event Sources                            │
│  (Prometheus, EDA, Nagios, Zabbix, Custom Webhooks)     │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│            Ansible Sage Service                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Event Classifier                                │  │
│  │  • Known vs Unknown event detection              │  │
│  │  • Automation mode selection                     │  │
│  │  • Confidence calculation                        │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                      │
│  ┌────────────────▼─────────────────────────────────┐  │
│  │  Playbook Generator                              │  │
│  │  • LLM provider (Claude/GPT/Ollama)             │  │
│  │  • Ansible-specific prompt engineering          │  │
│  │  • FQCN enforcement & best practices            │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                      │
│  ┌────────────────▼─────────────────────────────────┐  │
│  │  Validator                                       │  │
│  │  • ansible-lint (with auto-fix)                 │  │
│  │  • YAML syntax validation                       │  │
│  │  • Security checks                              │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                      │
│  ┌────────────────▼─────────────────────────────────┐  │
│  │  Git Publisher                                   │  │
│  │  • Confidence-based branch selection            │  │
│  │  • Commit with metadata                         │  │
│  │  • Push to remote repository                    │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Git Repository                              │
│  main/     - High confidence playbooks                   │
│  review/   - Medium confidence (needs approval)          │
│  draft/    - Low confidence (testing required)           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│         Your Execution Pipeline                          │
│  (AAP/AWX, GitLab CI, Jenkins, GitHub Actions, etc.)   │
│  • You control when/how playbooks execute               │
│  • Human approval for medium/low confidence             │
│  • Integration with existing automation                 │
└──────────────────────────────────────────────────────────┘
```

---

## 🎛️ Configuration

### Environment Variables

```bash
# LLM Provider Configuration
LLM_PROVIDER=claude                    # claude, openai, ollama, custom
ANTHROPIC_API_KEY=sk-ant-...           # For Claude
OPENAI_API_KEY=sk-...                  # For OpenAI
OLLAMA_BASE_URL=http://localhost:11434 # For Ollama (local)

# Git Repository Configuration
GIT_REPO_URL=https://github.com/your-org/ansible-playbooks.git
GIT_TOKEN=ghp_YourPersonalAccessToken  # GitHub/GitLab PAT
GIT_MAIN_BRANCH=main                   # High confidence target
GIT_REVIEW_BRANCH=review               # Medium confidence target
GIT_DRAFT_BRANCH=draft                 # Low confidence target
GIT_USERNAME=ansible-sage-bot
GIT_EMAIL=ansible-sage@example.com
GIT_AUTO_PUBLISH=false                 # Auto-push after generation

# Optional: AAP Integration (for querying existing playbooks)
AAP_URL=https://aap.example.com
AAP_TOKEN=your-aap-token
AAP_VERIFY_SSL=true

# Service Configuration
SAGE_LOG_LEVEL=INFO
SAGE_ANSIBLE_LINT_AUTO_FIX=true        # Auto-fix lint issues

# Database (for playbook history)
DATABASE_URL=postgresql://sage:password@postgres:5432/ansible_sage

# Redis (for caching and deduplication)
REDIS_URL=redis://redis:6379/0
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

| Confidence | Score | Branch | Action |
|-----------|-------|--------|--------|
| High | ≥ 80% | `main` | Production-ready, can be auto-deployed |
| Medium | 50-80% | `review` | Requires human review before merge |
| Low | < 50% | `draft` | Experimental, requires testing |

---

## 📚 Usage Examples

### Example 1: CLI Usage

```bash
# Generate playbook for disk cleanup
ansible-sage generate \
  --event-type disk_full \
  --description "Disk usage at 95% on /var" \
  --host web-server-01 \
  --severity high \
  --output cleanup.yml

# Validate a playbook
ansible-sage validate cleanup.yml --fix

# List supported event types
ansible-sage list-events

# Start API server
ansible-sage serve --port 8000 --reload
```

### Example 2: Python API

```python
import asyncio
from sage.core.providers import get_provider
from sage.handlers.orchestrator import (
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
    print(f"Target Branch: {response.target_branch}")
    print(f"Validation: {'Passed' if response.validation_result.passed else 'Failed'}")
    print(f"\nPlaybook:\n{response.playbook}")
    
    return response

# Run
asyncio.run(generate_playbook())
```

### Example 3: REST API with Git Publishing

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

# 2. Extract details
EVENT_ID=$(echo $RESPONSE | jq -r '.event_id')
PLAYBOOK=$(echo $RESPONSE | jq -r '.playbook')
CONFIDENCE=$(echo $RESPONSE | jq -r '.confidence_score')

echo "Confidence: $(echo $CONFIDENCE | jq '. * 100')%"
echo "Recommended: $(echo $RESPONSE | jq -r '.recommended_action')"

# 3. Publish to Git
curl -X POST http://localhost:8000/api/v1/events/publish-to-git \
  -H "Content-Type: application/json" \
  -d "{
    \"event_id\": \"$EVENT_ID\",
    \"playbook\": $(echo \"$PLAYBOOK\" | jq -Rs .),
    \"confidence_score\": $CONFIDENCE,
    \"metadata\": {
      \"event_type\": \"service_down\",
      \"host\": \"web-server-02\"
    },
    \"git_repo_url\": \"https://github.com/your-org/playbooks.git\",
    \"git_token\": \"$GIT_TOKEN\"
  }"
```

### Example 4: Integration with AAP

After Ansible Sage publishes to Git, configure AAP to execute:

```yaml
# AAP Project Configuration
- name: Generated Playbooks
  scm_type: git
  scm_url: https://github.com/your-org/ansible-playbooks.git
  scm_branch: main  # For high-confidence playbooks
  scm_update_on_launch: true

# Job Template
- name: Execute Generated Playbook
  project: Generated Playbooks
  playbook: playbooks/generated/latest.yml
  inventory: Production
  # Add appropriate credentials and limits
```

---

## 🔌 Integrations

### Event-Driven Ansible (EDA)

Forward events from EDA to Ansible Sage:

```yaml
# eda-rulebook.yml
- name: Forward alerts to Ansible Sage
  hosts: all
  sources:
    - ansible.eda.prometheus
      host: 0.0.0.0
      port: 8001
  
  rules:
    - name: Disk space critical
      condition: event.alert_name == "DiskSpaceCritical"
      action:
        post_event:
          post_args:
            url: "http://ansible-sage:8000/api/v1/events/generate"
            headers:
              Content-Type: "application/json"
            body:
              event_type: "disk_full"
              host: "{{ event.instance }}"
              severity: "high"
              description: "{{ event.annotations.description }}"
```

### Prometheus AlertManager

```yaml
# alertmanager.yml
receivers:
  - name: ansible-sage
    webhook_configs:
      - url: 'http://ansible-sage:8000/api/v1/events/prometheus'
        send_resolved: true
```

### GitLab CI/CD Execution

```yaml
# .gitlab-ci.yml in your playbooks repository
stages:
  - validate
  - test
  - deploy

lint:
  stage: validate
  script:
    - ansible-lint playbooks/generated/*.yml

test:
  stage: test
  only:
    - review
    - draft
  script:
    - molecule test

deploy-production:
  stage: deploy
  only:
    - main
  when: manual  # Or automatic based on your risk tolerance
  script:
    - ansible-playbook -i production playbooks/generated/*.yml
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
uvicorn sage.api.server:app --reload
```

### Project Structure

```
ansible-sage/
├── sage/                       # Main application package
│   ├── core/                   # Core business logic
│   │   ├── ansible_context.py  # Ansible context processing
│   │   ├── providers/          # LLM provider implementations
│   │   │   ├── base.py         # Base provider interface
│   │   │   ├── claude.py       # Claude/Anthropic
│   │   │   ├── openai.py       # OpenAI/GPT (to be implemented)
│   │   │   └── ollama.py       # Ollama (to be implemented)
│   │   ├── prompt_templates.py # System prompts
│   │   └── exceptions.py       # Custom exceptions
│   ├── handlers/               # Event handlers
│   │   └── orchestrator.py     # Main orchestration logic
│   ├── validation/             # Validation tools
│   │   ├── ansible_lint.py     # ansible-lint integration
│   │   └── molecule_runner.py  # Molecule testing (future)
│   ├── integrations/           # External integrations
│   │   ├── git_publisher.py    # Git repository publishing
│   │   └── aap_client.py       # AAP integration (future)
│   ├── api/                    # FastAPI application
│   │   ├── server.py           # Main FastAPI app
│   │   └── routes/
│   │       └── events.py       # Event endpoints
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
# Or: black sage/ tests/ && isort sage/ tests/

# Lint
make lint
# Or: ruff check sage/ tests/ && mypy sage/

# Run all pre-commit hooks
pre-commit run --all-files
```

---

## 🔒 Security

- **Never commit secrets**: Use environment variables or secret management
- **Git token security**: Store `GIT_TOKEN` securely, rotate regularly
- **Input validation**: All event payloads validated with Pydantic
- **Audit trail**: All generations logged with full metadata
- **Code review**: Medium/low confidence playbooks require review before merge
- **Branch protection**: Protect `main` branch with required reviews

For security issues, please email security@your-domain.com instead of using the issue tracker.

---

## 📖 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[WORKFLOW.md](WORKFLOW.md)** - Detailed workflow and integration guide
- **[CLAUDE.md](CLAUDE.md)** - Developer guidance for extending Ansible Sage
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[examples/](examples/)** - Usage examples and templates

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

- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-org/ansible-sage/discussions)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/your-org/ansible-sage/issues)
- 📧 **Email**: support@your-domain.com
- 📚 **Documentation**: See docs in this repository

---

## 🎯 Roadmap

- [ ] OpenAI provider implementation
- [ ] Ollama (local LLM) provider
- [ ] Molecule testing integration
- [ ] AAP catalog search before generation
- [ ] Pull request auto-creation for medium/low confidence
- [ ] Metrics and observability dashboard
- [ ] Multi-language support for event descriptions
- [ ] Custom prompt template editor

---

**Made with ❤️ by the Ansible Sage team**

**Remember**: Ansible Sage generates and publishes playbooks to Git. Your existing pipeline (AAP, CI/CD, etc.) handles execution with appropriate controls and approvals. This separation ensures safety, auditability, and integration with your existing workflows.
