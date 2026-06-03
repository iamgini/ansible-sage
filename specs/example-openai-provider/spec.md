# Specification: OpenAI Provider Support

**Feature ID**: 002  
**Status**: Example  
**Priority**: High  
**Estimated Effort**: 8 hours  

---

## Overview

Add support for OpenAI GPT-4 and GPT-3.5 as LLM providers for playbook generation, following the existing `BaseLLMProvider` interface.

## Problem Statement

Currently, Ansible Maya only supports Claude (Anthropic) as an LLM provider. Many users prefer or require OpenAI's GPT models due to:
- Existing OpenAI API subscriptions
- Corporate vendor preferences
- Specific model capabilities (GPT-4o, GPT-4-turbo)
- Cost optimization (GPT-3.5-turbo is cheaper for simple events)

## Goals

✅ Support OpenAI GPT-4 and GPT-3.5 models  
✅ Follow existing `BaseLLMProvider` interface (no special cases)  
✅ Support all three model tiers (fast/balanced/premium)  
✅ Proper error handling (rate limits, auth failures)  
✅ Token usage tracking and reporting  

## Non-Goals

❌ Support for legacy models (GPT-3, davinci, etc.)  
❌ Support for fine-tuned models (yet)  
❌ Streaming responses (can be added later)  
❌ Vision/image capabilities (text-only playbook generation)  

---

## User Stories

### US-1: Configure OpenAI Provider
**As a** DevOps engineer  
**I want** to use OpenAI GPT-4 for playbook generation  
**So that** I can leverage my existing OpenAI subscription

**Acceptance Criteria**:
- Can set `LLM_PROVIDER=openai` in environment
- `OPENAI_API_KEY` can be configured via environment variable
- Can specify model via `OPENAI_MODEL` (e.g., `gpt-4-turbo`)
- Configuration validation on startup
- Clear error message if API key missing

**Test Cases**:
```python
# Valid configuration
provider = get_provider("openai", config={"api_key": "sk-..."})
assert provider.name == "openai"

# Missing API key
with pytest.raises(ValueError, match="API key"):
    get_provider("openai", config={})
```

---

### US-2: Generate Playbook with OpenAI
**As a** system  
**I want** to generate playbooks using OpenAI's API  
**So that** users can choose their preferred LLM provider

**Acceptance Criteria**:
- Generates valid Ansible playbooks using GPT-4
- Applies same prompt templates as Claude provider
- Returns `GenerationResponse` with playbook content
- Includes token usage in metadata
- Handles API errors gracefully

**Test Cases**:
```python
# Successful generation
response = await openai_provider.generate_playbook(request)
assert "---" in response.playbook  # Valid YAML
assert "ansible.builtin" in response.playbook  # FQCN
assert response.tokens_used > 0

# API error
with mock_openai_error():
    with pytest.raises(LLMProviderError):
        await openai_provider.generate_playbook(request)
```

---

### US-3: Model Tier Mapping
**As a** system  
**I want** to automatically select appropriate OpenAI model based on tier  
**So that** simple events use cheaper models, complex events use better models

**Acceptance Criteria**:
- `ModelTier.FAST` → `gpt-3.5-turbo` (cheap, fast)
- `ModelTier.BALANCED` → `gpt-4o` (recommended default)
- `ModelTier.PREMIUM` → `gpt-4-turbo` (most capable)
- User can override default model via config
- Model selection logged for debugging

**Test Cases**:
```python
# Fast tier uses GPT-3.5
request = GenerationRequest(event_description="...", model_tier=ModelTier.FAST)
response = await provider.generate_playbook(request)
assert "gpt-3.5-turbo" in response.metadata["model"]

# Premium tier uses GPT-4-turbo
request = GenerationRequest(event_description="...", model_tier=ModelTier.PREMIUM)
response = await provider.generate_playbook(request)
assert "gpt-4-turbo" in response.metadata["model"]
```

---

### US-4: Rate Limit Handling
**As a** system  
**I want** to handle OpenAI rate limits gracefully  
**So that** users get clear error messages and can retry

**Acceptance Criteria**:
- Detect rate limit errors (HTTP 429)
- Raise `LLMRateLimitError` exception
- Include retry-after information in error
- Log rate limit events
- Return proper HTTP 429 from API endpoint

**Test Cases**:
```python
# Rate limit error
with mock_rate_limit_error(retry_after=60):
    with pytest.raises(LLMRateLimitError) as exc:
        await provider.generate_playbook(request)
    assert "retry after 60 seconds" in str(exc.value).lower()
```

---

### US-5: Token Usage Tracking
**As a** administrator  
**I want** to see token usage for OpenAI API calls  
**So that** I can track costs and optimize usage

**Acceptance Criteria**:
- Response includes `tokens_used` (input + output)
- Separate tracking of prompt_tokens and completion_tokens
- Logged with each generation
- Available in API response metadata

**Test Cases**:
```python
response = await provider.generate_playbook(request)
assert response.tokens_used > 0
assert "prompt_tokens" in response.metadata
assert "completion_tokens" in response.metadata
```

