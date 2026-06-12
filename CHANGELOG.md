# Changelog

All notable changes to Ansible Maya will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Spec-Kit Integration** - Two-phase generation workflow
  - `/api/v1/specs/plan` - Generate execution plan for approval
  - `/api/v1/specs/{id}/generate` - Generate playbook from approved spec
  - Uses cheaper model (Haiku) for specs, full model for playbooks
- **Multi-Agent Review Pipeline** - Optional quality enhancement
  - Security review agent (hardcoded secrets, unsafe commands, permissions)
  - Best practices review agent (FQCN, idempotency, task naming)
  - Auto-refinement based on findings
  - Confidence boost: +5% to +15% based on review scores
  - Enable with `?multi_agent_review=true` query parameter

### Planned
- OpenAI provider (native implementation)
- Ollama (local LLM) provider  
- Molecule testing integration for generated playbooks
- RAG/Knowledge base for learning from past playbooks
- Additional integration tests

## [0.1.0] - 2026-06-12

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
  - Stateless API design (no database required)
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

### Changed
- Updated from alpha to production-stable status
- Enhanced prompt templates with session context
- Improved confidence scoring algorithm
- Optimized Docker image size

### Security
- Non-root container execution
- Input validation with Pydantic schemas
- Audit trail for all generations
- Secure secrets management patterns

### Notes
This is the first public release. The API is functional but may evolve based on user feedback. Contributions and feedback welcome!

[Unreleased]: https://github.com/iamgini/ansible-maya/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/iamgini/ansible-maya/releases/tag/v0.1.0
