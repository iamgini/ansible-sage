# Multi-Task Chaining Implementation

**Date**: 2026-06-02  
**Status**: ✅ Implemented

---

## Summary

Implemented **multi-task chaining** support following the Ansible Lightspeed pattern, allowing users to generate complex playbooks with multiple related tasks using ampersand (`&`) separator.

## Lightspeed Pattern

### Industry Standard
From Ansible Lightspeed documentation:

> "To request multitask code recommendations, enter a sequence of natural language task prompts in a YAML file comment separated by ampersand (&) symbols."

**Example**:
```yaml
# Install postgresql-server & Run postgresql-setup command & Start and enable postgresql service
```

**Result**: Single playbook with all three tasks in proper sequence.

---

## Implementation

### 1. Core Functions (`prompt_templates.py`)

#### `parse_multi_task_prompt(prompt: str) -> List[str]`
Splits ampersand-separated prompt into individual tasks.

```python
>>> parse_multi_task_prompt("Install nginx & Configure site & Start service")
['Install nginx', 'Configure site', 'Start service']

>>> parse_multi_task_prompt("Single task")
['Single task']
```

#### `is_multi_task_prompt(prompt: str) -> bool`
Detects if prompt contains multiple tasks.

```python
>>> is_multi_task_prompt("Install nginx & Start service")
True

>>> is_multi_task_prompt("Install nginx")
False
```

#### `format_multi_task_prompt(tasks: List[str], event_context: dict) -> str`
Generates optimized prompt for multi-task playbook.

**Output includes**:
- Numbered task list
- Event context (host, timestamp)
- Multi-task example pattern
- Task chaining guidance
- Variable sharing patterns

### 2. Request Parameter (`providers/base.py`)

Added `is_multi_task` flag to `GenerationRequest`:

```python
@dataclass
class GenerationRequest:
    ...
    is_multi_task: bool = False  # Flag for multi-task chaining
```

### 3. Provider Integration (`providers/claude.py`)

ClaudeProvider automatically detects and handles multi-task prompts:

```python
# Check if this is a multi-task prompt
if request.is_multi_task or is_multi_task_prompt(request.event_description):
    # Parse multiple tasks and format combined prompt
    tasks = parse_multi_task_prompt(request.event_description)
    event_context = {
        'host': request.host or 'target_host',
        'timestamp': request.constraints.get('timestamp', 'now') if request.constraints else 'now',
    }
    user_prompt = format_multi_task_prompt(tasks, event_context)
```

---

## Usage Examples

### Example 1: Database Setup
```json
{
  "event_description": "Install postgresql & Setup database & Create admin user & Start service",
  "host": "db-server-01"
}
```

**Generated Prompt** (excerpt):
```
Generate an Ansible playbook to perform multiple related tasks on db-server-01.

## Tasks Required
1. Install postgresql
2. Setup database
3. Create admin user
4. Start service

## Example Multi-Task Pattern
```yaml
- name: Multi-task automation
  hosts: db-server-01
  tasks:
    - name: Task 1 description
      ansible.builtin.package:
        name: required_package
        state: present
      register: install_result

    - name: Task 2 description (uses result from Task 1)
      when: install_result is succeeded
      register: config_result
```
```

### Example 2: Web Server Setup
```
"Install nginx & Configure virtual host & Deploy SSL certificate & Start and enable service"
```

**Parsed as**:
1. Install nginx
2. Configure virtual host
3. Deploy SSL certificate
4. Start and enable service

### Example 3: Disk Cleanup
```
"Check disk usage & Identify large files & Clean old logs & Verify space recovered"
```

**Parsed as**:
1. Check disk usage
2. Identify large files
3. Clean old logs
4. Verify space recovered

---

## Multi-Task Prompt Template

The generated prompt emphasizes:

### 1. Task Sequencing
```
## Requirements
1. Organize tasks in logical sequence
2. Use variables to share data between tasks
3. Register results from each task for use in subsequent tasks
```

### 2. Task Chaining Pattern
```yaml
# Task 1: Setup
- name: Install package
  register: install_result

# Task 2: Configure (uses Task 1 result)
- name: Configure service
  when: install_result is succeeded
  register: config_result

# Task 3: Start (depends on Task 2)
- name: Start service
  when: config_result is changed
```

### 3. Error Handling
```
- Group related tasks with block: when appropriate
- Include rollback steps in rescue: blocks
```

### 4. Verification
```
- Verify each task completed successfully before proceeding
- Include verification steps after critical tasks
```

---

## Testing

Created `test-scripts/test_multi_task.py`:

### Parse Tests ✅
- Single task: `"Install nginx"` → 1 task
- Three tasks: `"Install & Configure & Start"` → 3 tasks
- Four tasks: `"Install & Setup & Create & Start"` → 4 tasks
- Whitespace handling: `"  Install  &  Start  "` → cleaned properly

### Formatting Tests ✅
- Host context included
- Task count displayed
- Numbered task list
- Example pattern present
- YAML code block
- Task chaining (register/when)
- Error handling (block/rescue)

**All tests passing!**

---

## Benefits

### 1. Complex Workflows in One Request
**Before**: Need 4 separate events/requests
```json
Event 1: "Install postgresql"
Event 2: "Setup database"
Event 3: "Create user"
Event 4: "Start service"
```

**After**: Single multi-task request
```json
Event: "Install postgresql & Setup database & Create user & Start service"
```

### 2. Better Task Correlation
Multi-task prompt generates playbook with:
- Shared variables across tasks
- Result registration and reuse
- Proper conditional chaining
- Unified error handling

