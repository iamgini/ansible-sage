# Changelog

All notable changes to Ansible Maya will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Core playbook generation engine
- LLM provider abstraction (Claude, OpenAI, Ollama)
- Event-driven architecture
- Ansible-specific prompt engineering (ported from vscode-ansible)
- ansible-lint integration with auto-fix
- Molecule testing support
- AAP (Ansible Automation Platform) integration
- FastAPI REST API
- Docker containerization
- PostgreSQL database for playbook history
- Redis for caching and job queue
- Comprehensive documentation
- CI/CD with GitHub Actions

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [0.1.0] - 2026-06-02

### Added
- Initial release
- Basic playbook generation from events
- Multi-provider LLM support
- Docker Compose setup
- Documentation and examples

[Unreleased]: https://github.com/your-org/ansible-maya/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/ansible-maya/releases/tag/v0.1.0
