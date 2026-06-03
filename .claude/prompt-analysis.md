# Ansible Maya Prompt Engineering Analysis

**Date**: 2026-06-02  
**Analysis Focus**: Comparing Ansible Maya prompting with industry best practices from Ansible Lightspeed

---

## Current State: Ansible Maya Prompting

### Strengths

1. **Strong System Prompt** (`prompt_templates.py:22-139`)
   - ✅ Emphasizes FQCN (Fully Qualified Collection Names)
   - ✅ Enforces idempotency patterns
   - ✅ Includes error handling guidance
   - ✅ Security best practices (no hardcoded credentials)
   - ✅ Provides concrete examples for common patterns
   - ✅ Clear output format instructions (no markdown fences)

2. **Event-Specific Templates**
   - ✅ Structured prompts for disk_full, service_down, high_cpu, high_memory
   - ✅ Includes event metadata in prompts
   - ✅ Safety measures (e.g., "don't delete if usage < 80%")
   - ✅ Clear requirements lists

3. **Context Processing** (`ansible_context.py`)
   - ✅ File type detection (playbook, tasks, vars, etc.)
   - ✅ FQCN enforcement
   - ✅ YAML normalization for LLM consumption
   - ✅ Context extraction with truncation

---

## Gaps vs. Ansible Lightspeed Best Practices

### 1. **Missing: Multi-Task Chaining**

**Industry Standard (Lightspeed)**:
```yaml
# Install postgresql-server & Run postgresql-setup command & Start and enable postgresql service
```

**Current Sage**: Only supports single event → single playbook generation

**Impact**: Users cannot generate complex playbooks with multiple related remediation steps in one prompt

**Recommendation**: Add multi-task prompt parsing
```python
def parse_multi_task_prompt(prompt: str) -> list[str]:
    """Parse ampersand-separated multi-task prompts."""
    if '&' in prompt:
        return [task.strip() for task in prompt.split('&')]
    return [prompt]
```

---

### 2. **Missing: Context Awareness Across File**

**Industry Standard (Lightspeed)**:
> "The entire contents of the file before the cursor position are used as context by the model"

**Current Sage**: Limited context from event description only

**What's Missing**:
- No awareness of previously generated playbooks in the session
- No correlation between multiple remediation attempts
- No playbook continuation pattern

**Example Use Case**:
```
Event 1: High CPU → generates process investigation playbook
Event 2: Same host, service identified → should correlate with Event 1's findings
```

**Recommendation**: Implement session-based context accumulation
```python
class SessionContext:
    def __init__(self):
        self.event_history = []
        self.playbook_history = []
    
    def add_event(self, event, playbook):
        self.event_history.append(event)
        self.playbook_history.append(playbook)
    
    def get_related_context(self, current_event):
        """Find previous events for same host/service."""
        return [e for e in self.event_history 
                if e['host'] == current_event['host']]
```

---

### 3. **Prompt Specificity: Good but Could Be Better**

**Lightspeed Guidelines**:
- ✅ "Create a user named deploy with sudo access and SSH key" (EXCELLENT)
- ❌ "Install package" (TOO VAGUE)

**Current Sage Event Prompts**: Moderately specific

**Example - Current**:
```python
EVENT_SERVICE_DOWN_PROMPT = """Generate an Ansible playbook to remediate service failure on {host}.
## Requirements
1. Check service status
2. Check service logs for errors
...
"""
```

**Could Be Enhanced To**:
```python
EVENT_SERVICE_DOWN_PROMPT = """Generate an Ansible playbook to remediate {service} service failure on {host}.

## Specific Requirements
1. Use 'systemctl status {service}' to check current service state
2. Extract last 50 lines from journal: 'journalctl -u {service} -n 50'
3. Check for common failure patterns:
   - Port conflicts (netstat/ss)
   - Permission issues (check service user)
   - Configuration errors (validate config if applicable)
4. Attempt restart with exponential backoff: 3 attempts, 5s/10s/20s delays
5. If service has dependencies (database, cache), verify those are running first
6. After successful restart, run health check endpoint if {service} is web service
7. Send notification with:
   - Service name and host
   - Downtime duration
   - Root cause from logs (if identifiable)
   - Recovery status (success/failed/manual intervention needed)

## Service-Specific Patterns
{service_specific_guidance}
"""
```

