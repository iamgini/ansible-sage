# Implementation Plan: OpenAI Provider Support

**Based on**: [spec.md](./spec.md)  
**Status**: Example  
**Estimated Time**: 8 hours  

---

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────┐
│         PlaybookOrchestrator                     │
│  (unchanged - provider-agnostic)                │
└──────────────────┬──────────────────────────────┘
                   │
                   │ uses
                   ▼
┌─────────────────────────────────────────────────┐
│    get_provider("openai", config)               │
│         ↓                                        │
│    OpenAIProvider                                │
│    └── inherits from BaseLLMProvider            │
│    └── implements: generate_playbook()          │
│                    validate_config()             │
│                    get_status()                  │
└──────────────────┬──────────────────────────────┘
                   │
                   │ calls
                   ▼
┌─────────────────────────────────────────────────┐
│    OpenAI Python SDK (openai >= 1.0.0)          │
│    AsyncOpenAI client                            │
│    chat.completions.create()                    │
└─────────────────────────────────────────────────┘
```

### Component Interaction

```python
# User/API calls orchestrator
response = await orchestrator.handle_event(event)

# Orchestrator uses injected provider
provider = get_provider("openai", config={"api_key": "..."})
llm_response = await provider.generate_playbook(request)

# OpenAIProvider calls OpenAI API
openai_client = AsyncOpenAI(api_key=config["api_key"])
completion = await openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "system", "content": system_prompt},
              {"role": "user", "content": user_prompt}],
)

# Returns in standard format
return GenerationResponse(
    playbook=cleaned_playbook,
    model="gpt-4o",
    provider="openai",
    tokens_used=completion.usage.total_tokens,
    ...
)
```

---

## Technology Choices

### Decision 1: OpenAI SDK vs HTTP Client

**Options**:
1. Use official `openai` Python SDK
2. Direct HTTP calls with `httpx`

**Decision**: Use official SDK ✅

**Rationale**:
- Official support and updates
- Built-in retry logic and error handling
- Automatic request formatting
- Type hints and better developer experience
- AsyncOpenAI for async support

**Trade-offs**:
- Additional dependency (but necessary anyway)
- Larger package size (acceptable)

---

### Decision 2: Model Selection Strategy

**Options**:
1. Single default model (e.g., always GPT-4)
2. Tier-based selection (fast/balanced/premium)
3. User-specified only

**Decision**: Tier-based with override ✅

**Rationale**:
- Matches existing Claude provider pattern
- Cost optimization (use GPT-3.5 for simple events)
- User can override via `OPENAI_MODEL` env var
- Consistent with existing architecture

**Mapping**:
```python
MODEL_MAPPING = {
    ModelTier.FAST: "gpt-3.5-turbo",      # Cheap, fast for known events
    ModelTier.BALANCED: "gpt-4o",          # Recommended default
    ModelTier.PREMIUM: "gpt-4-turbo",      # Most capable
}
```

---

### Decision 3: Async Implementation

**Approach**: Use `AsyncOpenAI` client ✅

**Rationale**:
- Existing codebase is fully async
- Non-blocking for concurrent requests
- Matches Claude provider pattern
- Better performance under load

**Implementation**:
```python
from openai import AsyncOpenAI

self.client = AsyncOpenAI(api_key=api_key)
response = await self.client.chat.completions.create(...)
```

---

## File Structure

### New Files

```
sage/core/providers/openai.py     # Main implementation (~250 lines)
tests/unit/providers/test_openai.py    # Unit tests (~150 lines)
tests/integration/test_openai_integration.py  # Integration test (~50 lines)
examples/openai_provider.py       # Usage example (~80 lines)
```

### Modified Files

```
sage/core/providers/__init__.py   # Add to PROVIDERS dict (1 line)
.env.example                       # Add OpenAI config (5 lines)
README.md                          # Document OpenAI support (update)
requirements.txt                   # Add openai>=1.0.0 (1 line)
CHANGELOG.md                       # Document new feature (update)
```

---

## Implementation Steps

### Phase 1: Core Provider (3 hours)

#### Step 1.1: Create OpenAIProvider Class
**File**: `sage/core/providers/openai.py`

```python
from openai import AsyncOpenAI, APIError, RateLimitError
from sage.core.providers.base import (
    BaseLLMProvider, GenerationRequest, GenerationResponse, 
    ModelTier, ProviderStatus
)

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
        api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            organization=self.config.get("org_id"),
            base_url=self.config.get("base_url"),
        )
        self.default_model = self.config.get(
            "default_model", self.MODEL_MAPPING[ModelTier.BALANCED]
        )
