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
Ansible Context Processor - ported from vscode-ansible ansibleContext.ts

Processes Ansible content to provide relevant context to LLMs for playbook generation.
Handles file type detection, YAML normalization, and context extraction.
"""

import re
from enum import Enum
from pathlib import Path
from typing import Optional


class AnsibleFileType(Enum):
    """Ansible file types based on content analysis."""

    PLAYBOOK = "playbook"
    TASKS = "tasks"
    HANDLERS = "handlers"
    VARS = "vars"
    DEFAULTS = "defaults"
    META = "meta"
    INVENTORY = "inventory"
    ROLE = "role"
    UNKNOWN = "unknown"


class AnsibleContextProcessor:
    """
    Processes Ansible content to extract relevant context for LLM prompts.

    Ported from vscode-ansible's AnsibleContextProcessor TypeScript class.
    Key responsibilities:
    - Detect Ansible file types from content and path
    - Extract relevant sections (tasks, vars, handlers)
    - Normalize YAML content for LLM consumption
    - Enforce best practices (FQCN for modules)
    """

    # File type detection patterns
    PLAYBOOK_INDICATORS = [
        r"^\s*-\s+hosts:",
        r"^\s*-\s+name:.*\n\s+hosts:",
        r"^\s*-\s+import_playbook:",
        r"^\s*-\s+ansible\.builtin\.import_playbook:",
    ]

    TASKS_INDICATORS = [
        r"^\s*-\s+name:",
        r"^\s*-\s+ansible\.builtin\.",
        r"^\s*-\s+[a-z_]+\.[a-z_]+\.",  # FQCN pattern
    ]

    # Module FQCN enforcement patterns
    BUILTIN_MODULES = {
        "debug", "set_fact", "include_vars", "include_tasks", "import_tasks",
        "command", "shell", "raw", "script", "copy", "file", "template",
        "lineinfile", "blockinfile", "replace", "yum", "apt", "dnf",
        "service", "systemd", "user", "group", "get_url", "uri", "wait_for",
        "stat", "assert", "fail", "package", "pip", "git", "unarchive",
    }

    def __init__(self):
        """Initialize the context processor."""
        self._file_type_cache = {}

    def detect_file_type(self, content: str, file_path: Optional[Path] = None) -> AnsibleFileType:
        """
        Detect Ansible file type from content and optional file path.

        Args:
            content: YAML content to analyze
            file_path: Optional file path for additional context

        Returns:
            Detected AnsibleFileType
        """
        # Check cache first
        cache_key = (content[:500], str(file_path) if file_path else "")
        if cache_key in self._file_type_cache:
            return self._file_type_cache[cache_key]

        detected_type = self._detect_file_type_internal(content, file_path)
        self._file_type_cache[cache_key] = detected_type
        return detected_type

    def _detect_file_type_internal(
        self, content: str, file_path: Optional[Path] = None
    ) -> AnsibleFileType:
        """Internal file type detection logic."""
        # Path-based detection
        if file_path:
            path_str = str(file_path)
            if "/tasks/" in path_str or path_str.endswith("/main.yml"):
                if "/tasks/" in path_str:
                    return AnsibleFileType.TASKS
            if "/handlers/" in path_str:
                return AnsibleFileType.HANDLERS
            if "/vars/" in path_str or "/group_vars/" in path_str or "/host_vars/" in path_str:
                return AnsibleFileType.VARS
            if "/defaults/" in path_str:
                return AnsibleFileType.DEFAULTS
            if "/meta/" in path_str:
                return AnsibleFileType.META
            if "inventory" in path_str.lower() or path_str.endswith(".ini"):
                return AnsibleFileType.INVENTORY

        # Content-based detection
        content_lower = content.lower()

        # Check for playbook indicators
        for pattern in self.PLAYBOOK_INDICATORS:
            if re.search(pattern, content, re.MULTILINE):
                return AnsibleFileType.PLAYBOOK

        # Check for tasks file
        for pattern in self.TASKS_INDICATORS:
            if re.search(pattern, content, re.MULTILINE):
                return AnsibleFileType.TASKS

        # Check for vars file (simple key-value pairs)
        if self._looks_like_vars(content):
            return AnsibleFileType.VARS

        return AnsibleFileType.UNKNOWN

    def _looks_like_vars(self, content: str) -> bool:
        """Check if content looks like a vars file."""
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        if not lines:
            return False

        # Vars files typically have key: value pairs without list indicators
        var_pattern = re.compile(r"^[a-z_][a-z0-9_]*:\s*.+$", re.IGNORECASE)
        matching_lines = sum(1 for line in lines if var_pattern.match(line))

        # If >50% of non-empty lines are var definitions
        return matching_lines / len(lines) > 0.5

    def enforce_fqcn(self, content: str) -> str:
        """
        Enforce FQCN (Fully Qualified Collection Names) for builtin modules.

        Converts short module names like 'debug' to 'ansible.builtin.debug'.

        Args:
            content: YAML content with potential short module names

        Returns:
            Content with FQCN enforced
        """
        lines = content.split("\n")
        result = []

        for line in lines:
            # Skip comments and empty lines
            if not line.strip() or line.strip().startswith("#"):
                result.append(line)
                continue

            # Check for short module names (simple key at task level)
            modified_line = line
            for module in self.BUILTIN_MODULES:
                # Pattern: "  module_name:" (with proper indentation)
                pattern = rf"^(\s+){module}:"
                if re.match(pattern, line):
                    # Replace with FQCN
                    modified_line = re.sub(
                        rf"^(\s+){module}:",
                        rf"\1ansible.builtin.{module}:",
                        line,
                    )
                    break

            result.append(modified_line)

        return "\n".join(result)

    def normalize_yaml_for_llm(self, content: str) -> str:
        """
        Normalize YAML content for better LLM understanding.

        - Removes excessive whitespace
        - Ensures consistent indentation
        - Removes empty lines between related items

        Args:
            content: Raw YAML content

        Returns:
            Normalized YAML content
        """
        lines = content.split("\n")
        normalized = []
        prev_indent = 0

        for line in lines:
            stripped = line.rstrip()

            # Skip completely empty lines at the start
            if not normalized and not stripped:
                continue

            # Keep line but normalize trailing whitespace
            if stripped:
                # Calculate indent level
                indent = len(line) - len(line.lstrip())

                # Add blank line before top-level items (except first)
                if indent == 0 and normalized and prev_indent > 0:
                    normalized.append("")

                prev_indent = indent

            normalized.append(stripped)

        # Remove trailing empty lines
        while normalized and not normalized[-1]:
            normalized.pop()

        return "\n".join(normalized)

    def extract_context(
        self, content: str, file_path: Optional[Path] = None, max_lines: int = 100
    ) -> dict:
        """
        Extract relevant context from Ansible content for LLM prompts.

        Args:
            content: Ansible YAML content
            file_path: Optional file path
            max_lines: Maximum number of lines to include

        Returns:
            Dictionary with file_type, content, and metadata
        """
        file_type = self.detect_file_type(content, file_path)

        # Normalize and enforce FQCN
        processed_content = self.normalize_yaml_for_llm(content)
        if file_type in (AnsibleFileType.PLAYBOOK, AnsibleFileType.TASKS):
            processed_content = self.enforce_fqcn(processed_content)

        # Truncate if needed
        lines = processed_content.split("\n")
        if len(lines) > max_lines:
            processed_content = "\n".join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"

        return {
            "file_type": file_type.value,
            "content": processed_content,
            "original_length": len(content),
            "processed_length": len(processed_content),
            "file_path": str(file_path) if file_path else None,
        }

    def create_generation_context(
        self,
        event_description: str,
        existing_playbooks: Optional[list] = None,
        inventory_context: Optional[str] = None,
    ) -> str:
        """
        Create a context string for LLM playbook generation.

        Args:
            event_description: Description of the infrastructure event
            existing_playbooks: Optional list of existing playbook contexts
            inventory_context: Optional inventory information

        Returns:
            Formatted context string for LLM prompt
        """
        context_parts = [
            "# Ansible Playbook Generation Context\n",
            f"## Event Description\n{event_description}\n",
        ]

        if existing_playbooks:
            context_parts.append("\n## Existing Playbooks\n")
            for idx, pb in enumerate(existing_playbooks, 1):
                context_parts.append(f"### Playbook {idx}\n```yaml\n{pb}\n```\n")

        if inventory_context:
            context_parts.append(f"\n## Inventory Context\n{inventory_context}\n")

        return "\n".join(context_parts)