**Recommendation**: Add service-type-specific sub-templates
```python
SERVICE_PATTERNS = {
    'nginx': "Check nginx -t config, verify ports 80/443",
    'postgresql': "Check /var/lib/pgsql/data/postgresql.conf, verify port 5432",
    'redis': "Check /etc/redis/redis.conf, verify port 6379",
    # ... more services
}
```

---

### 4. **Missing: Prompt Refinement Feedback Loop**

**Industry Pattern**: Lightspeed allows users to accept/reject/modify suggestions

**Current Sage**: 
- ✅ Has `REFINE_PLAYBOOK_PROMPT` template
- ✅ Has `refine_playbook()` method in ClaudeProvider
- ❌ No automated feedback collection
- ❌ No prompt quality scoring

**Recommendation**: Add prompt effectiveness tracking
```python
class PromptMetrics:
    def __init__(self):
        self.prompt_success_rate = {}
    
    def record_outcome(self, event_type, prompt_hash, validation_passed, user_modified):
        """Track which prompts produce valid playbooks."""
        key = f"{event_type}:{prompt_hash}"
        if key not in self.prompt_success_rate:
            self.prompt_success_rate[key] = {
                'total': 0, 'valid': 0, 'user_modified': 0
            }
        self.prompt_success_rate[key]['total'] += 1
        if validation_passed:
            self.prompt_success_rate[key]['valid'] += 1
        if user_modified:
            self.prompt_success_rate[key]['user_modified'] += 1
```

---

### 5. **Output Format: Good but Add Structured Output**

**Current Sage**: Text-based YAML output

**Enhancement**: Use Claude's structured output for guaranteed validity

**Current Pattern**:
```python
response = await self.async_client.messages.create(
    model=model,
    max_tokens=request.max_tokens,
    system=system_prompt,
    messages=[{"role": "user", "content": user_prompt}],
)
raw_playbook = response.content[0].text
```

**Enhanced Pattern**:
```python
# Define JSON schema for playbook structure
PLAYBOOK_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "hosts": {"type": "string"},
        "become": {"type": "boolean"},
        "vars": {"type": "object"},
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "module": {"type": "string", "pattern": "^[a-z_]+\\.[a-z_]+\\.[a-z_]+$"},  # FQCN
                    "args": {"type": "object"},
                    "when": {"type": "string"},
                    "register": {"type": "string"}
                },
                "required": ["name"]
            }
        }
    },
    "required": ["name", "hosts", "tasks"]
}

# Use extended thinking mode for complex playbooks
response = await self.async_client.messages.create(
    model=model,
    max_tokens=request.max_tokens,
    thinking={
        "type": "enabled",
        "budget_tokens": 1000
    },
    system=system_prompt,
    messages=[{"role": "user", "content": user_prompt}],
)
```

---

### 6. **Missing: Example-Based Prompting (Few-Shot Learning)**

**Industry Pattern**: Provide examples in the prompt for better results

**Current Sage**: Has examples in system prompt, but not event-specific

**Recommendation**: Add few-shot examples per event type

```python
EVENT_DISK_FULL_EXAMPLES = """
## Example 1: /var/log cleanup
Input: "Disk usage at 92% on /var/log"
Output playbook:
```yaml
- name: Remediate disk space on /var/log
  hosts: "{{ target_host }}"
  become: yes
  tasks:
    - name: Rotate logs using logrotate
      ansible.builtin.command: /usr/sbin/logrotate -f /etc/logrotate.conf
    
    - name: Remove logs older than 30 days
      ansible.builtin.find:
        paths: /var/log
        age: 30d
        recurse: yes
      register: old_logs
    
    - name: Delete old log files
      ansible.builtin.file:
        path: "{{ item.path }}"
        state: absent
      loop: "{{ old_logs.files }}"
      when: old_logs.matched > 0