```

**Tasks**:
- [ ] Import dependencies
- [ ] Define class with model mapping
- [ ] Initialize AsyncOpenAI client
- [ ] Handle missing API key

---

#### Step 1.2: Implement validate_config()

```python
def validate_config(self) -> None:
    """Validate OpenAI configuration."""
    api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key is required. Set OPENAI_API_KEY environment "
            "variable or provide 'api_key' in config."
        )
    
    if not api_key.startswith("sk-"):
        raise ValueError("Invalid OpenAI API key format")
```

**Tasks**:
- [ ] Check API key presence
- [ ] Validate key format
- [ ] Provide helpful error messages

---

#### Step 1.3: Implement get_status()

```python
async def get_status(self) -> ProviderStatus:
    """Check OpenAI API availability."""
    try:
        # Make minimal API call to test connectivity
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
        return ProviderStatus(
            available=False,
            error=f"Rate limited: {str(e)}",
        )
    except APIError as e:
        return ProviderStatus(
            available=False,
            error=f"API error: {str(e)}",
        )
    except Exception as e:
        return ProviderStatus(
            available=False,
            error=f"Unexpected error: {str(e)}",
        )
```

**Tasks**:
- [ ] Make test API call
- [ ] Handle rate limits
- [ ] Handle API errors
- [ ] Return ProviderStatus

---

#### Step 1.4: Implement generate_playbook()

```python
async def generate_playbook(
    self, request: GenerationRequest
) -> GenerationResponse:
    """Generate Ansible playbook using OpenAI."""
    start_time = time.time()
    
    # Select model based on tier
    model = self.MODEL_MAPPING.get(request.model_tier, self.default_model)
    
    # Build messages
    from sage.core.prompt_templates import get_system_prompt, get_event_prompt
    
    system_prompt = get_system_prompt()
    user_prompt = get_event_prompt(
        event_type=request.event_type,
        host=request.host or "target_host",
        **{k: v for k, v in (request.constraints or {}).items()},
    ) if request.event_type else request.event_description
    
    # Add existing playbooks context
    if request.existing_playbooks:
        user_prompt += "\n\n## Existing Playbooks for Reference\n"
        for idx, pb in enumerate(request.existing_playbooks, 1):
            user_prompt += f"\n### Playbook {idx}\n```yaml\n{pb}\n```\n"
    
    try:
        # Call OpenAI API
        completion = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        # Extract playbook
        raw_playbook = completion.choices[0].message.content
        cleaned_playbook = self.clean_output(raw_playbook)
        final_playbook = self.enforce_best_practices(cleaned_playbook)
        
        # Calculate latency
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

**Tasks**:
- [ ] Select model based on tier
- [ ] Build system and user prompts (reuse existing templates)
- [ ] Add context (existing playbooks, inventory)
- [ ] Call OpenAI API
- [ ] Clean output (remove markdown fences)
- [ ] Enforce best practices
- [ ] Extract token usage
- [ ] Handle errors (rate limits, auth, API errors)

---

### Phase 2: Registration & Configuration (1 hour)

#### Step 2.1: Register Provider

**File**: `sage/core/providers/__init__.py`

```python
from sage.core.providers.openai import OpenAIProvider  # Add import

PROVIDERS = {
    "claude": ClaudeProvider,
    "anthropic": ClaudeProvider,
    "openai": OpenAIProvider,  # Add this line
    "gpt": OpenAIProvider,  # Alias
}
```

**Tasks**:
- [ ] Import OpenAIProvider
- [ ] Add to PROVIDERS dict
- [ ] Add "gpt" alias

---

#### Step 2.2: Update Configuration

**File**: `.env.example`

Add:
```bash
# OpenAI (GPT-4, GPT-3.5)
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o  # Optional: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
OPENAI_ORG_ID=org-your-org-id  # Optional organization ID
```

**Tasks**:
- [ ] Add OpenAI configuration section
- [ ] Document all options
- [ ] Add examples

---

### Phase 3: Testing (3 hours)

