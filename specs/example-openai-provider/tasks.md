# Tasks: OpenAI Provider Support

**Based on**: [plan.md](./plan.md)  
**Total Estimated Time**: 8 hours  
**Status**: Example (Ready to implement)  

---

## Task 1: Setup Dependencies ⚙️

**Priority**: P0 (Blocker for all other tasks)  
**Estimated Time**: 15 minutes  
**Dependencies**: None  

### Checklist

- [ ] Add `openai>=1.0.0` to `requirements.txt`
- [ ] Run `pip install openai` locally
- [ ] Verify import works: `python -c "from openai import AsyncOpenAI"`
- [ ] Update Docker image requirements if needed

### Files Changed
- `requirements.txt` (1 line added)

### Verification
```bash
pip install openai
python -c "from openai import AsyncOpenAI; print('✓ OpenAI SDK installed')"
```

---

## Task 2: Create OpenAIProvider Class Structure 🏗️

**Priority**: P0  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 1  

### Checklist

- [ ] Create `sage/core/providers/openai.py`
- [ ] Add copyright header
- [ ] Import required dependencies (AsyncOpenAI, exceptions, base classes)
- [ ] Define `OpenAIProvider` class inheriting from `BaseLLMProvider`
- [ ] Add class docstring
- [ ] Define class attributes (name, display_name, MODEL_MAPPING)
- [ ] Implement `__init__()` method with AsyncOpenAI client initialization

### Code Structure

```python
from openai import AsyncOpenAI, APIError, RateLimitError
from sage.core.providers.base import BaseLLMProvider, ...

class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider for Ansible playbook generation."""
    
    name = "openai"
    display_name = "OpenAI GPT"
    requires_api_key = True
    
    MODEL_MAPPING = {
        ModelTier.FAST: "gpt-3.5-turbo",
        ModelTier.BALANCED: "gpt-4o",
        ModelTier.PREMIUM: "gpt-4-turbo",
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Initialize AsyncOpenAI client
        ...
```

### Files Changed
- `sage/core/providers/openai.py` (created, ~40 lines)

### Verification
```python
from sage.core.providers.openai import OpenAIProvider
provider = OpenAIProvider(config={"api_key": "sk-test"})
assert provider.name == "openai"
print("✓ Class structure created")
```

---

## Task 3: Implement validate_config() 🔒

**Priority**: P0  
**Estimated Time**: 20 minutes  
**Dependencies**: Task 2  

### Checklist

- [ ] Implement `validate_config()` method
- [ ] Check for API key in config or environment
- [ ] Validate API key format (starts with "sk-")
- [ ] Raise `ValueError` with helpful message if invalid
- [ ] Add docstring

### Implementation

```python
def validate_config(self) -> None:
    """Validate OpenAI provider configuration.
    
    Raises:
        ValueError: If configuration is invalid
    """
    api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key is required. Set OPENAI_API_KEY environment "
            "variable or provide 'api_key' in config."
        )
    
    if not api_key.startswith("sk-"):
        raise ValueError("Invalid OpenAI API key format. Should start with 'sk-'")
```

### Files Changed
- `sage/core/providers/openai.py` (update, +15 lines)

### Verification
```python
# Should pass
provider = OpenAIProvider(config={"api_key": "sk-valid"})

# Should fail
try:
    provider = OpenAIProvider(config={"api_key": "invalid"})
    assert False, "Should have raised ValueError"
except ValueError as e:
    assert "format" in str(e).lower()
    print("✓ Validation works")
```

---

## Task 4: Implement get_status() 📡

**Priority**: P1  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 3  

### Checklist

- [ ] Implement async `get_status()` method
- [ ] Make minimal API call (ping message with max 5 tokens)
- [ ] Return `ProviderStatus(available=True)` on success
- [ ] Catch `RateLimitError` → return unavailable with error message
- [ ] Catch `APIError` → return unavailable with error message
- [ ] Catch generic exceptions → return unavailable
- [ ] Add docstring

### Implementation

