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
Ansible Prompt Templates for LLM Generation.

Ported from vscode-ansible constants.ts - specialized prompts for Ansible context.
"""

from typing import List

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
1. Check current disk usage with appropriate commands
2. Identify large files/directories using standard tools
3. Clean up safely based on common patterns (logs, caches, temporary files)
4. Implement safety checks before any destructive operations
5. Verify the remediation was successful
6. Send notification with results

## Example Pattern
```yaml
- name: Remediate disk space on /var
  hosts: target_host
  become: yes
  vars:
    threshold_percent: 80
  tasks:
    - name: Check current disk usage
      ansible.builtin.shell: df {{ mount_point }} | tail -1 | awk '{{print $5}}' | sed 's/%//'
      register: current_usage
      changed_when: false

    - name: Clean package cache
      ansible.builtin.package:
        clean: yes
      when: current_usage.stdout | int > threshold_percent

    - name: Verify disk usage improved
      ansible.builtin.shell: df {{ mount_point }} | tail -1 | awk '{{print $5}}' | sed 's/%//'
      register: final_usage
      changed_when: false
```

## General Patterns to Follow
- Use conditional checks (when:) to ensure tasks only run when needed
- Implement proper error handling with block/rescue
- Register results for verification steps
- Use appropriate modules for the detected OS/distribution
- Ensure all operations are idempotent
"""

EVENT_SERVICE_DOWN_PROMPT = """Generate an Ansible playbook to remediate service failure on {host}.

## Event Details
- Host: {host}
- Service: {service}
- Status: {status}
- Event timestamp: {timestamp}

## Requirements
1. Gather current service status using appropriate service management tools
2. Collect diagnostic information from logs and system state
3. Check for common failure conditions (ports, permissions, dependencies, configuration)
4. Attempt service restart with appropriate retry logic
5. Verify service health after restart
6. Ensure service persistence across reboots
7. Send notification with outcome

## Example Pattern
```yaml
- name: Remediate service failure
  hosts: target_host
  become: yes
  tasks:
    - name: Gather service facts
      ansible.builtin.service_facts:

    - name: Check service status
      ansible.builtin.service:
        name: "{{ service_name }}"
        state: started
      register: service_result
      ignore_errors: yes

    - name: Restart service if needed
      block:
        - name: Stop service
          ansible.builtin.service:
            name: "{{ service_name }}"
            state: stopped

        - name: Start service
          ansible.builtin.service:
            name: "{{ service_name }}"
            state: started
            enabled: yes
      rescue:
        - name: Send failure notification
          ansible.builtin.debug:
            msg: "Failed to restart {{ service_name }}, manual intervention required"
```

## General Patterns to Follow
- Detect and use the appropriate service manager (systemd, sysvinit, etc.)
- Implement retry logic with exponential backoff where appropriate
- Collect relevant diagnostics before attempting fixes
- Use block/rescue to handle restart failures gracefully
- Verify both process state and functional health (ports, endpoints)
- Include rollback steps if remediation fails
"""

EVENT_HIGH_CPU_PROMPT = """Generate an Ansible playbook to investigate and remediate high CPU usage on {host}.

## Event Details
- Host: {host}
- CPU usage: {cpu_percent}%
- Duration: {duration}
- Event timestamp: {timestamp}

## Requirements
1. Collect system performance metrics and process information
2. Identify resource-intensive processes and patterns
3. Gather relevant diagnostic data for analysis
4. Determine appropriate remediation based on findings
5. Implement corrective actions with safety checks
6. Verify system state after remediation
7. Send comprehensive diagnostic report

## Example Pattern
```yaml
- name: Investigate high CPU usage
  hosts: target_host
  become: yes
  tasks:
    - name: Collect CPU metrics
      ansible.builtin.shell: top -bn1 | head -20
      register: cpu_snapshot
      changed_when: false

    - name: Identify top processes
      ansible.builtin.shell: ps aux --sort=-%cpu | head -10
      register: top_processes
      changed_when: false

    - name: Check if remediation needed
      ansible.builtin.set_fact:
        high_cpu_threshold: 80

    - name: Take action if threshold exceeded
      block:
        - name: Restart identified service
          ansible.builtin.service:
            name: "{{ identified_service }}"
            state: restarted
          when: identified_service is defined
      rescue:
        - name: Log for manual review
          ansible.builtin.debug:
            msg: "CPU issue requires manual intervention. Top processes: {{ top_processes.stdout }}"
```

## General Patterns to Follow
- Use multiple diagnostic tools to cross-verify findings
- Implement threshold checks before taking action
- Prefer service restarts over process termination
- Collect data before and after remediation for comparison
- Use conditional logic to handle different scenarios
- Include manual intervention triggers for uncertain cases
"""