#### Step 3.1: Unit Tests

**File**: `tests/unit/providers/test_openai.py`

```python
import pytest
from unittest.mock import AsyncMock, Mock, patch
from sage.core.providers.openai import OpenAIProvider
from sage.core.providers.base import GenerationRequest, ModelTier

@pytest.fixture
def openai_provider():
    """Create OpenAI provider with mock API key."""
    return OpenAIProvider(config={"api_key": "sk-test-key"})

class TestOpenAIProvider:
    def test_provider_initialization(self):
        """Test provider initializes correctly."""
        provider = OpenAIProvider(config={"api_key": "sk-test"})
        assert provider.name == "openai"
        assert provider.display_name == "OpenAI GPT"
    
    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        with pytest.raises(ValueError, match="API key"):
            OpenAIProvider(config={})
    
    def test_model_tier_mapping(self, openai_provider):
        """Test that model tiers map correctly."""
        assert openai_provider.MODEL_MAPPING[ModelTier.FAST] == "gpt-3.5-turbo"
        assert openai_provider.MODEL_MAPPING[ModelTier.BALANCED] == "gpt-4o"
        assert openai_provider.MODEL_MAPPING[ModelTier.PREMIUM] == "gpt-4-turbo"
    
    @pytest.mark.asyncio
    async def test_generate_playbook_success(self, openai_provider):
        """Test successful playbook generation."""
        # Mock OpenAI response
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content="---\n- name: Test"))]
        mock_completion.usage = Mock(
            total_tokens=100, 
            prompt_tokens=60, 
            completion_tokens=40
        )
        mock_completion.model = "gpt-4o"
        
        with patch.object(
            openai_provider.client.chat.completions,
            'create',
            return_value=mock_completion
        ):
            request = GenerationRequest(
                event_description="Test event",
                event_type="disk_full",
                host="test-host",
            )
            
            response = await openai_provider.generate_playbook(request)
            
            assert "---" in response.playbook
            assert response.provider == "openai"
            assert response.model == "gpt-4o"
            assert response.tokens_used == 100
    
    @pytest.mark.asyncio
    async def test_rate_limit_error(self, openai_provider):
        """Test rate limit error handling."""
        from openai import RateLimitError
        
        with patch.object(
            openai_provider.client.chat.completions,
            'create',
            side_effect=RateLimitError("Rate limit exceeded")
        ):
            request = GenerationRequest(event_description="Test")
            
            with pytest.raises(Exception, match="rate limit"):
                await openai_provider.generate_playbook(request)
```

**Tasks**:
- [ ] Test initialization
- [ ] Test configuration validation
- [ ] Test model tier mapping
- [ ] Test successful generation (with mocks)
- [ ] Test error scenarios (rate limit, auth, API errors)
- [ ] Test token usage extraction
- [ ] Test output cleaning

---

#### Step 3.2: Integration Test

**File**: `tests/integration/test_openai_integration.py`

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
        event_description="Clean up disk space on /var partition",
        event_type="disk_full",
        host="test-server-01",
        model_tier=ModelTier.FAST,  # Use cheaper model for testing
    )
    
    response = await provider.generate_playbook(request)
    
    # Verify response structure
    assert response.playbook
    assert "---" in response.playbook
    assert "ansible.builtin" in response.playbook
    assert response.provider == "openai"
    assert response.tokens_used > 0
    assert response.latency_ms > 0
    
    # Verify metadata
    assert "prompt_tokens" in response.metadata
    assert "completion_tokens" in response.metadata
    
    print(f"Generated playbook ({response.tokens_used} tokens):")
    print(response.playbook)
```

**Tasks**:
- [ ] Test with real OpenAI API (marked as integration test)
- [ ] Verify playbook structure
- [ ] Verify FQCN usage
- [ ] Verify token tracking
- [ ] Print generated playbook for manual review

---

### Phase 4: Documentation & Examples (1 hour)

#### Step 4.1: Usage Example

**File**: `examples/openai_provider.py`

```python
#!/usr/bin/env python3
"""
Example: Using OpenAI Provider for Playbook Generation

Demonstrates how to use OpenAI GPT-4 instead of Claude.
"""

import asyncio
import os
from datetime import datetime

from sage.core.providers import get_provider
from sage.handlers.orchestrator import AIOpsEvent, EventSeverity, PlaybookOrchestrator


