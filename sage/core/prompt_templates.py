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

"""
Ansible Prompt Templates for LLM Generation.

Ported from vscode-ansible constants.ts - specialized prompts for Ansible context.
"""

# Base system prompt for Ansible playbook generation
ANSIBLE_SYSTEM_PROMPT = """You are an expert Ansible automation engineer specialized in generating production-ready playbooks.

## Core Principles

1. **FQCN (Fully Qualified Collection Names)**: Always use FQCN for modules
   - ✓ ansible.builtin.copy, ansible.builtin.service, community.general.docker_container
   - ✗ copy, service, docker_container

2. **Idempotency**: All tasks must be idempotent (safe to run multiple times)
   - Use `state: present/absent` instead of creating/deleting
   - Check before changing with `stat` or `command` when needed
   - Use `creates` parameter for command/shell modules

3. **Error Handling**: Include proper error handling
   - Use `failed_when`, `ignore_errors`, or `block/rescue` appropriately
   - Add meaningful failure messages
   - Use `check_mode: yes` for dry-run support

4. **Naming**: Provide descriptive task names
   - Start with capital letter
   - Use imperative mood ("Install nginx", not "Installing nginx")
   - Be specific ("Install nginx 1.20" not "Install package")

5. **Security Best Practices**
   - Never hardcode credentials - use variables or vault
   - Set proper file permissions (mode parameter)
   - Use `become` only when necessary
   - Validate inputs with `assert`

6. **Variables**: Use variables for configuration
   - Define variables with defaults
   - Use descriptive variable names (snake_case)
   - Group related variables

## Output Format

Generate ONLY valid Ansible playbook YAML. Do not include:
- Markdown code fences (no ```yaml)
- Explanatory text before or after the playbook
- Comments about what you're doing

Start directly with the playbook YAML (either `---` or `- name:`).

## Example Structure

```yaml
---
- name: Descriptive playbook name
  hosts: target_hosts
  become: yes
  vars:
    config_var: default_value

  tasks:
    - name: Task description
      ansible.builtin.module_name:
        parameter: value
      when: condition
      register: result

    - name: Handle errors
      block:
        - name: Risky operation
          ansible.builtin.command: some_command
      rescue:
        - name: Handle failure
          ansible.builtin.debug:
            msg: "Operation failed, handling gracefully"
```

## Common Patterns

### File Operations
```yaml
- name: Copy configuration file
  ansible.builtin.copy:
    src: files/app.conf
    dest: /etc/app/app.conf
    owner: root
    group: root
    mode: '0644'
    backup: yes
  notify: Restart application
```

### Service Management
```yaml
- name: Ensure service is running
  ansible.builtin.systemd:
    name: nginx
    state: started
    enabled: yes
```

### Package Installation
```yaml
- name: Install required packages
  ansible.builtin.package:
    name:
      - nginx
      - python3-pip
    state: present
```

### Disk Space Cleanup
```yaml
- name: Check disk usage
  ansible.builtin.shell: df -h / | tail -n 1 | awk '{print $5}' | sed 's/%//'
  register: disk_usage
  changed_when: false

- name: Clean package cache when disk usage high
  ansible.builtin.command: apt clean
  when: disk_usage.stdout | int > 80
```

Remember: Generate production-ready, secure, idempotent playbooks following Ansible best practices.
"""

# Event-specific prompt templates

EVENT_DISK_FULL_PROMPT = """Generate an Ansible playbook to remediate disk space issues on {host}.

## Event Details
- Host: {host}
- Disk usage: {usage}%
- Mount point: {mount_point}
- Event timestamp: {timestamp}

## Requirements
1. Check current disk usage
2. Identify large files/directories (e.g., logs, tmp, package cache)
3. Clean up safely (rotate logs, clean package cache, remove old files)
4. Avoid deleting user data
5. Send notification after cleanup
6. Verify disk usage improved

Include proper checks and safety measures (e.g., don't delete if usage < 80%).
"""

EVENT_SERVICE_DOWN_PROMPT = """Generate an Ansible playbook to remediate service failure on {host}.

## Event Details
- Host: {host}
- Service: {service}
- Status: {status}
- Event timestamp: {timestamp}

## Requirements
1. Check service status
2. Check service logs for errors
3. Attempt to restart service
4. Verify service is running after restart
5. Enable service to start on boot
6. If restart fails, escalate (send alert)

Include error handling and notifications.
"""

EVENT_HIGH_CPU_PROMPT = """Generate an Ansible playbook to investigate and remediate high CPU usage on {host}.

## Event Details
- Host: {host}
- CPU usage: {cpu_percent}%
- Duration: {duration}
- Event timestamp: {timestamp}

## Requirements
1. Identify top CPU-consuming processes
2. Check if known service is causing it
3. Collect diagnostic data (ps, top output)
4. Optionally restart misbehaving service (with approval)
5. Send diagnostic report

Be cautious - don't automatically kill processes without verification.
"""

EVENT_MEMORY_HIGH_PROMPT = """Generate an Ansible playbook to investigate and remediate high memory usage on {host}.

## Event Details
- Host: {host}
- Memory usage: {memory_percent}%
- Available memory: {available_mb}MB
- Event timestamp: {timestamp}

## Requirements
1. Check memory usage (free -m)
2. Identify memory-consuming processes
3. Check for memory leaks (review logs)
4. Clear caches if appropriate (drop_caches)
5. Restart problematic service if identified
6. Send diagnostic report

Include safety checks (don't clear caches on database servers, etc.).
"""

