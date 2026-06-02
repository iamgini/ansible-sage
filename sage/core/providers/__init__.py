# Copyright 2026 Ansible Sage Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""LLM Provider package - supports multiple AI model providers."""

from sage.core.providers.base import (
    BaseLLMProvider,
    GenerationRequest,
    GenerationResponse,
    ModelTier,
    ProviderStatus,
)
from sage.core.providers.claude import ClaudeProvider

__all__ = [
    "BaseLLMProvider",
    "ClaudeProvider",
    "GenerationRequest",
    "GenerationResponse",
    "ModelTier",
    "ProviderStatus",
    "get_provider",
]


# Provider registry
PROVIDERS = {
    "claude": ClaudeProvider,
    "anthropic": ClaudeProvider,  # Alias
}


def get_provider(provider_name: str, config: dict = None) -> BaseLLMProvider:
    """
    Get an LLM provider instance by name.

    Args:
        provider_name: Name of the provider ('claude', 'openai', 'ollama', etc.)
        config: Provider-specific configuration

    Returns:
        Initialized provider instance

    Raises:
        ValueError: If provider is not found
    """
    provider_class = PROVIDERS.get(provider_name.lower())
    if not provider_class:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available providers: {', '.join(PROVIDERS.keys())}"
        )

    return provider_class(config=config)
