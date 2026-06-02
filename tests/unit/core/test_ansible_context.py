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

"""Tests for Ansible context processor."""

import pytest
from pathlib import Path

from sage.core.ansible_context import AnsibleContextProcessor, AnsibleFileType


@pytest.fixture
def context_processor():
    """Create AnsibleContextProcessor instance."""
    return AnsibleContextProcessor()


class TestFileTypeDetection:
    """Tests for file type detection."""

    def test_detect_playbook(self, context_processor):
        """Test playbook detection."""
        content = """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Test task
      ansible.builtin.debug:
        msg: "Hello"
"""
        file_type = context_processor.detect_file_type(content)
        assert file_type == AnsibleFileType.PLAYBOOK

    def test_detect_tasks_file(self, context_processor):
        """Test tasks file detection."""
        content = """---
- name: Install nginx
  ansible.builtin.package:
    name: nginx
    state: present

- name: Start nginx
  ansible.builtin.service:
    name: nginx
    state: started
"""
        file_type = context_processor.detect_file_type(content)
        assert file_type == AnsibleFileType.TASKS

    def test_detect_vars_file(self, context_processor):
        """Test vars file detection."""
        content = """---
nginx_port: 80
nginx_user: www-data
app_name: myapp
debug_mode: false
"""
        file_type = context_processor.detect_file_type(content)
        assert file_type == AnsibleFileType.VARS

    def test_detect_file_type_from_path(self, context_processor):
        """Test file type detection from path."""
        content = "# Some content"

        # Tasks file by path
        file_type = context_processor.detect_file_type(
            content, Path("/roles/myrole/tasks/main.yml")
        )
        assert file_type == AnsibleFileType.TASKS

        # Handlers file by path
        file_type = context_processor.detect_file_type(
            content, Path("/roles/myrole/handlers/main.yml")
        )
        assert file_type == AnsibleFileType.HANDLERS

        # Vars file by path
        file_type = context_processor.detect_file_type(
            content, Path("/group_vars/all.yml")
        )
        assert file_type == AnsibleFileType.VARS


class TestFQCNEnforcement:
    """Tests for FQCN enforcement."""

    def test_enforce_fqcn_for_builtin_modules(self, context_processor):
        """Test FQCN enforcement for builtin modules."""
        content = """- name: Test task
  debug:
    msg: "Hello"

- name: Copy file
  copy:
    src: file.txt
    dest: /tmp/file.txt
"""
        result = context_processor.enforce_fqcn(content)

        assert "ansible.builtin.debug:" in result
        assert "ansible.builtin.copy:" in result
        assert "debug:" not in result or "  debug:" not in result

    def test_skip_fqcn_for_already_qualified_modules(self, context_processor):
        """Test that already-qualified modules are not modified."""
        content = """- name: Test task
  ansible.builtin.debug:
    msg: "Hello"

- name: Install package
  ansible.builtin.package:
    name: nginx
"""
        result = context_processor.enforce_fqcn(content)
        assert result == content

    def test_skip_comments_and_empty_lines(self, context_processor):
        """Test that comments and empty lines are preserved."""
        content = """# This is a comment
- name: Test task
  debug:
    msg: "Hello"

# Another comment
- name: Another task
  copy:
    src: test
    dest: /tmp/test
"""
        result = context_processor.enforce_fqcn(content)

        assert "# This is a comment" in result
        assert "# Another comment" in result


class TestYAMLNormalization:
    """Tests for YAML normalization."""

    def test_normalize_yaml_removes_excessive_whitespace(self, context_processor):
        """Test YAML normalization."""
        content = """


- name: Test task
  debug:
    msg: "Hello"


- name: Another task
  copy:
    src: test
    dest: /tmp/test


"""
        result = context_processor.normalize_yaml_for_llm(content)

        # Should not start or end with empty lines
        assert not result.startswith("\n\n")
        assert not result.endswith("\n\n")

        # Should have consistent spacing
        lines = result.split("\n")
        assert len([l for l in lines if not l.strip()]) < 3  # Few empty lines


class TestContextExtraction:
    """Tests for context extraction."""

    def test_extract_context_basic(self, context_processor):
        """Test basic context extraction."""
        content = """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Test task
      ansible.builtin.debug:
        msg: "Hello"
"""
        context = context_processor.extract_context(content)

        assert context["file_type"] == AnsibleFileType.PLAYBOOK.value
        assert "ansible.builtin.debug" in context["content"]
        assert context["original_length"] > 0
        assert context["processed_length"] > 0

    def test_extract_context_truncates_long_content(self, context_processor):
        """Test that long content is truncated."""
        # Create content with > 100 lines
        lines = ["- name: Task {}".format(i) for i in range(150)]
        content = "\n".join(lines)

        context = context_processor.extract_context(content, max_lines=100)

        assert "more lines" in context["content"]


class TestGenerationContext:
    """Tests for generation context creation."""

    def test_create_generation_context_basic(self, context_processor):
        """Test basic generation context creation."""
        context = context_processor.create_generation_context(
            event_description="Disk is full on /var",
        )

        assert "Disk is full on /var" in context
        assert "Event Description" in context

    def test_create_generation_context_with_existing_playbooks(self, context_processor):
        """Test generation context with existing playbooks."""
        existing = [
            "- name: Clean logs\n  file: path=/var/log/old state=absent",
        ]

        context = context_processor.create_generation_context(
            event_description="Disk is full",
            existing_playbooks=existing,
        )

        assert "Existing Playbooks" in context
        assert "Clean logs" in context

    def test_create_generation_context_with_inventory(self, context_processor):
        """Test generation context with inventory info."""
        context = context_processor.create_generation_context(
            event_description="Disk is full",
            inventory_context="web_servers:\n  - web01\n  - web02",
        )

        assert "Inventory Context" in context
        assert "web_servers" in context