EVENT_MEMORY_HIGH_PROMPT = """Generate an Ansible playbook to investigate and remediate high memory usage on {host}.

## Event Details
- Host: {host}
- Memory usage: {memory_percent}%
- Available memory: {available_mb}MB
- Event timestamp: {timestamp}

## Requirements
1. Gather comprehensive memory utilization metrics
2. Identify processes and services consuming memory
3. Analyze for potential memory leaks or unusual patterns
4. Determine safe remediation strategies based on system role
5. Implement appropriate corrective actions
6. Verify memory state after remediation
7. Send diagnostic report with findings

## Example Pattern
```yaml
- name: Investigate high memory usage
  hosts: target_host
  become: yes
  tasks:
    - name: Check memory usage
      ansible.builtin.command: free -m
      register: memory_before
      changed_when: false

    - name: Identify memory-consuming processes
      ansible.builtin.shell: ps aux --sort=-%mem | head -10
      register: memory_hogs
      changed_when: false

    - name: Clear system caches if safe
      ansible.builtin.shell: sync && echo 3 > /proc/sys/vm/drop_caches
      when:
        - memory_percent | int > 85
        - "'database' not in group_names"
      register: cache_clear

    - name: Verify memory improved
      ansible.builtin.command: free -m
      register: memory_after
      changed_when: false
      when: cache_clear is changed

    - name: Send diagnostic report
      ansible.builtin.debug:
        msg:
          - "Before: {{ memory_before.stdout }}"
          - "Top consumers: {{ memory_hogs.stdout_lines[:5] }}"
          - "After: {{ memory_after.stdout | default('N/A') }}"
```

## General Patterns to Follow
- Consider system role when selecting remediation strategies
- Implement safety checks before memory operations
- Use graduated approach (cache clearing → service restart → escalation)
- Collect before/after metrics for validation
- Include thresholds to prevent over-correction
- Handle different scenarios (application leak vs system cache)
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
1. Analyze the event and determine appropriate investigation steps
2. Collect comprehensive diagnostic data
3. Identify root cause or contributing factors
4. Implement remediation if safe and appropriate
5. Verify the fix and validate system state
6. Send detailed notification with findings and actions taken

## Example Pattern
```yaml
- name: Remediate infrastructure event
  hosts: target_host
  become: yes
  gather_facts: yes
  tasks:
    - name: Investigate issue
      block:
        - name: Gather system state
          ansible.builtin.setup:

        - name: Collect diagnostics
          ansible.builtin.command: relevant_diagnostic_command
          register: diagnostic_data
          changed_when: false

        - name: Analyze and remediate
          ansible.builtin.service:
            name: affected_service
            state: restarted
          when: remediation_needed | default(false)

      rescue:
        - name: Handle failure
          ansible.builtin.debug:
            msg: "Remediation failed, escalating to manual intervention"

      always:
        - name: Send notification
          ansible.builtin.debug:
            msg: "Event processed: {{ event_type }} on {{ inventory_hostname }}"
```

## General Patterns to Follow
- Use fact gathering to adapt to the target system environment
- Implement progressive remediation (investigate → fix → verify)
- Include safety checks and rollback capabilities
- Use block/rescue/always for proper error handling
- Make all tasks idempotent and repeatable
- Register results and use them in subsequent tasks
- Provide clear task names describing what and why
- Include both success and failure notification paths
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


# Temperature tuning by event complexity
TEMPERATURE_BY_EVENT = {
    'disk_full': 0.2,        # Well-defined problem, deterministic solution
    'disk_space': 0.2,       # Same as disk_full
    'service_down': 0.3,     # Some variation needed for different services
    'service_stopped': 0.3,  # Same as service_down
    'high_cpu': 0.5,         # Investigative, needs more creativity
    'cpu_usage': 0.5,        # Same as high_cpu
    'high_memory': 0.4,      # Investigative but more constrained than CPU
    'memory_usage': 0.4,     # Same as high_memory
    'generic': 0.3,          # Balanced default
}


def get_optimal_temperature(event_type: str, is_refinement: bool = False) -> float:
    """
    Get optimal temperature for event type and operation.

    Args:
        event_type: Type of infrastructure event
        is_refinement: Whether this is a refinement operation (more focused)

    Returns:
        Optimal temperature value (0.0-1.0)
    """
    base_temp = TEMPERATURE_BY_EVENT.get(event_type, 0.3)
    # Refinement should be more focused (lower temperature)
    return base_temp * 0.7 if is_refinement else base_temp


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


# Multi-task chaining support (Lightspeed pattern)

def parse_multi_task_prompt(prompt: str) -> List[str]:
    """
    Parse ampersand-separated multi-task prompts.

    Follows Ansible Lightspeed pattern:
    "Install postgresql & Setup database & Start service"

    Args:
        prompt: User prompt, potentially with multiple tasks separated by '&'

    Returns:
        List of individual task descriptions

    Examples:
        >>> parse_multi_task_prompt("Install nginx")
        ['Install nginx']

        >>> parse_multi_task_prompt("Install nginx & Configure site & Start service")
        ['Install nginx', 'Configure site', 'Start service']
    """
    if '&' not in prompt:
        return [prompt.strip()]

    # Split by ampersand and clean up whitespace
    tasks = [task.strip() for task in prompt.split('&')]

    # Filter out empty tasks
    return [task for task in tasks if task]


def format_multi_task_prompt(tasks: List[str], event_context: dict = None) -> str:
    """
    Format multiple tasks into a single playbook generation prompt.

    Args:
        tasks: List of task descriptions
        event_context: Optional event context (host, timestamp, etc.)

    Returns:
        Formatted prompt for multi-task playbook generation

    Examples:
        >>> tasks = ['Install postgresql', 'Setup database', 'Start service']
        >>> format_multi_task_prompt(tasks)
        "Generate an Ansible playbook with the following tasks:
        1. Install postgresql
        2. Setup database
        3. Start service
        ..."
    """
    context = event_context or {}
    host = context.get('host', 'target_host')
    timestamp = context.get('timestamp', 'now')

    prompt = f"""Generate an Ansible playbook to perform multiple related tasks on {host}.