```python
async def get_status(self) -> ProviderStatus:
    """Check OpenAI API availability.
    
    Returns:
        ProviderStatus with availability information
    """
    try:
        response = await self.client.chat.completions.create(
            model=self.default_model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        
        return ProviderStatus(
            available=True,
            model=self.default_model,
        )
    except RateLimitError as e:
        return ProviderStatus(available=False, error=f"Rate limited: {str(e)}")
    except APIError as e:
        return ProviderStatus(available=False, error=f"API error: {str(e)}")
    except Exception as e:
        return ProviderStatus(available=False, error=f"Unexpected error: {str(e)}")
```

### Files Changed
- `sage/core/providers/openai.py` (update, +25 lines)

### Verification
```python
# Requires real API key for full test
# Mock test:
with mock.patch.object(provider.client.chat.completions, 'create'):
    status = await provider.get_status()
    assert status.available == True
print("✓ Status check implemented")
```

---

## Task 5: Implement generate_playbook() - Part 1 (Prompts) 📝

**Priority**: P0  
**Estimated Time**: 45 minutes  
**Dependencies**: Task 4  

### Checklist

- [ ] Implement `generate_playbook(request: GenerationRequest)` signature
- [ ] Import prompt functions from `sage.core.prompt_templates`
- [ ] Select model based on `request.model_tier`
- [ ] Build system prompt using `get_system_prompt()`
- [ ] Build user prompt using `get_event_prompt()` or description
- [ ] Add existing playbooks context if provided
- [ ] Add inventory context if provided
- [ ] Add timing (start_time)

### Implementation

```python
async def generate_playbook(
    self, request: GenerationRequest
) -> GenerationResponse:
    """Generate Ansible playbook using OpenAI.
    
    Args:
        request: Generation parameters
        
    Returns:
        Generated playbook and metadata
    """
    start_time = time.time()
    
    # Select model
    model = self.MODEL_MAPPING.get(request.model_tier, self.default_model)
    
    # Build prompts
    from sage.core.prompt_templates import get_system_prompt, get_event_prompt
    
    system_prompt = get_system_prompt()
    
    if request.event_type:
        user_prompt = get_event_prompt(
            event_type=request.event_type,
            host=request.host or "target_host",
            **{k: v for k, v in (request.constraints or {}).items()},
        )
    else:
        user_prompt = request.event_description
    
    # Add context
    if request.existing_playbooks:
        user_prompt += "\n\n## Existing Playbooks for Reference\n"
        for idx, pb in enumerate(request.existing_playbooks, 1):
            user_prompt += f"\n### Playbook {idx}\n```yaml\n{pb}\n```\n"
    
    if request.inventory_context:
        user_prompt += f"\n\n## Inventory Context\n{request.inventory_context}\n"
    
    # Continue in Part 2...
```

### Files Changed
- `sage/core/providers/openai.py` (update, +40 lines)

### Verification
```python
request = GenerationRequest(
    event_description="Test",
    event_type="disk_full",
    host="test-01",
)
# Verify prompts build without errors
print("✓ Prompt building implemented")
```

---

## Task 6: Implement generate_playbook() - Part 2 (API Call) 🚀

**Priority**: P0  
**Estimated Time**: 45 minutes  
**Dependencies**: Task 5  

### Checklist

- [ ] Call `self.client.chat.completions.create()` with messages
- [ ] Pass temperature and max_tokens from request
- [ ] Extract playbook from `completion.choices[0].message.content`
- [ ] Call `self.clean_output()` to remove markdown fences
- [ ] Call `self.enforce_best_practices()` for FQCN
- [ ] Calculate latency
- [ ] Extract token usage from completion
- [ ] Build and return `GenerationResponse`

### Implementation

