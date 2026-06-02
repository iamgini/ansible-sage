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

"""Claude (Anthropic) LLM Provider implementation."""

import os
import time
from typing import Any, Dict, Optional

from anthropic import Anthropic, AsyncAnthropic, APIError, RateLimitError

from sage.core.providers.base import (
    BaseLLMProvider,
    GenerationRequest,
    GenerationResponse,
    ModelTier,
    ProviderStatus,
)
from sage.core.prompt_templates import get_system_prompt, get_event_prompt


class ClaudeProvider(BaseLLMProvider):
    """
    Anthropic Claude LLM provider.

    Supports:
    - Claude 3.5 Sonnet (balanced, recommended)
    - Claude 3 Opus (premium, most capable)
    - Claude 3 Haiku (fast, cost-effective)
    """

    name = "claude"
    display_name = "Anthropic Claude"
    requires_api_key = True

    # Model selection by tier
    MODEL_MAPPING = {
        ModelTier.FAST: "claude-3-haiku-20240307",
        ModelTier.BALANCED: "claude-3-5-sonnet-20241022",
        ModelTier.PREMIUM: "claude-3-opus-20240229",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Claude provider.

        Args:
            config: Provider configuration with 'api_key' required
        """
        super().__init__(config)

        # Initialize sync and async clients
        api_key = self.config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Claude API key not provided")

        self.client = Anthropic(api_key=api_key)
        self.async_client = AsyncAnthropic(api_key=api_key)

        # Configuration
        self.default_model = self.config.get(
            "default_model", self.MODEL_MAPPING[ModelTier.BALANCED]
        )
        self.timeout = self.config.get("timeout", 60)

    def validate_config(self) -> None:
        """Validate Claude provider configuration."""
        api_key = self.config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Claude API key is required. Set ANTHROPIC_API_KEY environment variable "
                "or provide 'api_key' in config."
            )

        if not api_key.startswith("sk-ant-"):
            raise ValueError("Invalid Claude API key format. Should start with 'sk-ant-'")

    async def get_status(self) -> ProviderStatus:
        """
        Check Claude API availability.

        Returns:
            Provider status with availability info
        """
        try:
            # Make a minimal API call to check status
            response = await self.async_client.messages.create(
                model=self.default_model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
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

    async def generate_playbook(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate Ansible playbook using Claude.

        Args:
            request: Generation request parameters

        Returns:
            Generated playbook and metadata

        Raises:
            APIError: If Claude API call fails
        """
        start_time = time.time()

        # Select model based on tier
        model = self.MODEL_MAPPING.get(request.model_tier, self.default_model)

        # Build the prompt
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

        # Make API call
        try:
            response = await self.async_client.messages.create(
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
            )

            # Extract playbook from response
            raw_playbook = response.content[0].text

            # Clean output (remove markdown fences, etc.)
            cleaned_playbook = self.clean_output(raw_playbook)

            # Enforce best practices
            final_playbook = self.enforce_best_practices(cleaned_playbook)

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Extract usage information
            tokens_used = (
                response.usage.input_tokens + response.usage.output_tokens
                if hasattr(response, "usage")
                else None
            )

            return GenerationResponse(
                playbook=final_playbook,
                model=model,
                provider=self.name,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                metadata={
                    "input_tokens": response.usage.input_tokens if hasattr(response, "usage") else None,
                    "output_tokens": response.usage.output_tokens if hasattr(response, "usage") else None,
                    "stop_reason": response.stop_reason if hasattr(response, "stop_reason") else None,
                },
            )

        except RateLimitError as e:
            raise Exception(f"Claude rate limit exceeded: {str(e)}")
        except APIError as e:
            raise Exception(f"Claude API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Playbook generation failed: {str(e)}")

    async def refine_playbook(
        self,
        original_playbook: str,
        issues: str,
        temperature: float = 0.2,
    ) -> GenerationResponse:
        """
        Refine a playbook based on identified issues.

        Args:
            original_playbook: The original playbook with issues
            issues: Description of issues to fix
            temperature: Generation temperature (lower = more focused)

        Returns:
            Refined playbook
        """
        start_time = time.time()

        system_prompt = get_system_prompt()
        user_prompt = f"""The following Ansible playbook has issues that need to be fixed.

## Original Playbook
```yaml
{original_playbook}
```

## Issues Found
{issues}

Generate a corrected version that:
1. Fixes all identified issues
2. Maintains the original functionality
3. Follows Ansible best practices
4. Uses FQCN for all modules

Output only the corrected YAML playbook, no explanations.
"""

        try:
            response = await self.async_client.messages.create(
                model=self.default_model,
                max_tokens=4000,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            raw_playbook = response.content[0].text
            cleaned_playbook = self.clean_output(raw_playbook)
            final_playbook = self.enforce_best_practices(cleaned_playbook)

            latency_ms = int((time.time() - start_time) * 1000)
            tokens_used = (
                response.usage.input_tokens + response.usage.output_tokens
                if hasattr(response, "usage")
                else None
            )

            return GenerationResponse(
                playbook=final_playbook,
                model=self.default_model,
                provider=self.name,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                metadata={"refinement": True},
            )

        except Exception as e:
            raise Exception(f"Playbook refinement failed: {str(e)}")
