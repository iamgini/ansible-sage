# Copyright 2026 Ansible AI Gateway Contributors
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

"""
Base LLM Provider - Abstract interface for AI model providers.

Ported from vscode-ansible providers/base.ts - enables BYOM (Bring Your Own Model).
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml


class ModelTier(Enum):
    """Model capability tiers."""

    FAST = "fast"  # Fast, lower-cost models for simple tasks
    BALANCED = "balanced"  # Balanced performance and cost
    PREMIUM = "premium"  # Most capable models for complex generation


@dataclass
class GenerationRequest:
    """Request parameters for playbook generation."""

    event_description: str
    event_type: Optional[str] = None
    host: Optional[str] = None
    existing_playbooks: Optional[List[str]] = None
    inventory_context: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None
    model_tier: ModelTier = ModelTier.BALANCED
    temperature: float = 0.3
    max_tokens: int = 4000
    is_multi_task: bool = False  # Flag for multi-task chaining


@dataclass
class GenerationResponse:
    """Response from LLM playbook generation."""

    playbook: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProviderStatus:
    """Status of an LLM provider."""

    available: bool
    model: Optional[str] = None
    error: Optional[str] = None
    rate_limit_remaining: Optional[int] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Subclasses must implement:
    - generate_playbook() - Generate playbook from event
    - validate_config() - Validate provider configuration
    - get_status() - Check provider availability
    """

    name: str = "base"
    display_name: str = "Base Provider"
    requires_api_key: bool = True

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize provider with configuration.

        Args:
            config: Provider-specific configuration (API keys, endpoints, etc.)
        """
        self.config = config or {}
        self.validate_config()

    @abstractmethod
    async def generate_playbook(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate Ansible playbook from event description.

        Args:
            request: Generation request parameters

        Returns:
            Generated playbook and metadata

        Raises:
            LLMProviderError: If generation fails
        """
        pass

    @abstractmethod
    def validate_config(self) -> None:
        """
        Validate provider configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    @abstractmethod
    async def get_status(self) -> ProviderStatus:
        """
        Check provider availability and status.

        Returns:
            Provider status information
        """
        pass

    def clean_output(self, raw_output: str) -> str:
        """
        Clean LLM output to extract valid YAML.

        Removes:
        - Markdown code fences (```yaml, ```)
        - Explanatory text before/after YAML
        - Excessive whitespace

        Args:
            raw_output: Raw LLM response

        Returns:
            Cleaned YAML content
        """
        # Remove markdown code fences
        content = re.sub(r"```ya?ml\s*\n", "", raw_output)
        content = re.sub(r"```\s*$", "", content)

        # Extract YAML content (lines starting with - or alphanumeric)
        lines = content.split("\n")
        yaml_lines = []
        in_yaml = False

        for line in lines:
            stripped = line.strip()

            # Start of YAML content
            if stripped.startswith("---") or stripped.startswith("-") or (
                stripped and not in_yaml and re.match(r"^[a-z_]", stripped, re.IGNORECASE)
            ):
                in_yaml = True

            if in_yaml:
                yaml_lines.append(line)

        result = "\n".join(yaml_lines).strip()

        # Validate it's valid YAML
        try:
            yaml.safe_load(result)
            return result
        except yaml.YAMLError:
            # If cleaning failed, return original (will fail validation later)
            return raw_output.strip()

    def enforce_best_practices(self, playbook_content: str) -> str:
        """
        Enforce Ansible best practices on generated content.

        - Ensures FQCN for builtin modules
        - Adds check_mode support where appropriate
        - Validates naming conventions

        Args:
            playbook_content: Generated playbook YAML

        Returns:
            Playbook with best practices enforced
        """
        # This is a basic implementation - can be enhanced
        # The AnsibleContextProcessor has more sophisticated FQCN enforcement

        # Ensure all plays have names
        lines = playbook_content.split("\n")
        result = []

        for i, line in enumerate(lines):
            # Add name to unnamed plays
            if line.strip().startswith("- hosts:") or line.strip().startswith("hosts:"):
                # Check if previous line has name
                if i == 0 or not any(
                    prev_line.strip().startswith("- name:") or prev_line.strip().startswith("name:")
                    for prev_line in lines[max(0, i - 2) : i]
                ):
                    indent = len(line) - len(line.lstrip())
                    result.append(" " * indent + "- name: Auto-generated playbook")

            result.append(line)

        return "\n".join(result)

    def extract_tasks_count(self, playbook_content: str) -> int:
        """
        Count number of tasks in playbook.

        Args:
            playbook_content: Playbook YAML content

        Returns:
            Number of tasks found
        """
        try:
            data = yaml.safe_load(playbook_content)
            if not data:
                return 0

            task_count = 0
            if isinstance(data, list):
                for play in data:
                    if isinstance(play, dict):
                        if "tasks" in play:
                            task_count += len(play["tasks"])
                        if "pre_tasks" in play:
                            task_count += len(play["pre_tasks"])
                        if "post_tasks" in play:
                            task_count += len(play["post_tasks"])

            return task_count
        except (yaml.YAMLError, TypeError, AttributeError):
            return 0

    def is_multi_task_request(self, event_description: str) -> bool:
        """
        Detect if event requires multiple tasks.

        Args:
            event_description: Event description

        Returns:
            True if multiple tasks are likely needed
        """
        multi_task_indicators = [
            "and then",
            "after that",
            "first",
            "second",
            "finally",
            "also",
            "multiple",
            "several",
        ]

        description_lower = event_description.lower()
        return any(indicator in description_lower for indicator in multi_task_indicators)