```python
    # ... continued from Task 5
    
    try:
        completion = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        # Extract and clean playbook
        raw_playbook = completion.choices[0].message.content
        cleaned_playbook = self.clean_output(raw_playbook)
        final_playbook = self.enforce_best_practices(cleaned_playbook)
        
        # Metadata
        latency_ms = int((time.time() - start_time) * 1000)
        
        return GenerationResponse(
            playbook=final_playbook,
            model=model,
            provider=self.name,
            tokens_used=completion.usage.total_tokens,
            latency_ms=latency_ms,
            metadata={
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
                "finish_reason": completion.choices[0].finish_reason,
                "model_version": completion.model,
            },
        )
    
    except RateLimitError as e:
        raise Exception(f"OpenAI rate limit exceeded: {str(e)}")
    except APIError as e:
        raise Exception(f"OpenAI API error: {str(e)}")
    except Exception as e:
        raise Exception(f"Playbook generation failed: {str(e)}")
```

### Files Changed
- `sage/core/providers/openai.py` (update, +45 lines)

### Verification
```python
# Mock test
mock_completion = Mock(
    choices=[Mock(message=Mock(content="---\n- name: Test"))],
    usage=Mock(total_tokens=100, prompt_tokens=60, completion_tokens=40),
    model="gpt-4o",
)

with patch.object(provider.client.chat.completions, 'create', return_value=mock_completion):
    response = await provider.generate_playbook(request)
    assert response.tokens_used == 100
print("✓ API call implemented")
```

---

## Task 7: Register Provider 🔌

**Priority**: P0  
**Estimated Time**: 10 minutes  
**Dependencies**: Task 6  

### Checklist

- [ ] Open `sage/core/providers/__init__.py`
- [ ] Import `OpenAIProvider` at top
- [ ] Add `"openai": OpenAIProvider` to `PROVIDERS` dict
- [ ] Add `"gpt": OpenAIProvider` alias
- [ ] Add to `__all__` list if present

### Implementation

```python
# sage/core/providers/__init__.py
from sage.core.providers.openai import OpenAIProvider  # Add this

PROVIDERS = {
    "claude": ClaudeProvider,
    "anthropic": ClaudeProvider,
    "openai": OpenAIProvider,  # Add this
    "gpt": OpenAIProvider,      # Add this (alias)
}
```

### Files Changed
- `sage/core/providers/__init__.py` (update, +3 lines)

### Verification
```python
from sage.core.providers import get_provider

provider = get_provider("openai", config={"api_key": "sk-test"})
assert provider.name == "openai"

provider2 = get_provider("gpt", config={"api_key": "sk-test"})
assert provider2.name == "openai"  # Same class
print("✓ Provider registered")
```

---

## Task 8: Update Environment Configuration 📝

**Priority**: P1  
**Estimated Time**: 15 minutes  
**Dependencies**: None (can be parallel)  

### Checklist

- [ ] Open `.env.example`
- [ ] Add OpenAI configuration section after Claude section
- [ ] Document all OpenAI environment variables
- [ ] Add comments explaining optional variables
- [ ] Add example values

### Content to Add

```bash
# OpenAI (GPT-4, GPT-3.5)
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o                    # Optional: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
OPENAI_ORG_ID=org-your-org-id          # Optional: organization ID
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional: custom endpoint
```

### Files Changed
- `.env.example` (update, +5 lines)

### Verification
```bash
grep -A 5 "OpenAI" .env.example
# Should show the new section
```

---

## Task 9: Write Unit Tests 🧪

**Priority**: P0  
**Estimated Time**: 90 minutes  
**Dependencies**: Tasks 2-6  

### Checklist

- [ ] Create `tests/unit/providers/test_openai.py`
- [ ] Add pytest fixtures (openai_provider, mock_completion)
- [ ] Test 1: Provider initialization
- [ ] Test 2: Missing API key raises ValueError
- [ ] Test 3: Invalid API key format raises ValueError
- [ ] Test 4: Model tier mapping correct
- [ ] Test 5: Successful playbook generation (mocked)
- [ ] Test 6: Token usage extraction correct
- [ ] Test 7: Rate limit error handling
- [ ] Test 8: API error handling
- [ ] Test 9: Network error handling
- [ ] Test 10: Output cleaning works
- [ ] Aim for 80%+ coverage

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from sage.core.providers.openai import OpenAIProvider
from sage.core.providers.base import GenerationRequest, ModelTier

