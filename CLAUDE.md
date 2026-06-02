# CLAUDE.md

This file provides guidance to Claude Code when working with the Ansible Sage codebase.

## Project Overview

**Ansible Sage** is an AI-powered event-driven playbook generation service for AIOps workflows. It automatically generates, validates, tests, and executes Ansible playbooks in response to infrastructure events.

### Core Components

1. **Event Handler** (`sage/handlers/`) - Receives and classifies infrastructure events
2. **Playbook Generator** (`sage/core/`) - Uses LLMs to generate Ansible playbooks
3. **Validator** (`sage/validation/`) - Lints and tests generated playbooks
4. **LLM Providers** (`sage/core/providers/`) - Pluggable interface for different AI models
5. **API Server** (`sage/api/`) - FastAPI REST interface

### Technology Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **LLM SDKs**: Anthropic (Claude), OpenAI, Ollama
- **Database**: PostgreSQL (for playbook history)
- **Cache/Queue**: Redis
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest, pytest-asyncio
- **Linting**: ruff, mypy, black, isort
- **CI/CD**: GitHub Actions

---

## Code Architecture Patterns

### Ported from vscode-ansible

This project ports key concepts from the `vscode-ansible` TypeScript codebase to Python:

**Critical files ported:**
- `vscode-ansible/src/features/lightspeed/ansibleContext.ts` → `sage/core/ansible_context.py`
- `vscode-ansible/src/features/lightspeed/providers/base.ts` → `sage/core/providers/base.py`
- `vscode-ansible/src/definitions/constants.ts` → `sage/core/prompt_templates.py`

**Key patterns to maintain:**

1. **Ansible Context Processor** - Applies file-type-specific prompt engineering
2. **Provider Abstraction** - BYOM (Bring Your Own Model) pattern
3. **Output Cleaning** - Removes markdown fences, validates YAML
4. **Multi-task Detection** - Identifies single vs multi-task prompts

### File Naming Conventions

- Use `snake_case` for all Python files
- Prefix with domain: `ansible_*.py`, `aap_*.py`, `molecule_*.py`
- Test files mirror source: `test_ansible_context.py` for `ansible_context.py`

### Import Structure

```python
# Standard library
import os
import sys
from typing import Optional, Dict, Any

# Third-party
import yaml
from anthropic import Anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Local - absolute imports
from sage.core.ansible_context import AnsibleContextProcessor
from sage.core.providers.base import BaseLLMProvider
```

---

## Development Guidelines

### Adding a New LLM Provider

1. Create `sage/core/providers/{provider_name}.py`
2. Inherit from `BaseLLMProvider`
3. Implement required abstract methods:
   - `generate_playbook()`
   - `validate_config()`
   - `get_status()`
4. Register in `sage/core/providers/__init__.py`
5. Add configuration schema to `config/providers.yaml`
6. Write tests in `tests/unit/providers/test_{provider_name}.py`

Example:
```python
# sage/core/providers/custom.py
from sage.core.providers.base import BaseLLMProvider

class CustomProvider(BaseLLMProvider):
    name = "custom"
    display_name = "Custom LLM"
    
    async def generate_playbook(self, params: GenerationRequest) -> GenerationResponse:
        # Implementation
        pass
```

### Adding a New Event Type

1. Define pattern in `config/event_patterns.yaml`
2. Add prompt template function in `sage/handlers/event_classifier.py`
3. Add validation rules if needed
4. Write integration test in `tests/integration/test_events.py`

### Running Specific Tests

```bash
# Unit tests for a specific module
pytest tests/unit/core/test_ansible_context.py -v

# Integration tests with real LLM (requires API key)
pytest tests/integration/test_playbook_generation.py --run-integration

# Skip slow tests
pytest -m "not slow"

# Run with coverage
pytest --cov=sage --cov-report=html
```

### Pre-commit Hooks

The project uses pre-commit hooks. Always run before committing:

