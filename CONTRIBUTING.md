# Contributing to Ansible Maya

First off, thank you for considering contributing to Ansible Maya! It's people like you that make Ansible Maya such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

**Bug Report Template:**
```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Send event '...'
2. Check output '....'
3. See error

**Expected behavior**
What you expected to happen.

**Environment:**
 - OS: [e.g. Ubuntu 22.04]
 - Python version: [e.g. 3.11.5]
 - Docker version: [e.g. 24.0.7]
 - LLM Provider: [e.g. Claude, OpenAI]

**Logs**
```
Paste relevant logs here
```

**Additional context**
Add any other context about the problem here.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description** of the suggested enhancement
- **Provide specific examples** to demonstrate the steps
- **Describe the current behavior** and **explain which behavior you expected to see instead**
- **Explain why this enhancement would be useful**

### Pull Requests

1. **Fork the repo** and create your branch from `main`
2. **If you've added code**, add tests
3. **If you've changed APIs**, update the documentation
4. **Ensure the test suite passes**
5. **Make sure your code lints**
6. **Issue that pull request!**

## Development Process

### Setting Up Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ansible-maya.git
cd ansible-maya

# Add upstream remote
git remote add upstream https://github.com/your-org/ansible-maya.git

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Copy environment template
cp .env.example .env
# Edit .env with your settings
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=sage --cov-report=html

# Run specific test file
pytest tests/unit/core/test_ansible_context.py -v

# Run only unit tests (fast)
pytest tests/unit/

# Run integration tests (requires API keys)
pytest tests/integration/ --run-integration

# Skip slow tests
pytest -m "not slow"
```

### Code Style

We use the following tools to maintain code quality:

- **black** - Code formatting
- **isort** - Import sorting
- **ruff** - Linting
- **mypy** - Type checking

Run all checks:
```bash
# Format code
black sage/ tests/
isort sage/ tests/

# Lint
ruff check sage/ tests/

# Type check
mypy sage/

# Or run all via pre-commit
pre-commit run --all-files
```

### Git Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes and commit:**
   ```bash
   git add .
   git commit -m "Add amazing feature"
   ```
   
   **Commit message format:**
   ```
   <type>(<scope>): <subject>
   
   <body>
   
   <footer>
   ```
   
   **Types:**
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation changes
   - `style`: Code style changes (formatting, etc.)
   - `refactor`: Code refactoring
   - `test`: Adding or updating tests
   - `chore`: Maintenance tasks
   
   **Example:**
   ```
   feat(providers): add Ollama provider support
   
   - Implement OllamaProvider class
   - Add configuration schema
   - Write unit tests
   
   Closes #123
   ```

3. **Keep your branch updated:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

4. **Push to your fork:**
   ```bash
   git push origin feature/amazing-feature
   ```

5. **Open a Pull Request** on GitHub

### Pull Request Guidelines

- **Keep it focused** - One feature/fix per PR
- **Write tests** - Ensure your changes are tested
- **Update docs** - If you change APIs or add features
- **Follow style guide** - Run pre-commit hooks
- **Write good commit messages** - See format above
- **Respond to feedback** - Address review comments promptly

## Project Structure

```
ansible-maya/
├── sage/                       # Main application package
│   ├── core/                   # Core business logic
│   │   ├── ansible_context.py  # Ansible-specific prompt engineering
│   │   ├── providers/          # LLM provider implementations
│   │   │   ├── base.py         # Abstract base class
│   │   │   ├── claude.py       # Claude provider
│   │   │   ├── openai.py       # OpenAI provider
│   │   │   └── ollama.py       # Ollama provider
│   │   ├── prompt_templates.py # System prompts
│   │   └── exceptions.py       # Custom exceptions
│   ├── handlers/               # Event handlers
│   │   ├── event_classifier.py # Event classification logic
│   │   └── orchestrator.py     # Main orchestration
│   ├── validation/             # Validation tools
│   │   ├── ansible_lint.py     # ansible-lint wrapper
│   │   ├── molecule_runner.py  # Molecule testing
│   │   └── syntax_checker.py   # YAML validation
│   ├── integrations/           # External integrations
│   │   ├── aap_client.py       # AAP integration
│   │   └── itsm_client.py      # ITSM integration
│   ├── api/                    # FastAPI application
│   │   ├── server.py           # Main app
│   │   ├── routes/             # API routes
│   │   └── schemas.py          # Pydantic models
│   └── utils/                  # Utilities
│       ├── logger.py           # Logging setup
│       └── config.py           # Configuration
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test fixtures
└── docs/                       # Documentation
```

## Adding a New Feature

### Example: Adding a New LLM Provider

1. **Create provider file:**
   ```bash
   touch sage/core/providers/newprovider.py
   ```