@pytest.fixture
def openai_provider():
    return OpenAIProvider(config={"api_key": "sk-test"})

@pytest.fixture
def mock_completion():
    return Mock(
        choices=[Mock(message=Mock(content="---\n- name: Test"))],
        usage=Mock(total_tokens=100, prompt_tokens=60, completion_tokens=40),
        model="gpt-4o",
    )

class TestOpenAIProvider:
    def test_initialization(self):
        """Test provider initializes correctly."""
        ...
    
    def test_missing_api_key(self):
        """Test missing API key raises error."""
        ...
    
    @pytest.mark.asyncio
    async def test_generate_playbook_success(self, openai_provider, mock_completion):
        """Test successful generation."""
        ...
    
    # ... more tests
```

### Files Changed
- `tests/unit/providers/test_openai.py` (created, ~150 lines)

### Verification
```bash
pytest tests/unit/providers/test_openai.py -v
# All tests should pass
```

---

## Task 10: Write Integration Test 🔬

**Priority**: P1  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 6  

### Checklist

- [ ] Create `tests/integration/test_openai_integration.py`
- [ ] Mark test with `@pytest.mark.integration`
- [ ] Skip if `OPENAI_API_KEY` not set
- [ ] Test full workflow with real OpenAI API
- [ ] Use `ModelTier.FAST` (GPT-3.5) to save costs
- [ ] Verify playbook structure, FQCN, token usage
- [ ] Print generated playbook for manual review

### Implementation

```python
import os
import pytest
from sage.core.providers import get_provider
from sage.core.providers.base import GenerationRequest, ModelTier

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)
@pytest.mark.asyncio
async def test_openai_provider_integration():
    """Test OpenAI provider with real API."""
    provider = get_provider("openai", config={
        "api_key": os.getenv("OPENAI_API_KEY")
    })
    
    request = GenerationRequest(
        event_description="Clean up disk space on /tmp",
        event_type="disk_full",
        host="test-server",
        model_tier=ModelTier.FAST,  # Use cheap model
    )
    
    response = await provider.generate_playbook(request)
    
    assert response.playbook
    assert "---" in response.playbook
    assert "ansible.builtin" in response.playbook
    assert response.tokens_used > 0
    
    print(f"\n{'='*70}")
    print(f"Generated with {response.model} ({response.tokens_used} tokens)")
    print(f"{'='*70}")
    print(response.playbook)
```

### Files Changed
- `tests/integration/test_openai_integration.py` (created, ~50 lines)

### Verification
```bash
export OPENAI_API_KEY="sk-..."
pytest tests/integration/test_openai_integration.py -v -s
# Should generate real playbook and print it
```

---

## Task 11: Create Usage Example 📚

**Priority**: P1  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 7  

### Checklist

- [ ] Create `examples/openai_provider.py`
- [ ] Add shebang and docstring
- [ ] Show provider initialization
- [ ] Show status check
- [ ] Show event creation
- [ ] Show playbook generation
- [ ] Display results (confidence, tokens, validation)
- [ ] Make file executable (`chmod +x`)

### Structure

```python
#!/usr/bin/env python3
"""Example: Using OpenAI Provider for Playbook Generation."""

import asyncio
import os
from sage.core.providers import get_provider
from sage.handlers.orchestrator import AIOpsEvent, PlaybookOrchestrator

async def main():
    # 1. Configure provider
    # 2. Check status
    # 3. Create event
    # 4. Generate playbook
    # 5. Display results
    ...

if __name__ == "__main__":
    asyncio.run(main())
