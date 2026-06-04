# Ansible Maya - Scope Clarification

## What Ansible Maya IS ✅

**A stateless REST API for AI-powered Ansible playbook generation**

```
┌─────────────────────────────────────────────────────────┐
│              Ansible Maya API                            │
│                                                          │
│  Input:  Event JSON (disk_full, service_down, etc.)    │
│           ↓                                              │
│  Process: LLM → Generate Playbook → Validate            │
│           ↓                                              │
│  Output: Playbook YAML + Confidence Score + Metadata    │
└─────────────────────────────────────────────────────────┘
```

**Responsibilities:**
- ✅ Receive event context via REST API
- ✅ Generate Ansible playbook using LLM (Claude, OpenAI, or custom)
- ✅ Apply Ansible best practices (FQCN, idempotence, error handling)
- ✅ Validate playbook with ansible-lint
- ✅ Calculate confidence score
- ✅ Return playbook JSON

**That's it!** Nothing more, nothing less.

## What Ansible Maya IS NOT ❌

### 1. NOT an Event Listener
- ❌ Does NOT listen to monitoring systems (Prometheus, Grafana, etc.)
- ❌ Does NOT subscribe to webhooks
- ❌ Does NOT receive events directly from infrastructure

**You must:** Build your own event-driven system that calls Maya's API

### 2. NOT a Playbook Executor
- ❌ Does NOT run playbooks
- ❌ Does NOT connect to managed hosts
- ❌ Does NOT execute `ansible-playbook`

**You must:** Execute playbooks yourself (AAP, ansible-playbook, AWX, etc.)

### 3. NOT a Playbook Storage
- ❌ Does NOT have a database
- ❌ Does NOT store playbook history
- ❌ Does NOT track versions
- ❌ Does NOT persist generated playbooks

**You must:** Save playbooks yourself (git, filesystem, database, etc.)

### 4. NOT an AAP Integration ❌
- ❌ Does NOT connect to Ansible Automation Platform (AAP)
- ❌ Does NOT launch AAP job templates
- ❌ Does NOT use AAP MCP server
- ❌ Does NOT interact with `ansible.mcp` collection

**AAP/MCP is completely separate!**

### 5. NOT a Git Manager
- ❌ Does NOT commit to git
- ❌ Does NOT push to repositories
- ❌ Does NOT manage branches

**You must:** Handle git operations in your orchestration layer

## Architecture Separation

```
┌─────────────────────────────────────────────────────────────────┐
│  YOUR EVENT-DRIVEN ORCHESTRATION                                 │
│  (EDA Rulebook, AAP Workflow, Custom Script, etc.)              │
│                                                                  │
│  1. Listen to events (Prometheus, webhook, etc.)                │
│  2. Call Maya API ──────────────┐                               │
│                                  │                               │
│                                  ▼                               │
│                       ┌────────────────────┐                    │
│                       │  Ansible Maya API  │                    │
│                       │                    │                    │
│                       │  Generate Playbook │                    │
│                       │  Validate YAML     │                    │
│                       │  Return JSON       │                    │
│                       └────────────────────┘                    │
│                                  │                               │
│  3. Receive playbook ◄───────────┘                               │
│  4. Save to git                                                  │
│  5. Execute with AAP/ansible-playbook                           │
│  6. (Optional) Use ansible.mcp to query AAP for job templates  │
└─────────────────────────────────────────────────────────────────┘
```

## Code Evidence

### Ansible Maya Dependencies (requirements-minimal.txt)
```txt
fastapi==0.115.6          # Web API
uvicorn[standard]==0.34.0 # ASGI server
anthropic==0.42.0         # Claude LLM
openai==1.59.7            # OpenAI LLM
pyyaml==6.0.2            # YAML processing
```

**No AAP, No MCP, No Database, No Redis!**

### Only MCP Reference in Code
```python
# ansible_maya/core/exceptions.py
class AAPIntegrationError(SageException):
    """Raised when AAP (Ansible Automation Platform) integration fails."""
```

**This exception is NEVER raised anywhere!** It's leftover code from planning.

### What Maya Actually Does (Code Check)
```bash
$ grep -r "os.getenv" ansible_maya/ --include="*.py"

# Only these environment variables are used:
- LLM_PROVIDER
- ANTHROPIC_API_KEY
- OPENAI_API_KEY
- CUSTOM_LLM_ENDPOINT
- CUSTOM_LLM_MODEL
- CUSTOM_LLM_API_KEY

# NO AAP_URL, NO AAP_TOKEN, NO MCP_SERVER!
```

## AAP/MCP Integration - Separate Project

**Location:** `/home/gmadappa/ansible/ansible-aiops/`

This is where AAP MCP integration lives:

```yaml
# ansible-aiops/playbooks/find-matching-job-template.yml
- name: Query AAP via MCP for matching job templates
  ansible.mcp.query_aap:
    mcp_server_url: "{{ lookup('env', 'AAP_MCP_SERVER_URL') }}"
    bearer_token: "{{ lookup('env', 'AAP_BEARER_TOKEN') }}"
    # ... MCP-specific logic
```

**Uses:** `ansible.mcp` collection to interact with AAP MCP server

**Completely independent from Ansible Maya!**

## Integration Example

### Workflow 1: Maya + Git (Current Implementation)
```yaml
# generate-and-push.yml
- name: Call Maya API
  uri:
    url: http://localhost:8000/api/v1/events/generate
    body: { event_type: "disk_full", ... }
  register: maya_response

- name: Save to git
  git: ...

- name: Commit and push
  command: git push
```

**Maya's role:** Generate playbook only

### Workflow 2: Maya + AAP MCP (Hypothetical)
```yaml
- name: Generate playbook with Maya
  uri:
    url: http://localhost:8000/api/v1/events/generate
  register: maya_response

- name: Find matching AAP job template using MCP
  ansible.mcp.query_aap:
    mcp_server_url: "{{ aap_mcp_url }}"
  register: aap_templates

- name: Launch AAP job template
  awx.awx.job_launch:
    job_template: "{{ aap_templates.best_match }}"
    extra_vars: "{{ maya_response.json.playbook }}"
```

**Maya's role:** Generate playbook only  
**MCP's role:** Find AAP job templates  
**AAP's role:** Execute playbook

## Summary Table

| Feature | Ansible Maya | ansible-aiops (MCP) | Your Orchestration |
|---------|--------------|---------------------|-------------------|
| Generate Playbook | ✅ **Core function** | ❌ | ❌ |
| Validate YAML | ✅ | ❌ | ❌ |
| Query AAP via MCP | ❌ | ✅ **Core function** | Optional |
| Execute Playbook | ❌ | ❌ | ✅ **Your job** |
| Store Playbooks | ❌ | ❌ | ✅ **Your job** |
| Listen to Events | ❌ | ❌ | ✅ **Your job** |
| Git Operations | ❌ | ❌ | ✅ **Your job** |

## Key Takeaway

**Ansible Maya:**
- ✅ Playbook generation microservice
- ✅ LLM + validation + confidence scoring
- ✅ Stateless REST API

**Everything else (AAP, MCP, git, execution, storage, event listening) is YOUR responsibility in the orchestration layer!**

Maya is a **tool**, not a **platform**. It does one thing well: generate playbooks.

You build the platform around it using:
- Event-Driven Ansible (EDA) for event handling
- `ansible.mcp` collection for AAP integration
- `generate-and-push.yml` for git workflow
- AAP/AWX for playbook execution
- Your choice of storage (git, database, filesystem)

**Separation of concerns = flexibility!**
