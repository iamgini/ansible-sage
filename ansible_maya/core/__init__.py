# Copyright 2026 Ansible Maya Contributors
# Licensed under the Apache License, Version 2.0

"""Core business logic for Ansible Maya."""

from ansible_maya.core.ansible_context import AnsibleContextProcessor, AnsibleFileType
from ansible_maya.core.exceptions import (
    AnsibleLintError,
    ConfigurationError,
    EventClassificationError,
    LLMProviderError,
    PlaybookGenerationError,
    ValidationError,
)
from ansible_maya.core.providers import (
    BaseLLMProvider,
    ClaudeProvider,
    GenerationRequest,
    GenerationResponse,
    ModelTier,
    get_provider,
)
from ansible_maya.core.prompt_templates import get_event_prompt, get_system_prompt

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
