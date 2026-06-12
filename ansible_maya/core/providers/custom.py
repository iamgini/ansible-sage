# Copyright 2026 Ansible Maya Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Custom LLM Provider - OpenAI-compatible (LiteLLM, vLLM, etc.)."""

import os
from typing import Optional

from openai import AsyncOpenAI

from ansible_maya.core.providers.base import (
    BaseLLMProvider,
    GenerationRequest,
    GenerationResponse,
    ModelTier,
    ProviderStatus,
)


class CustomProvider(BaseLLMProvider):
    """Custom OpenAI-compatible LLM provider (LiteLLM, vLLM, etc.)."""

    name = "custom"
    display_name = "Custom OpenAI-Compatible LLM"

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize Custom provider.

        Args:
            config: Optional configuration with:
                - endpoint: API endpoint URL
                - api_key: API key for authentication
                - model: Model name to use
        """
        # Get configuration from env or config dict BEFORE super().__init__
        self.endpoint = config.get("endpoint") if config else None
        self.endpoint = self.endpoint or os.getenv("CUSTOM_LLM_ENDPOINT")

        self.api_key = config.get("api_key") if config else None
        self.api_key = self.api_key or os.getenv("CUSTOM_LLM_API_KEY", "dummy-key")

        self.model = config.get("model") if config else None
        self.model = self.model or os.getenv("CUSTOM_LLM_MODEL", "gpt-4")

        if not self.endpoint:
            raise ValueError(
                "Custom LLM endpoint not configured. "
                "Set CUSTOM_LLM_ENDPOINT environment variable."
            )

        # Initialize OpenAI client with custom base URL
        self.client = AsyncOpenAI(
            base_url=self.endpoint,
            api_key=self.api_key,
        )

        # Call parent __init__ AFTER setting attributes
        super().__init__(config)

    async def generate_playbook(
        self, request: GenerationRequest
    ) -> GenerationResponse:
        """
        Generate Ansible playbook using custom LLM.

        Args:
            request: Generation request with prompt and parameters

        Returns:
            Generation response with playbook content
        """
        import time
        from ansible_maya.core.prompt_templates import get_system_prompt, get_event_prompt

        start_time = time.time()

        # Build the prompt (same as Claude provider)
        system_prompt = get_system_prompt()

        # Format event-specific prompt if event_type provided
        if request.event_type:
            user_prompt = get_event_prompt(
                event_type=request.event_type,
                host=request.host or "target_host",
                **{k: v for k, v in (request.constraints or {}).items()},
            )
        else:
            # Use generic event description
            user_prompt = f"""Generate an Ansible playbook to address the following:

{request.event_description}

Host: {request.host or 'target_host'}

Follow all Ansible best practices and use FQCN for modules.
Output only valid YAML, no explanations."""

        # Add existing playbooks context if provided
        if request.existing_playbooks:
            user_prompt += "\n\n## Existing Playbooks for Reference\n"
            for idx, pb in enumerate(request.existing_playbooks, 1):
                user_prompt += f"\n### Playbook {idx}\n```yaml\n{pb}\n```\n"

        # Add inventory context if provided
        if request.inventory_context:
            user_prompt += f"\n\n## Inventory Context\n{request.inventory_context}\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Call custom LLM via OpenAI-compatible API
        # Note: For reasoning models like Qwen, we need higher max_tokens
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=max(request.max_tokens, 8000),  # Reasoning models need more tokens
        )

        # Handle both standard and reasoning models
        message = response.choices[0].message

        # Try to get content from various possible fields
        content = None

        # Standard OpenAI format
        if hasattr(message, 'content') and message.content:
            content = message.content

        # Reasoning model format (Qwen3.6-35B-A3B)
        if not content and hasattr(message, 'reasoning_content') and message.reasoning_content:
            content = message.reasoning_content

        # Check provider_specific_fields (some proxies put it here)
        if not content:
            try:
                # Try accessing as attribute
                if hasattr(message, 'provider_specific_fields'):
                    fields = message.provider_specific_fields
                    if isinstance(fields, dict):
                        content = fields.get('reasoning') or fields.get('reasoning_content')

                # Try accessing raw dict if available
                if not content and hasattr(message, 'model_extra'):
                    extra = message.model_extra
                    if isinstance(extra, dict) and 'provider_specific_fields' in extra:
                        fields = extra['provider_specific_fields']
                        content = fields.get('reasoning') or fields.get('reasoning_content')
            except Exception:
                pass

        if not content:
            raise Exception(f"LLM returned empty response. finish_reason: {response.choices[0].finish_reason}")

        # Clean output (remove markdown fences, etc.) - import from base if available
        import re
        content = re.sub(r'^```ya?ml\s*\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n```\s*$', '', content, flags=re.MULTILINE)
        content = content.strip()

        latency_ms = int((time.time() - start_time) * 1000)

        return GenerationResponse(
            playbook=content,
            model=response.model,
            provider=self.name,
            tokens_used=response.usage.prompt_tokens + response.usage.completion_tokens if response.usage else None,
            latency_ms=latency_ms,
            metadata={
                "input_tokens": response.usage.prompt_tokens if response.usage else None,
                "output_tokens": response.usage.completion_tokens if response.usage else None,
                "endpoint": self.endpoint,
                "model_requested": self.model,
            },
        )

    async def get_status(self) -> ProviderStatus:
        """Get provider status (basic health check)."""
        try:
            # Try a simple completion to verify connectivity
            await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )
            return ProviderStatus(
                available=True,
                model_tier=ModelTier.PRODUCTION,
                message=f"Connected to {self.endpoint}",
            )
        except Exception as e:
            return ProviderStatus(
                available=False,
                model_tier=ModelTier.PRODUCTION,
                message=f"Connection failed: {str(e)}",
            )

    def validate_config(self) -> bool:
        """Validate provider configuration."""
        if not self.endpoint:
            return False
        if not self.model:
            return False
        return True