async def main():
    print("=" * 70)
    print("Ansible Sage - OpenAI Provider Example")
    print("=" * 70)
    
    # 1. Configure OpenAI Provider
    print("\n1. Configuring OpenAI Provider (GPT-4)...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='sk-proj-...'")
        return
    
    provider = get_provider("openai", config={"api_key": api_key})
    print(f"✓ Provider configured: {provider.display_name}")
    
    # 2. Check provider status
    print("\n2. Checking OpenAI API Status...")
    status = await provider.get_status()
    if status.available:
        print(f"✓ OpenAI API is available (model: {status.model})")
    else:
        print(f"❌ OpenAI API unavailable: {status.error}")
        return
    
    # 3. Create infrastructure event
    print("\n3. Creating Infrastructure Event...")
    event = AIOpsEvent(
        event_id="example-openai-001",
        event_type="service_down",
        description="Nginx service stopped unexpectedly on production server",
        host="web-server-prod-01.example.com",
        severity=EventSeverity.CRITICAL,
        timestamp=datetime.now(),
        metadata={
            "service": "nginx",
            "port": 80,
            "last_active": "2026-06-02T14:30:00Z",
        },
    )
    print(f"✓ Event: {event.event_type} on {event.host}")
    
    # 4. Generate playbook
    print("\n4. Generating Playbook with OpenAI GPT-4...")
    orchestrator = PlaybookOrchestrator(provider=provider)
    
    response = await orchestrator.handle_event(event)
    
    # 5. Display results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"\nModel: {response.generation_metadata.get('model')}")
    print(f"Provider: {response.generation_metadata.get('provider')}")
    print(f"Tokens Used: {response.generation_metadata.get('tokens_used')}")
    print(f"  - Prompt: {response.generation_metadata.get('prompt_tokens')}")
    print(f"  - Completion: {response.generation_metadata.get('completion_tokens')}")
    print(f"Latency: {response.generation_metadata.get('latency_ms')}ms")
    print(f"\nConfidence: {response.confidence_score:.0%} ({response.confidence_level})")
    print(f"Target Branch: {response.target_branch}")
    print(f"Validation: {'✓ Passed' if response.validation_result.passed else '✗ Failed'}")
    
    print(f"\n{response.recommended_action}")
    
    print("\n" + "=" * 70)
    print("GENERATED PLAYBOOK")
    print("=" * 70)
    print(response.playbook)
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
```

**Tasks**:
- [ ] Create example script
- [ ] Show provider initialization
- [ ] Show status checking
- [ ] Show playbook generation
- [ ] Display token usage
- [ ] Make executable

---

#### Step 4.2: Update Documentation

**Files**: README.md, CLAUDE.md, QUICKSTART.md

**README.md additions**:
```markdown
### LLM Provider Configuration

```bash
# Claude (Anthropic)
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-your-key-here

# OpenAI (GPT-4)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o  # Optional: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
```

**Supported Providers**:
- **Claude** (Anthropic): claude-3-5-sonnet, claude-3-opus, claude-3-haiku
- **OpenAI**: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
- **Ollama**: Local LLM support (coming soon)
```

**Tasks**:
- [ ] Update README.md with OpenAI configuration
- [ ] Update QUICKSTART.md
- [ ] Add to CLAUDE.md provider section
- [ ] Update CHANGELOG.md

---

## Error Handling Strategy

### Error Mapping

| OpenAI Error | Ansible Sage Exception | HTTP Status |
|-------------|----------------------|-------------|
| 401 Unauthorized | `LLMAuthenticationError` | 500 |
| 429 Rate Limit | `LLMRateLimitError` | 429 |
| 400 Bad Request | `PlaybookGenerationError` | 500 |
| 500+ Server Error | `LLMUnavailableError` | 503 |
| Network Timeout | `LLMUnavailableError` | 504 |

### Retry Strategy

- ❌ No automatic retries (caller decides)
- ✅ Single timeout per request (15 seconds)
- ✅ Clear error messages with context
- ✅ Log all errors with event_id

---

## Performance Considerations

### Latency Targets

- GPT-3.5-turbo: < 5 seconds (typical)
- GPT-4o: < 10 seconds (typical)
- GPT-4-turbo: < 15 seconds (typical)

### Cost Optimization

Use tier-based model selection:
- Known safe events → GPT-3.5-turbo (cheapest)
- Standard events → GPT-4o (balanced)
- Complex events → GPT-4-turbo (most capable)

### Token Limits

- Input: ~3000 tokens (prompts + context)
- Output: ~1000 tokens (typical playbook)
- Total: ~4000 tokens per request

---

## Security Considerations

### API Key Protection

```python
# ✅ Good - from environment
api_key = os.getenv("OPENAI_API_KEY")