## Tasks Required
"""

    # Add numbered task list
    for idx, task in enumerate(tasks, 1):
        prompt += f"{idx}. {task}\n"

    prompt += f"""
## Event Context
- Host: {host}
- Timestamp: {timestamp}
- Task sequence: {len(tasks)} related tasks

## Requirements
1. Organize tasks in logical sequence
2. Use variables to share data between tasks
3. Register results from each task for use in subsequent tasks
4. Include verification steps after critical tasks
5. Implement proper error handling with block/rescue
6. Ensure idempotency across all tasks
7. Add meaningful task names and descriptions

## Example Multi-Task Pattern
```yaml
- name: Multi-task automation
  hosts: {host}
  become: yes
  gather_facts: yes

  vars:
    component_name: example

  tasks:
    # Task 1: Setup
    - name: Task 1 description
      ansible.builtin.package:
        name: required_package
        state: present
      register: install_result

    # Task 2: Configure (uses result from Task 1)
    - name: Task 2 description
      ansible.builtin.template:
        src: config.j2
        dest: /etc/config.conf
      when: install_result is succeeded
      register: config_result

    # Task 3: Start (depends on Task 2)
    - name: Task 3 description
      ansible.builtin.service:
        name: service_name
        state: started
        enabled: yes
      when: config_result is changed
```

## General Patterns to Follow
- Chain tasks using registered variables and when: conditions
- Verify each task completed successfully before proceeding
- Use meaningful variable names that describe the data
- Group related tasks with block: when appropriate
- Add comments between task groups for clarity
- Include rollback steps in rescue: blocks
"""

    return prompt


def is_multi_task_prompt(prompt: str) -> bool:
    """
    Check if a prompt contains multiple tasks.

    Args:
        prompt: User prompt to check

    Returns:
        True if prompt contains multiple tasks (ampersand separator)

    Examples:
        >>> is_multi_task_prompt("Install nginx")
        False

        >>> is_multi_task_prompt("Install nginx & Start service")
        True
    """
    return '&' in prompt