```

### Files Changed
- `examples/openai_provider.py` (created, ~80 lines)

### Verification
```bash
chmod +x examples/openai_provider.py
export OPENAI_API_KEY="sk-..."
python examples/openai_provider.py
# Should run successfully and print playbook
```

---

## Task 12: Update Documentation 📖

**Priority**: P0  
**Estimated Time**: 45 minutes  
**Dependencies**: All previous tasks  

### Checklist

#### README.md
- [ ] Add OpenAI to "Features" section
- [ ] Update configuration example with OpenAI
- [ ] Add OpenAI to supported providers list
- [ ] Update quick start example to show provider choice

#### QUICKSTART.md
- [ ] Add OpenAI configuration instructions
- [ ] Show how to switch providers

#### CLAUDE.md
- [ ] Add note about OpenAI provider in provider section
- [ ] Reference as example for adding new providers

#### CHANGELOG.md
- [ ] Add entry under [Unreleased]
- [ ] List: "Added OpenAI GPT-4 and GPT-3.5 provider support"

### README.md Changes

Add to configuration section:
```markdown
### LLM Provider Configuration

Choose your LLM provider:

```bash
# Claude (Anthropic) - Default
export LLM_PROVIDER=claude
export ANTHROPIC_API_KEY=sk-ant-your-key

# OpenAI (GPT-4)
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-proj-your-key
export OPENAI_MODEL=gpt-4o  # Optional

# Ollama (Local) - Coming soon
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
```

**Supported Models**:
- **Claude**: claude-3-5-sonnet, claude-3-opus, claude-3-haiku
- **OpenAI**: gpt-4o (default), gpt-4-turbo, gpt-3.5-turbo
```

### Files Changed
- `README.md` (update, +20 lines)
- `QUICKSTART.md` (update, +10 lines)
- `CLAUDE.md` (update, +5 lines)
- `CHANGELOG.md` (update, +3 lines)

### Verification
```bash
# Check all docs mention OpenAI
grep -r "OpenAI" README.md QUICKSTART.md CLAUDE.md CHANGELOG.md
```

---

## Summary

### Task Dependencies (Critical Path)

```
1 → 2 → 3 → 4 → 5 → 6 → 7 → 9 → 12
        ↓         ↓     ↓
        8        10    11
```

### Time Breakdown

| Phase | Tasks | Time |
|-------|-------|------|
| Setup & Structure | 1-3 | 1h 05m |
| Core Implementation | 4-6 | 2h 00m |
| Integration | 7-8 | 25m |
| Testing | 9-10 | 2h 00m |
| Examples & Docs | 11-12 | 1h 15m |
| **Total** | **12** | **6h 45m** |

(Buffer: +1h 15m for debugging/refinement = 8 hours total)

### Completion Checklist

Mark complete when:
- [ ] All 12 tasks completed
- [ ] All tests passing (`pytest tests/unit/providers/test_openai.py`)
- [ ] Integration test passes with real API
- [ ] Example script runs successfully
- [ ] Documentation updated
- [ ] Code coverage ≥80%
- [ ] No linting errors (`ruff check sage/core/providers/openai.py`)
- [ ] Type checking passes (`mypy sage/core/providers/openai.py`)
- [ ] CHANGELOG.md updated

### Post-Completion

After all tasks done:
1. Create PR with all changes
2. Request review
3. Run full test suite
4. Merge to main
5. Tag release (v0.2.0)
6. Update Docker images
7. Announce feature

---

## How to Use These Tasks with Claude Code

### Method 1: Sequential Implementation

```
Implement Task 1 from specs/example-openai-provider/tasks.md
```

After Task 1 completes:
```
Implement Task 2 from specs/example-openai-provider/tasks.md
```

Continue until all 12 tasks complete.

### Method 2: Batch Related Tasks

```
Implement Tasks 1-3 (setup and structure) from specs/example-openai-provider/tasks.md
```

Then:
```
Implement Tasks 4-6 (core implementation) from specs/example-openai-provider/tasks.md
```

### Method 3: Use Spec-Kit Commands

```
/speckit.implement

Focus on Task 5 from specs/example-openai-provider/tasks.md.
Use the implementation details from plan.md.
```

---

**Tasks Version**: 1.0  
**Last Updated**: 2026-06-02  
**Status**: Ready for implementation ✅