2. **Implement provider class:**
   ```python
   from ansible_maya.core.providers.base import BaseLLMProvider
   from ansible_maya.core.schemas import GenerationRequest, GenerationResponse
   
   class NewProvider(BaseLLMProvider):
       name = "newprovider"
       display_name = "New Provider"
       
       async def generate_playbook(
           self, 
           params: GenerationRequest
       ) -> GenerationResponse:
           # Implementation
           pass
       
       async def validate_config(self) -> bool:
           # Validation logic
           pass
       
       async def get_status(self) -> ProviderStatus:
           # Status check
           pass
   ```

3. **Register provider:**
   ```python
   # sage/core/providers/__init__.py
   from ansible_maya.core.providers.newprovider import NewProvider
   
   PROVIDERS = {
       "claude": ClaudeProvider,
       "openai": OpenAIProvider,
       "ollama": OllamaProvider,
       "newprovider": NewProvider,  # Add here
   }
   ```

4. **Add configuration:**
   ```yaml
   # config/providers.yaml
   providers:
     newprovider:
       api_key_env: NEWPROVIDER_API_KEY
       model: default-model
       timeout: 60
   ```

5. **Write tests:**
   ```python
   # tests/unit/providers/test_newprovider.py
   import pytest
   from ansible_maya.core.providers.newprovider import NewProvider
   
   @pytest.mark.asyncio
   async def test_newprovider_generation():
       provider = NewProvider(config={...})
       result = await provider.generate_playbook(...)
       assert result.content
   ```

6. **Update documentation:**
   ```markdown
   # docs/providers.md
   
   ## New Provider
   
   Configuration:
   ```yaml
   LLM_PROVIDER=newprovider
   NEWPROVIDER_API_KEY=your-key
   ```
   ```

## Testing Guidelines

### Writing Tests

- **Test one thing** - Each test should verify one behavior
- **Use fixtures** - Share common setup via pytest fixtures
- **Mock external calls** - Don't call real APIs in unit tests
- **Test edge cases** - Include error conditions and boundary cases
- **Name tests clearly** - `test_<function>_<scenario>_<expected_result>`

**Example:**
```python
import pytest
from unittest.mock import Mock, patch
from ansible_maya.core.ansible_context import AnsibleContextProcessor

class TestAnsibleContextProcessor:
    def test_is_multi_task_prompt_with_multiple_tasks(self):
        """Should detect multiple tasks in prompt."""
        prompt = """
        - name: Task 1
          debug: msg="test"
        - name: Task 2
          debug: msg="test2"
        """
        assert AnsibleContextProcessor._is_multi_task_prompt(prompt)
    
    def test_is_multi_task_prompt_with_single_task(self):
        """Should not detect single task as multi-task."""
        prompt = "- name: Single task"
        assert not AnsibleContextProcessor._is_multi_task_prompt(prompt)
    
    @patch('yaml.safe_load')
    def test_preprocess_ansible_content_handles_invalid_yaml(self, mock_yaml):
        """Should return original content if YAML is invalid."""
        mock_yaml.side_effect = yaml.YAMLError()
        result = AnsibleContextProcessor._preprocess_ansible_content("invalid")
        assert result == "invalid"
```

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_something():
    pass

@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_integration():
    pass

@pytest.mark.slow
def test_molecule():
    pass
```

Run specific categories:
```bash
pytest -m unit          # Only unit tests
pytest -m integration   # Only integration tests
pytest -m "not slow"    # Skip slow tests
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def generate_playbook(
    event: AIOpsEvent,
    context: Optional[AnsibleContext] = None
) -> PlaybookResponse:
    """Generate Ansible playbook from infrastructure event.
    
    This function takes an AIOps event and generates a remediation
    playbook using the configured LLM provider. The playbook follows
    Ansible best practices and is automatically validated.
    
    Args:
        event: Infrastructure event containing host, type, and details
        context: Optional Ansible-specific context for generation
        
    Returns:
        PlaybookResponse containing generated playbook and metadata
        
    Raises:
        ValidationError: If event validation fails
        PlaybookGenerationError: If LLM generation fails
        
    Example:
        >>> event = AIOpsEvent(
        ...     event_type="disk_full",
        ...     host="web01.example.com",
        ...     severity="warning"
        ... )
        >>> response = generate_playbook(event)
        >>> print(response.playbook)
    """
    pass
```

### Updating Documentation

When adding features:

1. Update relevant files in `docs/`
2. Add examples to README.md if user-facing
3. Update API documentation if changing endpoints
4. Add entry to CHANGELOG.md (unreleased section)

## Release Process

Maintainers will handle releases, but here's the process:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Create git tag: `git tag -a v1.2.3 -m "Release v1.2.3"`
4. Push tag: `git push origin v1.2.3`
5. GitHub Actions builds and publishes Docker image
6. Create GitHub Release with changelog

## Questions?

- **General questions**: Open a [GitHub Discussion](https://github.com/your-org/ansible-maya/discussions)
- **Bug reports**: Open an [Issue](https://github.com/your-org/ansible-maya/issues)
- **Feature requests**: Open an [Issue](https://github.com/your-org/ansible-maya/issues) with `enhancement` label
- **Security issues**: Email security@your-domain.com (do NOT open public issue)

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

**Thank you for contributing to Ansible Maya!** 🙏