```bash
pre-commit run --all-files
```

This runs:
- black (formatting)
- isort (import sorting)
- ruff (linting)
- mypy (type checking)
- trailing whitespace removal
- YAML/JSON validation

---

## Common Tasks

### Adding a New Ansible System Prompt

Edit `sage/core/prompt_templates.py`:

```python
ANSIBLE_SYSTEM_PROMPT_CUSTOM = """You are an Ansible expert specializing in {domain}.

Requirements:
- Use FQCN (Fully Qualified Collection Names)
- Follow security best practices
- Include error handling
- Add meaningful task names
"""
```

### Debugging Playbook Generation

Enable debug logging in `.env`:

```bash
SAGE_LOG_LEVEL=DEBUG
SAGE_LOG_LLM_PROMPTS=true
SAGE_LOG_LLM_RESPONSES=true
```

Logs will show:
- Full prompts sent to LLM
- Raw LLM responses
- Ansible context applied
- Validation results

### Testing with Different LLM Models

```bash
# Test with Claude
LLM_PROVIDER=claude pytest tests/integration/

# Test with OpenAI
LLM_PROVIDER=openai pytest tests/integration/

# Test with local Ollama
LLM_PROVIDER=ollama OLLAMA_BASE_URL=http://localhost:11434 pytest tests/integration/
```

---

## Code Quality Standards

### Type Hints

**REQUIRED** for all function signatures:

```python
def generate_playbook(
    event: AIOpsEvent,
    context: Optional[AnsibleContext] = None
) -> PlaybookResponse:
    """Generate Ansible playbook from event.
    
    Args:
        event: Infrastructure event to remediate
        context: Additional Ansible-specific context
        
    Returns:
        Generated playbook with metadata
        
    Raises:
        ValidationError: If event is invalid
        LLMError: If playbook generation fails
    """
    pass
```

### Error Handling

Use custom exceptions defined in `sage/core/exceptions.py`:

```python
from sage.core.exceptions import PlaybookGenerationError, ValidationError

try:
    playbook = await generator.generate(event)
except ValidationError as e:
    logger.warning(f"Invalid event: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except PlaybookGenerationError as e:
    logger.error(f"Generation failed: {e}")
    raise HTTPException(status_code=500, detail="Playbook generation failed")
```

### Async/Await

Use `async`/`await` for all I/O operations:
- LLM API calls
- Database queries
- HTTP requests
- File operations (use `aiofiles`)

```python
async def validate_playbook(content: str) -> ValidationResult:
    """Async validation to not block event loop."""
    async with aiofiles.open("/tmp/playbook.yml", "w") as f:
        await f.write(content)
    
    result = await run_ansible_lint_async(content)
    return result
```

### Logging

Use structured logging:

```python
import logging
from sage.utils.logger import get_logger

logger = get_logger(__name__)

# Good - structured context
logger.info(
    "Playbook generated",
    extra={
        "event_type": event.event_type,
        "host": event.host,
        "playbook_lines": len(playbook.split("\n")),
        "model": response.model
    }
)

# Bad - string concatenation
logger.info(f"Generated playbook for {event.event_type}")
```

---

## Testing Guidelines

### Unit Tests

- Mock all external dependencies (LLM APIs, AAP, etc.)
- Use `pytest.fixture` for common setup
- Aim for 80%+ code coverage
- Test edge cases and error conditions

```python
# tests/unit/core/test_ansible_context.py
import pytest
from sage.core.ansible_context import AnsibleContextProcessor

def test_multi_task_detection():
    """Test detection of multi-task prompts."""
    multi_task_prompt = """
    - name: Install nginx
      package: name=nginx state=present
    - name: Start nginx
      service: name=nginx state=started
    """
    
    assert AnsibleContextProcessor._is_multi_task_prompt(multi_task_prompt)

def test_single_task_detection():
    """Test detection of single-task prompts."""
    single_task = "- name: Install nginx"
    assert not AnsibleContextProcessor._is_multi_task_prompt(single_task)
```