# ❌ Never - hardcoded
api_key = "sk-proj-..."  # NEVER DO THIS

# ✅ Good - redact in errors
logger.error(f"API error", extra={"api_key": "sk-...***"})

# ❌ Never - log full key
logger.error(f"API key: {api_key}")  # NEVER DO THIS
```

### Data Privacy

- Don't send sensitive data in events to LLM
- Sanitize host information if needed
- Review OpenAI data usage policy
- Consider data residency requirements

---

## Testing Strategy

### Test Pyramid

```
    ▲
   /│\     1 integration test (real API)
  / │ \    
 /  │  \   ~10 unit tests (mocked)
/____|___\  
```

### Coverage Requirements

- Unit tests: 80%+ coverage
- Integration test: 1 full workflow
- Error scenarios: All error types tested

### Mock Strategy

```python
# Mock OpenAI completion
mock_completion = Mock(
    choices=[Mock(message=Mock(content="--- playbook"))],
    usage=Mock(total_tokens=100, prompt_tokens=60, completion_tokens=40),
    model="gpt-4o",
)

with patch.object(provider.client.chat.completions, 'create', 
                  return_value=mock_completion):
    response = await provider.generate_playbook(request)
```

---

## Rollout Plan

### Phase 1: Development (Complete Implementation)
- [ ] Implement OpenAIProvider class
- [ ] Add unit tests (80%+ coverage)
- [ ] Add integration test
- [ ] Update documentation

### Phase 2: Internal Testing
- [ ] Test with real OpenAI API
- [ ] Compare output quality with Claude
- [ ] Test error scenarios
- [ ] Verify token usage accuracy

### Phase 3: Documentation & Examples
- [ ] Complete all documentation updates
- [ ] Create usage examples
- [ ] Update CHANGELOG.md
- [ ] Review SPEC-KIT spec for completeness

### Phase 4: Release
- [ ] Merge to main branch
- [ ] Tag release (v0.2.0)
- [ ] Update Docker images
- [ ] Announce feature

---

## Acceptance Criteria

### Must Have ✅

- [ ] OpenAIProvider implements BaseLLMProvider fully
- [ ] All three model tiers supported
- [ ] Generates valid, FQCN-compliant playbooks
- [ ] Token usage accurately tracked
- [ ] Error handling for all OpenAI errors
- [ ] 80%+ test coverage
- [ ] Documentation complete
- [ ] Example script works

### Nice to Have 📋

- [ ] Retry logic for transient errors
- [ ] Streaming response support
- [ ] Cost estimation per request
- [ ] Model performance comparison docs

---

## Dependencies & Prerequisites

### External
- OpenAI API key (user-provided)
- `openai` Python package >= 1.0.0
- Network access to api.openai.com

### Internal
- Existing BaseLLMProvider interface
- Existing prompt templates
- Provider registry system

---

## Success Metrics

After implementation, verify:

1. ✅ Can switch between Claude and OpenAI with env var only
2. ✅ Generated playbooks pass ansible-lint
3. ✅ Token usage matches OpenAI dashboard
4. ✅ Error messages are clear and actionable
5. ✅ No breaking changes to existing code
6. ✅ Documentation is complete and accurate

---

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Core Implementation | 3 hours | Steps 1.1-1.4 |
| Registration & Config | 1 hour | Steps 2.1-2.2 |
| Testing | 3 hours | Steps 3.1-3.2 |
| Documentation | 1 hour | Steps 4.1-4.2 |
| **Total** | **8 hours** | |

---

## Next Steps After Completion

1. Consider adding more providers (Ollama, custom endpoints)
2. Implement streaming responses
3. Add cost tracking and reporting
4. Create provider comparison benchmarks

---

**Plan Version**: 1.0  
**Last Updated**: 2026-06-02  
**Status**: Ready for implementation
