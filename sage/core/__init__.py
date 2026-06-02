# Copyright 2026 Ansible Sage Contributors
# Licensed under the Apache License, Version 2.0

"""Core business logic for Ansible Sage."""

from sage.core.ansible_context import AnsibleContextProcessor, AnsibleFileType
from sage.core.exceptions import (
    AnsibleLintError,
    ConfigurationError,
    EventClassificationError,
    LLMProviderError,
    PlaybookGenerationError,
    ValidationError,
)
from sage.core.providers import (
    BaseLLMProvider,
    ClaudeProvider,
    GenerationRequest,
    GenerationResponse,
    ModelTier,
    get_provider,
)
from sage.core.prompt_templates import get_event_prompt, get_system_prompt

__all__ = [
    # Context processing
    "AnsibleContextProcessor",
    "AnsibleFileType",
    # Providers
    "BaseLLMProvider",
    "ClaudeProvider",
    "GenerationRequest",
    "GenerationResponse",
    "ModelTier",
    "get_provider",
    # Prompts
    "get_system_prompt",
    "get_event_prompt",
    # Exceptions
    "ConfigurationError",
    "LLMProviderError",
    "PlaybookGenerationError",
    "ValidationError",
    "AnsibleLintError",
    "EventClassificationError",
]