**Example**:
```yaml
vars:
  db_name: myapp_db
  db_user: myapp_user

tasks:
  - name: Install postgresql
    register: install_result

  - name: Setup {{ db_name }}
    when: install_result is succeeded
    register: setup_result

  - name: Create {{ db_user }}
    when: setup_result is succeeded
```

### 3. Logical Task Grouping
The LLM understands tasks are related and generates:
- Meaningful playbook name
- Grouped variable definitions
- Sequential verification steps
- Combined notification

---

## Comparison with Lightspeed

### Similarities ✅
- Ampersand (`&`) separator
- Multi-task in single playbook
- Context-aware generation
- Maintains task sequence

### Differences
| Feature | Lightspeed | Ansible Maya |
|---------|-----------|--------------|
| **Input** | YAML comment | Event description |
| **Context** | Current file | Event metadata |
| **Scope** | Single file | Full playbook |
| **Output** | Task snippets | Complete playbook |

### Our Enhancement
Sage adds:
- Event context integration
- Host-specific generation
- Timestamp tracking
- Constraint handling
- Multi-task example pattern in prompt

---

## Limitations & Future Work

### Current Limitations

1. **No Task Dependencies Specified**
   - User can't specify "Task 2 depends on Task 1"
   - LLM infers dependencies from task order

2. **All Tasks in One Play**
   - No support for multi-play playbooks
   - All tasks run on same host

3. **No Conditional Task Inclusion**
   - Can't specify "Only run Task 3 if Task 2 succeeds"
   - LLM must infer this from task descriptions

### Future Enhancements

1. **Explicit Dependencies**
   ```
   "Install nginx [dep: none] & Configure site [dep: Install nginx] & Start service [dep: Configure site]"
   ```

2. **Multi-Host Tasks**
   ```
   "Install nginx on web servers & Setup database on db servers & Configure load balancer"
   ```

3. **Conditional Branches**
   ```
   "Check disk space & If > 80% then Clean logs else Send notification"
   ```

4. **Parallel Tasks**
   ```
   "Install nginx || Install postgresql || Install redis"
   ```
   (Use `||` for parallel, `&` for sequential)

5. **Task Modifiers**
   ```
   "Install nginx [retry: 3] & Configure site [check: true] & Start service [notify: team]"
   ```

---

## Integration Example

### API Request
```python
from ansible_maya.core.providers.claude import ClaudeProvider
from ansible_maya.core.providers.base import GenerationRequest

provider = ClaudeProvider()

request = GenerationRequest(
    event_description="Install postgresql & Setup database & Create admin user & Start service",
    host="db-server-01.example.com",
    constraints={
        "database_name": "appdb",
        "admin_user": "dbadmin",
    },
    is_multi_task=True,  # Explicit flag (optional, auto-detected)
)

response = await provider.generate_playbook(request)
print(response.playbook)
```

### Generated Playbook (Example)
```yaml
---
- name: Database setup automation
  hosts: db-server-01.example.com
  become: yes
  gather_facts: yes

  vars:
    db_package: postgresql-server
    db_name: appdb
    admin_user: dbadmin

  tasks:
    - name: Install PostgreSQL
      ansible.builtin.package:
        name: "{{ db_package }}"
        state: present
      register: install_result

    - name: Initialize database
      ansible.builtin.command: postgresql-setup initdb
      when: install_result is changed
      register: init_result

    - name: Start PostgreSQL service
      ansible.builtin.service:
        name: postgresql
        state: started
        enabled: yes
      when: init_result is succeeded
      register: service_result

    - name: Create admin user
      community.postgresql.postgresql_user:
        name: "{{ admin_user }}"
        role_attr_flags: SUPERUSER
      when: service_result is succeeded

    - name: Create application database
      community.postgresql.postgresql_db:
        name: "{{ db_name }}"
        owner: "{{ admin_user }}"
      when: service_result is succeeded

    - name: Send completion notification
      ansible.builtin.debug:
        msg: "Database setup complete: {{ db_name }} owned by {{ admin_user }}"
```

---

## Documentation for Users

### How to Use Multi-Task Chaining

**Format**: Separate tasks with ampersand (`&`)

```
"Task 1 & Task 2 & Task 3"
```

**Examples**:

1. **Web Server Setup**
   ```
   "Install nginx & Configure site & Deploy SSL cert & Start service"
   ```

2. **Application Deployment**
   ```
   "Clone repository & Install dependencies & Build application & Start service"
   ```

3. **Monitoring Setup**
   ```
   "Install Prometheus & Configure targets & Setup Grafana & Import dashboards"
   ```

4. **Security Hardening**
   ```
   "Update packages & Configure firewall & Setup fail2ban & Enable SELinux"
   ```

**Best Practices**:
- ✅ Order tasks logically (setup → configure → start)
- ✅ Use clear task descriptions
- ✅ Keep tasks related (same component/workflow)
- ❌ Don't mix unrelated tasks
- ❌ Don't exceed 5-6 tasks (split into multiple requests)

---

## Conclusion

✅ **Multi-task chaining implemented** following Lightspeed pattern  
✅ **Automatic detection** via ampersand separator  
✅ **Optimized prompt** with task chaining guidance  
✅ **All tests passing**  

**Impact**: Users can now generate complex, multi-step playbooks with a single request, with proper task sequencing, variable sharing, and error handling.

---

## References

- Lightspeed docs: Multi-task code recommendations
- Analysis: `.claude/prompt-analysis.md`
- Tests: `test-scripts/test_multi_task.py`