### Integration Tests

- Use real LLM APIs (mark with `@pytest.mark.integration`)
- Can be skipped in CI with `--skip-integration`
- Verify end-to-end flows

```python
# tests/integration/test_playbook_generation.py
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_generation_flow(event_fixture, claude_provider):
    """Test complete playbook generation with real LLM."""
    from sage.handlers.orchestrator import PlaybookOrchestrator
    
    orchestrator = PlaybookOrchestrator(provider=claude_provider)
    result = await orchestrator.handle_event(event_fixture)
    
    assert result["playbook"]
    assert "- name:" in result["playbook"]
    assert result["validation"]["passed"]
```

### Molecule Tests

For critical playbooks, validate with Molecule:

```python
# sage/validation/molecule_runner.py
async def test_generated_playbook(playbook_content: str) -> MoleculeResult:
    """Run Molecule test on generated playbook."""
    # Create temp directory with molecule structure
    # Run molecule test in container
    # Parse results
    pass
```

---

## Docker Development

### Building Locally

```bash
# Build development image
docker build -t ansible-sage:dev .

# Build with build args
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  -t ansible-sage:dev .

# Run locally
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  ansible-sage:dev
```

### Docker Compose Development

```bash
# Start all services
docker-compose up -d

# View logs for specific service
docker-compose logs -f ansible-sage

# Rebuild after code changes
docker-compose up -d --build ansible-sage

# Run tests in container
docker-compose exec ansible-sage pytest

# Shell into container
docker-compose exec ansible-sage bash
```

---

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'sage'`
**Solution**: Install in editable mode: `pip install -e .`

**Issue**: LLM API timeouts
**Solution**: Increase timeout in provider config or use faster model

**Issue**: ansible-lint not found
**Solution**: Ensure ansible-lint is in PATH or use container execution

**Issue**: Molecule tests fail
**Solution**: Check Docker/Podman is running and accessible

### Debug Mode

Run with full debug output:

```bash
SAGE_LOG_LEVEL=DEBUG \
SAGE_LOG_LLM_PROMPTS=true \
SAGE_LOG_LLM_RESPONSES=true \
python -m sage.api.server
```

---

## Performance Considerations

### Caching

Use Redis for:
- Event deduplication (same event within 5 minutes)
- Generated playbook caching (by event hash)
- LLM response caching (for identical prompts)

### Async Processing

For long-running tasks (Molecule tests), use background workers:

```python
from sage.workers.tasks import run_molecule_test

# Enqueue task
task_id = await run_molecule_test.delay(playbook_content)

# Client polls for result
result = await get_task_result(task_id)
```

### Rate Limiting

Implement rate limiting for LLM APIs:

```python
from sage.core.rate_limiter import RateLimiter

limiter = RateLimiter(
    requests_per_minute=50,
    tokens_per_minute=100000
)

await limiter.acquire()
response = await llm_client.generate(...)
```

---

## Security Checklist

- [ ] Never log API keys or secrets
- [ ] Validate all input events (use Pydantic schemas)
- [ ] Sanitize LLM outputs before execution
- [ ] Use RBAC for AAP integration
- [ ] Encrypt sensitive data at rest
- [ ] Use HTTPS for all external APIs
- [ ] Implement authentication for API endpoints
- [ ] Audit all playbook executions

---

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
4. Push tag: `git push origin v1.0.0`
5. GitHub Actions will build and push Docker image
6. Create GitHub release with changelog

---

## Questions?

- Check existing code patterns in `sage/core/`
- Review tests in `tests/` for examples
- See `docs/` for detailed documentation
- Ask in GitHub Discussions for clarification

**Remember**: This is an event-driven system that generates Ansible playbooks using AI. Safety, validation, and best practices are critical. When in doubt, add more validation and logging.