```

## Example 2: Package cache cleanup
Input: "Disk usage at 88% on / partition, server is Ubuntu"
Output playbook:
```yaml
- name: Clean package cache on Ubuntu
  hosts: "{{ target_host }}"
  become: yes
  tasks:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: yes
    
    - name: Clean apt cache
      ansible.builtin.apt:
        autoclean: yes
        autoremove: yes
```

Now generate a playbook for: {event_description}
"""
```

---

### 7. **Temperature Settings: Not Optimized**

**Current Claude Provider**:
```python
temperature=request.temperature  # Default likely 0.7-1.0
```

**Lightspeed Pattern**: Lower temperature for code generation (more deterministic)

**Recommendation**: Event-specific temperature tuning
```python
TEMPERATURE_BY_COMPLEXITY = {
    'disk_full': 0.2,        # Well-defined problem, deterministic solution
    'service_down': 0.3,     # Some variation needed for different services
    'high_cpu': 0.5,         # Investigative, needs more creativity
    'generic': 0.4,          # Balanced
}

def get_optimal_temperature(event_type: str, is_refinement: bool = False) -> float:
    """Get optimal temperature for event type."""
    base_temp = TEMPERATURE_BY_COMPLEXITY.get(event_type, 0.4)
    # Refinement should be more focused
    return base_temp * 0.8 if is_refinement else base_temp
```

---

## Recommended Improvements (Priority Order)

### Priority 1: Immediate Impact
1. **Add service-specific patterns** to event prompts
2. **Lower temperature** for code generation (0.2-0.4)
3. **Add few-shot examples** to event templates

### Priority 2: Medium-Term
4. **Implement multi-task chaining** (parse `&` separated prompts)
5. **Add session context** for related events
6. **Track prompt effectiveness** metrics

### Priority 3: Future Enhancement
7. **Structured output schema** for guaranteed validity
8. **Extended thinking mode** for complex playbooks
9. **Automated prompt refinement** based on validation failures

---

## Implementation Plan

### Phase 1: Enhance Existing Prompts (1-2 hours)
- Add service-specific guidance to `EVENT_SERVICE_DOWN_PROMPT`
- Add few-shot examples to all event prompts
- Adjust default temperature in ClaudeProvider to 0.3

### Phase 2: Multi-Task Support (2-3 hours)
- Add `parse_multi_task_prompt()` to prompt_templates.py
- Update ClaudeProvider to handle multi-task requests
- Add tests for multi-task parsing

### Phase 3: Session Context (3-4 hours)
- Implement `SessionContext` class
- Add context accumulation to orchestrator
- Add "related events" section to prompts

### Phase 4: Metrics & Refinement (2-3 hours)
- Add `PromptMetrics` tracking
- Implement automated refinement suggestions
- Add telemetry for prompt effectiveness

---

## Conclusion

**Current Sage Prompting**: **7/10** - Solid foundation with good best practices

**Lightspeed Comparison**:
- ✅ Better than Lightspeed: Explicit security guidance, error handling patterns
- ✅ On par: FQCN enforcement, structured requirements
- ❌ Behind Lightspeed: Multi-task chaining, session context, few-shot examples

**Biggest Quick Win**: Add service-specific patterns + few-shot examples + lower temperature

**Biggest Long-Term Win**: Session context for correlated event handling

---

## Sources

- [IBM watsonx Code Assistant for Ansible - Prompting Guidelines](https://github.com/IBM/watsonx-code-assistant-for-ansible)
- [Ansible Lightspeed User Guide - Developing Content](https://docs.redhat.com/en/documentation/red_hat_ansible_lightspeed_with_ibm_watsonx_code_assistant/2.x_latest/html/red_hat_ansible_lightspeed_with_ibm_watsonx_code_assistant_user_guide/developing-ansible-content_lightspeed-user-guide)
- [Ansible Lightspeed: AI-Powered Playbook Automation Guide](https://spacelift.io/blog/ansible-lightspeed)
- [Ansible Lightspeed Research Paper - arXiv](https://arxiv.org/html/2402.17442v1)