EVENT_GENERIC_PROMPT = """Generate an Ansible playbook to address the following infrastructure event:

## Event Description
{event_description}

## Host Information
- Host: {host}
- Event type: {event_type}
- Event timestamp: {timestamp}

## Additional Context
{additional_context}

## Requirements
1. Investigate the issue
2. Collect relevant diagnostic data
3. Remediate if possible
4. Include error handling
5. Send notification with results

Follow Ansible best practices and ensure idempotency.
"""

# Refinement prompts for iterative improvement

REFINE_PLAYBOOK_PROMPT = """The generated Ansible playbook has issues that need to be fixed.

## Original Playbook
```yaml
{original_playbook}
```

## Issues Found
{issues}

## Requirements
Generate a corrected version of the playbook that:
1. Fixes all identified issues
2. Maintains the original functionality
3. Follows Ansible best practices
4. Uses FQCN for all modules

Output only the corrected YAML playbook, no explanations.
"""

ADD_ERROR_HANDLING_PROMPT = """Enhance the following Ansible playbook with better error handling.

## Current Playbook
```yaml
{playbook}
```

## Requirements
Add appropriate error handling:
1. Use block/rescue for operations that might fail
2. Add failed_when conditions where appropriate
3. Include retry logic for network operations
4. Add meaningful error messages
5. Ensure failures are reported clearly

Output only the enhanced YAML playbook.
"""

ADD_MOLECULE_TEST_PROMPT = """Generate a Molecule test scenario for the following Ansible playbook.

## Playbook
```yaml
{playbook}
```

## Requirements
Create a complete Molecule scenario including:
1. molecule.yml configuration
2. converge.yml (the playbook)
3. verify.yml (test assertions)
4. requirements.yml (if needed)

Test should verify:
- Playbook runs successfully
- Expected changes are made
- Idempotency (second run makes no changes)
- Services are running if applicable

Output the Molecule scenario structure.
"""

# Helper function to format prompts


def format_event_prompt(
    event_type: str,
    host: str = "target_host",
    timestamp: str = "now",
    **kwargs,
) -> str:
    """
    Format event-specific prompt with parameters.

    Args:
        event_type: Type of event (disk_full, service_down, etc.)
        host: Target host
        timestamp: Event timestamp
        **kwargs: Additional event-specific parameters

    Returns:
        Formatted prompt string
    """
    prompts = {
        "disk_full": EVENT_DISK_FULL_PROMPT,
        "disk_space": EVENT_DISK_FULL_PROMPT,
        "service_down": EVENT_SERVICE_DOWN_PROMPT,
        "service_stopped": EVENT_SERVICE_DOWN_PROMPT,
        "high_cpu": EVENT_HIGH_CPU_PROMPT,
        "cpu_usage": EVENT_HIGH_CPU_PROMPT,
        "high_memory": EVENT_MEMORY_HIGH_PROMPT,
        "memory_usage": EVENT_MEMORY_HIGH_PROMPT,
    }

    template = prompts.get(event_type, EVENT_GENERIC_PROMPT)

    # Build parameters
    params = {
        "host": host,
        "timestamp": timestamp,
        **kwargs,
    }

    # Add defaults for required fields
    if event_type in ["disk_full", "disk_space"]:
        params.setdefault("usage", "85")
        params.setdefault("mount_point", "/")

    if event_type in ["service_down", "service_stopped"]:
        params.setdefault("service", "unknown")
        params.setdefault("status", "inactive")

    if event_type in ["high_cpu", "cpu_usage"]:
        params.setdefault("cpu_percent", "90")
        params.setdefault("duration", "5m")

    if event_type in ["high_memory", "memory_usage"]:
        params.setdefault("memory_percent", "90")
        params.setdefault("available_mb", "100")

    # For generic events
    if event_type not in prompts:
        params.setdefault("event_type", event_type)
        params.setdefault("event_description", "Infrastructure event detected")
        params.setdefault("additional_context", "No additional context provided")

    try:
        return template.format(**params)
    except KeyError as e:
        # If template has missing keys, fall back to generic
        params["event_description"] = f"Event type: {event_type}"
        params["event_type"] = event_type
        params["additional_context"] = str(kwargs)
        return EVENT_GENERIC_PROMPT.format(**params)


# Validation prompts

ANSIBLE_LINT_FIX_PROMPT = """The following Ansible playbook has linting issues.

## Playbook
```yaml
{playbook}
```

## Linting Issues
{lint_issues}

Fix these issues while maintaining functionality. Output only the corrected YAML.
"""


def get_system_prompt() -> str:
    """Get the base Ansible system prompt."""
    return ANSIBLE_SYSTEM_PROMPT


def get_event_prompt(event_type: str, **kwargs) -> str:
    """
    Get formatted prompt for specific event type.

    Args:
        event_type: Type of infrastructure event
        **kwargs: Event-specific parameters

    Returns:
        Formatted prompt string
    """
    return format_event_prompt(event_type, **kwargs)