---

## Functional Requirements

### FR-1: Provider Implementation
The `OpenAIProvider` class must:
- Inherit from `BaseLLMProvider`
- Implement `generate_playbook(request: GenerationRequest) -> GenerationResponse`
- Implement `validate_config() -> None`
- Implement `get_status() -> ProviderStatus`
- Support async operations throughout

### FR-2: Configuration
Required environment variables:
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o  # Optional, defaults per tier
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional override
OPENAI_ORG_ID=org-...  # Optional organization ID
```

### FR-3: Error Handling
Must handle and properly categorize:
- Authentication errors (401) → `LLMAuthenticationError`
- Rate limits (429) → `LLMRateLimitError`
- Invalid requests (400) → `PlaybookGenerationError`
- Server errors (500+) → `LLMUnavailableError`
- Network errors (timeout, connection) → `LLMUnavailableError`

### FR-4: Response Processing
- Clean markdown code fences (```yaml)
- Enforce FQCN (same as Claude)
- Validate YAML syntax
- Extract token usage from response

---

## Non-Functional Requirements

### NFR-1: Performance
- API calls complete within 15 seconds (timeout)
- No blocking on rate limits (fail fast)
- Async/await throughout

### NFR-2: Reliability
- Handle transient network errors
- Retry on network timeout (1 retry max)
- Proper cleanup on errors

### NFR-3: Security
- API key never logged
- API key stored in environment only
- Redact key in error messages

### NFR-4: Compatibility
- Works with existing orchestrator without changes
- Same response format as Claude provider
- No breaking changes to API

---

## Constraints

### Technical Constraints
- Must use OpenAI Python SDK (`openai >= 1.0.0`)
- Must support Python 3.11+
- Must be async (no sync blocking calls)

### Business Constraints
- Users must provide their own OpenAI API key
- No free tier or fallback (fail if no key)

### Compatibility Constraints
- Must work with existing `PlaybookOrchestrator`
- Must register in provider registry
- Must use same prompt templates

---

## Dependencies

### External Dependencies
- `openai` Python package (version >= 1.0.0)
- Valid OpenAI API key
- Network access to `api.openai.com`

### Internal Dependencies
- `sage.core.providers.base.BaseLLMProvider`
- `sage.core.prompt_templates`
- `sage.core.exceptions`

---

## API Contract

### Provider Interface

```python
class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider for playbook generation."""
    
    name: str = "openai"
    display_name: str = "OpenAI GPT"
    requires_api_key: bool = True
    
    async def generate_playbook(
        self, 
        request: GenerationRequest
    ) -> GenerationResponse:
        """Generate playbook using OpenAI API."""
        pass
    
    def validate_config(self) -> None:
        """Validate OpenAI configuration."""
        pass
    
    async def get_status(self) -> ProviderStatus:
        """Check OpenAI API availability."""
        pass
```

### Response Format

Same as existing `GenerationResponse`:

```python
GenerationResponse(
    playbook="---\n- name: ...",
    model="gpt-4o",
    provider="openai",
    tokens_used=1250,
    latency_ms=3400,
    metadata={
        "prompt_tokens": 850,
        "completion_tokens": 400,
        "model_version": "gpt-4o-2024-05-13"
    }
)
```

---

## Success Metrics

### Quantitative
- ✅ 100% of existing tests still pass
- ✅ 80%+ code coverage on new provider
- ✅ API calls complete in <15 seconds (95th percentile)
- ✅ Token usage accurately tracked

### Qualitative
- ✅ Generated playbooks pass ansible-lint
- ✅ Same quality as Claude-generated playbooks
- ✅ Clear error messages on failure
- ✅ Easy to configure and use

---

## Out of Scope (Future Work)

- Streaming responses (OpenAI supports this)
- Function calling / structured outputs
- Fine-tuned model support
- GPT-4 Vision integration
- Batch API support
- Assistants API integration

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| OpenAI API changes | High | Medium | Use official SDK, version pinning |
| Rate limiting in production | Medium | High | Clear error messages, user monitoring |
| Higher costs than Claude | Low | High | Document pricing, support tier selection |
| Different prompt behavior | Medium | Medium | Extensive testing, prompt tuning |

---

## Acceptance Checklist

Before marking complete, verify:

- [ ] All user stories implemented and tested
- [ ] Unit tests for all methods (80%+ coverage)
- [ ] Integration test with real OpenAI API
- [ ] Error scenarios tested (auth, rate limit, network)
- [ ] Documentation updated (README, .env.example, CLAUDE.md)
- [ ] Example added to `examples/openai_provider.py`
- [ ] Provider registered in `PROVIDERS` dict
- [ ] No breaking changes to existing code
- [ ] No API keys in code or tests
- [ ] CHANGELOG.md updated

---

## References

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Ansible Maya BaseLLMProvider](../sage/core/providers/base.py)
- [Existing Claude Provider](../sage/core/providers/claude.py)

---

**Specification Version**: 1.0  
**Last Updated**: 2026-06-02  
**Author**: Ansible Maya Team
