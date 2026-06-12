# Copy this for GitHub Release Description

Use this when creating the GitHub Release at:
https://github.com/iamgini/ansible-maya/releases/new?tag=v0.1.0

---

# 🎉 Ansible Maya v0.1.0 - Initial Public Release!

माया (maya) - "creative power" in Sanskrit

This is the **first public release** of Ansible Maya, an AI-powered Ansible playbook generator with validation and best practices.

## ⚠️ Status: v0.x.x - Initial Development

This is a **v0.1.0 release**, which means:
- ✅ Core functionality is working and tested
- ⚠️ API may evolve based on user feedback
- 🔍 Integration tests are limited (basic coverage)
- 🙏 Seeking community feedback and contributions

**Use in production?** Possible, but review generated playbooks carefully. High-confidence (80%+) playbooks are generally safe.

---

## ✨ Features

- 🤖 **AI-Powered Generation**: Leverages LLMs (Claude or custom) to generate production-ready playbooks
- 📝 **Event-Aware**: Generates playbooks based on infrastructure event context
- ✅ **Intelligent Validation**: Automatic ansible-lint checking with auto-fix
- 📊 **Confidence-Based Recommendations**: High/Medium/Low scoring
- 🎯 **Ansible Best Practices**: FQCN-compliant, idempotent playbooks
- 🏗️ **BYOM**: Bring Your Own Model - pluggable LLM providers
- 🔌 **REST API & CLI**: Easy integration
- 🔍 **Session Context**: Multi-turn conversations for refinement

---

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
docker pull ghcr.io/iamgini/ansible-maya:0.1.0

docker run -d -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key-here \
  ghcr.io/iamgini/ansible-maya:0.1.0
```

Access API docs: http://localhost:8000/docs

### Using Docker Compose

```bash
git clone https://github.com/iamgini/ansible-maya.git
cd ansible-maya
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
docker-compose up -d
```

### Generate Your First Playbook

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

---

## 📚 Documentation

- [README](https://github.com/iamgini/ansible-maya#readme) - Full documentation
- [Quick Start Guide](https://github.com/iamgini/ansible-maya/blob/main/QUICKSTART.md) - Get started in 5 minutes
- [Workflow Guide](https://github.com/iamgini/ansible-maya/blob/main/WORKFLOW.md) - Integration patterns
- [Docker Usage](https://github.com/iamgini/ansible-maya/blob/main/DOCKER-USAGE.md) - Deployment guide

---

## 🐳 Docker Images

Multi-architecture images (AMD64 + ARM64):
- `ghcr.io/iamgini/ansible-maya:0.1.0`
- `ghcr.io/iamgini/ansible-maya:0.1`
- `ghcr.io/iamgini/ansible-maya:latest`

---

## 🎯 Use Cases

Perfect for:
- Self-healing infrastructure
- Event-Driven Ansible (EDA) workflows
- Incident response automation
- AIOps integration
- AAP (Ansible Automation Platform) workflows

---

## 🛣️ What's Next? (Roadmap to v1.0.0)

- [ ] Native OpenAI provider implementation
- [ ] Ollama (local LLM) provider
- [ ] Comprehensive integration tests with real LLM providers
- [ ] Molecule testing integration
- [ ] AAP catalog search before generation
- [ ] Community feedback incorporation
- [ ] API stabilization

**Your feedback will shape the roadmap!**

---

## 🙏 Feedback Welcome!

This is an initial release - I'd love your input:

- 🐛 **Found a bug?** [Open an issue](https://github.com/iamgini/ansible-maya/issues)
- 💡 **Have a feature idea?** [Start a discussion](https://github.com/iamgini/ansible-maya/discussions)
- 🤝 **Want to contribute?** [Check CONTRIBUTING.md](https://github.com/iamgini/ansible-maya/blob/main/CONTRIBUTING.md)
- ⭐ **Like it?** Give it a star!

---

## 📊 Full Changelog

See [CHANGELOG.md](https://github.com/iamgini/ansible-maya/blob/main/CHANGELOG.md) for complete details.

### Added - Initial Public Release

- **Core Features**:
  - AI-powered playbook generation using Claude and custom LLM providers
  - Event-driven architecture with intelligent event classification
  - Confidence-based recommendations (High/Medium/Low)
  - Session context management for multi-turn conversations
  - Few-shot learning examples for improved generation quality
  - Temperature tuning for consistency vs creativity

- **Validation & Quality**:
  - ansible-lint integration with auto-fix capabilities
  - YAML syntax validation
  - Security best practices enforcement
  - FQCN (Fully Qualified Collection Names) compliance

- **LLM Providers**:
  - Claude/Anthropic provider (fully implemented)
  - Custom OpenAI-compatible provider support
  - BYOM (Bring Your Own Model) architecture

- **APIs & Interfaces**:
  - FastAPI REST API with OpenAPI documentation
  - CLI interface (`ansible-maya` command)
  - Python SDK for programmatic usage

- **Infrastructure**:
  - Docker containerization with multi-stage builds
  - Docker Compose for local development
  - PostgreSQL for playbook history
  - Redis for caching and deduplication
  - GitHub Actions CI/CD pipeline

- **Documentation**:
  - Comprehensive README with architecture diagrams
  - QUICKSTART guide for 5-minute setup
  - WORKFLOW guide for integration patterns
  - CLAUDE.md for developer guidance
  - CONTRIBUTING guide with code standards
  - Multiple usage examples (CLI, Python, REST API, EDA, AAP)

- **Ansible Best Practices**:
  - Prompt engineering ported from vscode-ansible Lightspeed
  - Multi-task vs single-task detection
  - Context-aware generation (playbook, role, task level)
  - Idempotency enforcement
  - Error handling patterns

### Security
- Non-root container execution
- Input validation with Pydantic schemas
- Audit trail for all generations
- Secure secrets management patterns

### Notes
This is the first public release. The API is functional but may evolve based on user feedback. Contributions and feedback welcome!

---

**Thank you for trying Ansible Maya! 🚀**

Built with ❤️ for the Ansible community.
