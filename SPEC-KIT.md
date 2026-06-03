# Ansible Maya - Spec-Kit Implementation Guide

This document describes how to use [GitHub Spec-Kit](https://github.com/github/spec-kit) for specification-driven development of Ansible Maya features.

## What is Spec-Kit?

Spec-Kit is a framework for **Specification-Driven Development (SDD)** where:
- Specifications drive implementation (not just documentation)
- AI agents use specs to generate code systematically
- Multi-step refinement process (specify → plan → implement)
- Works with 30+ AI coding agents (Claude Code, Cursor, Windsurf, etc.)

## Setup

### 1. Install Spec-Kit

```bash
cd /home/gmadappa/ansible/ansible-maya

# Install spec-kit globally or locally
npm install -g @github/spec-kit
# OR for local project:
npm install --save-dev @github/spec-kit
```

### 2. Initialize Spec-Kit

```bash
# Initialize in the project
specify init ansible-maya

# This creates:
# .specify/           - Spec-kit configuration and templates
# specs/              - Feature specifications directory
```

### 3. Configure for Ansible Maya

The initialization creates:

```
ansible-maya/
├── .specify/
│   ├── memory/
│   │   └── constitution.md       # Project principles
│   ├── templates/
│   │   ├── spec.md.hbs           # Spec template
│   │   ├── plan.md.hbs           # Plan template
│   │   └── tasks.md.hbs          # Tasks template
│   └── extensions/               # Custom extensions
└── specs/
    └── 001-git-publisher/        # Example feature
        ├── spec.md               # What to build
        ├── plan.md               # How to build
        └── tasks.md              # Action items
```

---

## Ansible Maya Constitution

Create `.specify/memory/constitution.md`:

```markdown
# Ansible Maya Development Constitution

## Project Mission
Build an AI-powered playbook generation service that creates validated Ansible playbooks from infrastructure events and publishes them to Git repositories for execution by existing automation pipelines.

## Core Principles

### 1. GitOps First
- **No Execution**: Ansible Maya NEVER executes playbooks
- **Git Publishing**: All playbooks committed to Git for external pipeline execution
- **Confidence-Based Branching**: High confidence → main, Medium → review, Low → draft

### 2. Safety by Design
- **Validation Required**: Every playbook must pass ansible-lint
- **Human Review**: Medium/low confidence playbooks require approval
- **Audit Trail**: Full metadata in Git commits
- **No Auto-Merge**: Pull requests for non-production branches

### 3. Ansible Best Practices
- **FQCN Required**: Fully Qualified Collection Names for all modules
- **Idempotency**: All tasks must be idempotent
- **Error Handling**: Proper use of failed_when, block/rescue
- **Security**: No hardcoded credentials, proper file permissions

### 4. LLM Provider Agnostic
- **BYOM Pattern**: Bring Your Own Model
- **Provider Abstraction**: BaseLLMProvider interface
- **No Vendor Lock-in**: Support Claude, OpenAI, Ollama, custom providers

### 5. Event-Driven Architecture
- **Stateless Processing**: Each event processed independently
- **Classification First**: Known → Complex → Unknown
- **Confidence Scoring**: Transparent, rule-based scoring

## Technical Standards

### Code Quality
- **Type Hints**: All functions must have type annotations
- **Async/Await**: All I/O operations must be async
- **Testing**: 80%+ code coverage required
- **Linting**: black, isort, ruff, mypy must pass

### API Design
- **RESTful**: Follow REST conventions
- **OpenAPI**: FastAPI auto-documentation
- **Versioning**: API versioned (/api/v1/)
- **Error Handling**: Proper HTTP status codes

### Documentation
- **Docstrings**: Google style for all public functions
- **Examples**: Every major feature needs usage example
- **Architecture**: Update WORKFLOW.md for process changes
- **CLAUDE.md**: Keep developer guidance current

## Decision Framework

### When Adding a Feature
1. Does it align with GitOps-first principle?
2. Does it maintain safety guarantees?
3. Is it provider-agnostic?
4. Does it follow Ansible best practices?
5. Is it properly tested and documented?

### When Choosing Technology
- Prefer Python 3.11+ standard library
- Use established Ansible ecosystem tools
- Avoid unnecessary dependencies
- Consider Docker/container compatibility

### When Handling Events
- Classify before generating
- Calculate confidence transparently
- Log all decisions with context
- Never execute without explicit external trigger

## Non-Negotiables

❌ **NEVER**:
- Execute playbooks directly from Ansible Maya
- Skip validation (ansible-lint)
- Auto-merge to main branch without confidence check
- Hardcode credentials or secrets
- Generate playbooks without event context

✅ **ALWAYS**:
- Calculate and expose confidence score
- Commit to appropriate Git branch
- Validate with ansible-lint before publishing
- Log generation metadata
- Provide human-readable recommendations

## Extension Guidelines

New features must:
- Maintain separation between generation and execution
- Support all configured LLM providers
- Include unit tests and integration tests
- Update relevant documentation
- Follow existing code patterns

---

This constitution guides all development decisions for Ansible Maya.
```

---

## Development Workflow

### Phase 1: Constitution (`/speckit.constitution`)

Already created above. This establishes the project's principles.

### Phase 2: Specify Feature (`/speckit.specify`)

For each new feature, create a spec. Example:

**Command**:
```bash
specify new "Git Publisher Integration"
# Creates: specs/001-git-publisher/spec.md
```

**Example Spec** (`specs/001-git-publisher/spec.md`):

```markdown
# Specification: Git Publisher Integration

## Overview
Implement Git repository integration to publish generated playbooks to configured repositories based on confidence levels.

## User Stories

### US-1: Configure Git Repository
**As a** DevOps engineer  
**I want** to configure a Git repository for playbook storage  
**So that** generated playbooks are version controlled and accessible to our pipeline

**Acceptance Criteria**:
- Repository URL can be configured via environment variables
- Support both SSH and HTTPS authentication
- Support GitHub, GitLab, Bitbucket, and generic Git
- Allow configuration of branch names (main, review, draft)

### US-2: Confidence-Based Branch Publishing
**As a** system  
**I want** to publish playbooks to different branches based on confidence  
**So that** high-confidence playbooks go to main, medium to review, low to draft

**Acceptance Criteria**:
- Confidence ≥80% → main branch
- Confidence 50-80% → review branch
- Confidence <50% → draft branch
- Branch names configurable
- Clear logging of branch selection logic

### US-3: Commit Metadata
**As a** reviewer  
**I want** commit messages to include full context  
**So that** I can understand the playbook's origin and confidence

**Acceptance Criteria**:
- Commit message includes event type, host, confidence
- Includes validation status and model used
- Includes timestamp and event ID
- Follows conventional commit format

### US-4: API Endpoint for Publishing
**As a** developer  
**I want** an API endpoint to publish playbooks  
**So that** I can trigger publishing programmatically

**Acceptance Criteria**:
- POST /api/v1/events/publish-to-git endpoint
- Accepts playbook content, confidence, metadata
- Returns commit SHA and branch
- Handles authentication errors gracefully

## Constraints

- Must not execute playbooks
- Must support temporary working directory (no persistent clone)
- Must clean up temp directories on completion
- Must support branch creation if not exists
- Must handle merge conflicts (fail gracefully)

## Non-Functional Requirements

- Publishing completes within 30 seconds
- Supports repositories up to 1GB
- Thread-safe (multiple concurrent publishes)
- Proper error logging with context
- No secrets in logs

## Dependencies

- GitPython or subprocess git commands
- Temporary file system access
- Network access to Git remote
- Git credentials (SSH key or PAT)

## Success Metrics

- 100% of generated playbooks successfully published
- <5 second average publish time
- Zero credential leaks in logs
- Clear audit trail in Git history
```

### Phase 3: Plan (`/speckit.plan`)

**Command**:
```bash
cd specs/001-git-publisher
specify plan
# Creates/updates: plan.md
```

**Example Plan** (`specs/001-git-publisher/plan.md`):

```markdown
# Implementation Plan: Git Publisher Integration

## Architecture Overview

### Components

1. **GitPublisher** (`sage/integrations/git_publisher.py`)
   - Main class for Git operations
   - Handles clone, commit, push operations
   - Manages temporary working directories

2. **GitConfig** (dataclass)
   - Configuration holder
   - Validation logic
   - Default values

3. **PublishResult** (dataclass)
   - Return value from publish operation
   - Success/failure status
   - Commit SHA, branch, file path

4. **API Endpoint** (`sage/api/routes/events.py`)
   - POST /api/v1/events/publish-to-git
   - Request/response models
   - Error handling

### Data Flow

```
Event Generated
    ↓
Calculate Confidence
    ↓
Determine Target Branch
    ↓
GitPublisher.publish_playbook()
    ↓
1. Clone repo to temp dir
2. Checkout/create branch
3. Write playbook file
4. Commit with metadata
5. Push to remote
6. Clean up temp dir
    ↓
Return PublishResult
```

## Technology Choices

### Git Operations
- **Approach**: Subprocess calls to `git` CLI
- **Why**: More reliable than GitPython, better error messages
- **Alternative Considered**: GitPython - rejected due to complexity

### Temporary Storage
- **Approach**: Python `tempfile.mkdtemp()`
- **Why**: Automatic cleanup, OS-appropriate location
- **Cleanup**: Using `try/finally` block

### Authentication
- **SSH**: Via `GIT_SSH_COMMAND` environment variable
- **HTTPS**: Token in URL (https://token@github.com/...)
- **Storage**: Environment variables only

## File Structure

```
sage/integrations/git_publisher.py  # Main implementation
sage/api/routes/events.py           # API endpoint (update)
.env.example                         # Git config examples
tests/unit/integrations/test_git_publisher.py
tests/integration/test_git_integration.py
```

## Implementation Steps

### Step 1: Core GitPublisher Class
- [ ] Create `GitConfig` dataclass
- [ ] Create `PublishResult` dataclass  
- [ ] Create `ConfidenceLevel` enum
- [ ] Implement `GitPublisher.__init__()`
- [ ] Implement `_calculate_confidence_level()`
- [ ] Implement `_get_target_branch()`

### Step 2: Git Operations
- [ ] Implement `_prepare_repo()` - clone repository
- [ ] Implement `_checkout_branch()` - create/checkout branch
- [ ] Implement `_write_playbook()` - write file with timestamp
- [ ] Implement `_generate_commit_message()` - format metadata
- [ ] Implement `_commit_changes()` - git add, commit
- [ ] Implement `_push_to_remote()` - git push
- [ ] Implement `_cleanup()` - remove temp directory

### Step 3: Main Publish Method
- [ ] Implement `publish_playbook()` orchestration
- [ ] Add error handling (try/except/finally)
- [ ] Add logging at each step
- [ ] Return `PublishResult`

### Step 4: API Integration
- [ ] Create `GitPublishRequest` Pydantic model
- [ ] Create `GitPublishResponse` Pydantic model
- [ ] Implement POST endpoint `/api/v1/events/publish-to-git`
- [ ] Add to FastAPI router

### Step 5: Testing
- [ ] Unit tests for confidence calculation
- [ ] Unit tests for branch selection
- [ ] Unit tests for commit message generation
- [ ] Mock tests for git operations
- [ ] Integration test with actual Git repo
- [ ] API endpoint tests

### Step 6: Documentation
- [ ] Update .env.example with Git variables
- [ ] Add docstrings to all functions
- [ ] Update WORKFLOW.md with Git publishing
- [ ] Add example to examples/git_publish.py
- [ ] Update README.md

## Error Handling

### Scenarios
- Git clone fails (network, auth)
- Branch already exists with conflicts
- Push fails (permissions, conflicts)
- Disk full during clone
- Invalid Git URL

### Strategy
- Return `PublishResult(success=False, error="...")`
- Log full error context
- Clean up temp directory even on failure
- Don't retry automatically (caller decides)

## Security Considerations

- Never log Git tokens
- Use SSH keys when possible
- Store credentials in environment only
- Clear sensitive data from memory
- Validate repository URLs

## Performance

- Target: <5 seconds for typical playbook
- Clone only (no full history): `git clone --depth 1`
- Shallow clone for speed
- Parallel publishes supported

## Rollback Plan

If Git publishing fails in production:
1. Disable `GIT_AUTO_PUBLISH` 
2. Queue failed publishes for retry
3. Manual publish via API
4. Check Git server status
5. Verify credentials

## Dependencies

### New
- None (use subprocess, stdlib only)

### Environment Variables
- `GIT_REPO_URL`
- `GIT_TOKEN` or `GIT_SSH_KEY_PATH`
- `GIT_MAIN_BRANCH`
- `GIT_REVIEW_BRANCH`
- `GIT_DRAFT_BRANCH`
- `GIT_USERNAME`
- `GIT_EMAIL`

## Acceptance Criteria Met

✅ Repository URL configurable  
✅ Support SSH and HTTPS  
✅ Confidence-based branching  
✅ Rich commit metadata  
✅ API endpoint for publishing  
✅ No playbook execution  
✅ Temp directory cleanup  
✅ Error handling  
```

### Phase 4: Tasks (`/speckit.tasks`)

**Command**:
```bash
specify tasks
# Creates/updates: tasks.md
```

**Example Tasks** (`specs/001-git-publisher/tasks.md`):

```markdown
# Tasks: Git Publisher Integration

## Task 1: Create Data Models
**Dependencies**: None  
**Estimated Time**: 30 minutes

- [ ] Create `ConfidenceLevel` enum (HIGH, MEDIUM, LOW)
- [ ] Create `GitConfig` dataclass with validation
- [ ] Create `PublishResult` dataclass
- [ ] Add type hints to all fields
- [ ] Write unit tests for dataclasses

**Files**:
- Create `sage/integrations/git_publisher.py`

---

## Task 2: Implement Confidence Logic
**Dependencies**: Task 1  
**Estimated Time**: 20 minutes

- [ ] Implement `_calculate_confidence_level(score: float) -> ConfidenceLevel`
- [ ] Implement `_get_target_branch(level: ConfidenceLevel) -> str`
- [ ] Write unit tests for confidence thresholds
- [ ] Test boundary conditions (0.5, 0.8, etc.)

**Files**:
- Update `sage/integrations/git_publisher.py`
- Create `tests/unit/integrations/test_git_publisher.py`

---

## Task 3: Implement Repository Cloning
**Dependencies**: Task 1  
**Estimated Time**: 45 minutes

- [ ] Implement `_get_authenticated_url()` for HTTPS with token
- [ ] Implement `_prepare_repo()` to clone repository
- [ ] Support SSH key authentication via GIT_SSH_COMMAND
- [ ] Configure git user.name and user.email
- [ ] Add error handling for auth failures
- [ ] Write mock tests

**Files**:
- Update `sage/integrations/git_publisher.py`
- Update `tests/unit/integrations/test_git_publisher.py`

---

## Task 4: Implement Branch Operations
**Dependencies**: Task 3  
**Estimated Time**: 30 minutes

- [ ] Implement `_checkout_branch(branch: str)` 
- [ ] Create branch if doesn't exist
- [ ] Checkout existing branch
- [ ] Run git command via `_run_git_command()`
- [ ] Write tests for branch creation/checkout

**Files**:
- Update `sage/integrations/git_publisher.py`
- Update tests

---

## Task 5: Implement File Writing
**Dependencies**: Task 3  
**Estimated Time**: 30 minutes

- [ ] Implement `_write_playbook(name, content) -> Path`
- [ ] Create playbooks directory if needed
- [ ] Add timestamp prefix to filename
- [ ] Ensure .yml extension
- [ ] Write tests

**Files**:
- Update `sage/integrations/git_publisher.py`
- Update tests

---

## Task 6: Implement Commit Generation
**Dependencies**: Task 5  
**Estimated Time**: 45 minutes

- [ ] Implement `_generate_commit_message(name, confidence, metadata) -> str`
- [ ] Include all required metadata (event, host, confidence, model)
- [ ] Format as multi-line message
- [ ] Add "Generated by Ansible Maya" footer
- [ ] Write tests for message formatting

**Files**:
- Update `sage/integrations/git_publisher.py`
- Update tests

---

## Task 7: Implement Commit and Push
**Dependencies**: Task 6  
**Estimated Time**: 40 minutes

- [ ] Implement `_commit_changes(file_path, message) -> str`
- [ ] Stage file with `git add`
- [ ] Commit with message
- [ ] Return commit SHA
- [ ] Implement `_push_to_remote(branch)`
- [ ] Handle push failures
- [ ] Write tests

**Files**:
- Update `sage/integrations/git_publisher.py`
- Update tests

---

## Task 8: Implement Cleanup
**Dependencies**: Task 3  
**Estimated Time**: 15 minutes

- [ ] Implement `_cleanup()` to remove temp directory
- [ ] Use `shutil.rmtree()` with error handling
- [ ] Call in finally block
- [ ] Write tests

**Files**:
- Update `sage/integrations/git_publisher.py`
- Update tests

---

## Task 9: Orchestrate publish_playbook()
**Dependencies**: Tasks 2-8  
**Estimated Time**: 60 minutes

- [ ] Implement main `publish_playbook()` method
- [ ] Call all helper methods in sequence
- [ ] Wrap in try/except/finally
- [ ] Return PublishResult with success/error
- [ ] Add comprehensive logging
- [ ] Write integration test with real Git repo
- [ ] Test error scenarios

**Files**:
- Update `sage/integrations/git_publisher.py`
- Create `tests/integration/test_git_integration.py`

---

## Task 10: Create API Endpoint
**Dependencies**: Task 9  
**Estimated Time**: 45 minutes

- [ ] Create `GitPublishRequest` Pydantic model
- [ ] Create `GitPublishResponse` Pydantic model
- [ ] Implement POST `/api/v1/events/publish-to-git` endpoint
- [ ] Parse request, create GitConfig, call publisher
- [ ] Return GitPublishResponse
- [ ] Add error handling
- [ ] Write API tests

**Files**:
- Update `sage/api/routes/events.py`
- Update `tests/unit/api/test_events_api.py`

---

## Task 11: Environment Configuration
**Dependencies**: None (can be parallel)  
**Estimated Time**: 20 minutes

- [ ] Add Git variables to `.env.example`
- [ ] Document all Git configuration options
- [ ] Add comments explaining SSH vs HTTPS
- [ ] Update README.md configuration section

**Files**:
- Update `.env.example`
- Update `README.md`

---

## Task 12: Documentation
**Dependencies**: Tasks 1-11  
**Estimated Time**: 60 minutes

- [ ] Add docstrings to all public methods
- [ ] Create `examples/git_publish.py` example
- [ ] Update WORKFLOW.md with Git publishing flow
- [ ] Add troubleshooting section for Git errors
- [ ] Update QUICKSTART.md

**Files**:
- Update all Python files with docstrings
- Create `examples/git_publish.py`
- Update `WORKFLOW.md`
- Update `QUICKSTART.md`

---

## Summary

**Total Estimated Time**: ~7 hours  
**Total Tasks**: 12  
**Critical Path**: 1 → 3 → 5 → 6 → 7 → 9 → 10

**Testing Strategy**:
- Unit tests for each component
- Mock tests for git operations
- Integration test with actual Git repository
- API endpoint tests
- Error scenario tests

**Validation**:
- All tests pass
- Code coverage ≥80%
- Linting passes (black, mypy, ruff)
- Manual test with real Git repo
- API docs updated automatically
```

### Phase 5: Implementation (`/speckit.implement`)

Now use your AI coding agent (Claude Code, Cursor, etc.) to implement:

```bash
# Let Claude Code implement tasks
# Use task IDs from tasks.md

# Example prompts:
"Implement Task 1 from specs/001-git-publisher/tasks.md"
"Implement Task 2, use the plan in specs/001-git-publisher/plan.md"
"Run tests for Task 9"
```

---

## Spec-Kit Commands Reference

### Core Commands

```bash
# Initialize project
specify init ansible-maya

# Create new feature spec
specify new "Feature Name"

# Define constitution (project principles)
/speckit.constitution

# Create specification (what to build)
/speckit.specify

# Clarify underspecified areas
/speckit.clarify

# Create implementation plan
/speckit.plan

# Generate task breakdown
/speckit.tasks

# Implement tasks
/speckit.implement

# Analyze consistency across specs
/speckit.analyze

# Generate quality checklist
/speckit.checklist
```

---

## Benefits for Ansible Maya

### 1. **Structured Development**
- Clear phases: Specify → Plan → Implement
- No skipping validation or best practices
- Documented decision-making

### 2. **AI Agent Efficiency**
- AI reads spec, plan, tasks systematically
- Less back-and-forth clarification
- Consistent code quality

### 3. **Team Collaboration**
- Specs reviewable before implementation
- Clear acceptance criteria
- Audit trail of decisions

### 4. **Quality Assurance**
- Every feature has tests defined upfront
- Non-functional requirements documented
- Security/performance considered early

### 5. **Onboarding**
- New contributors read specs to understand features
- Constitution guides architectural decisions
- Examples show proper patterns

---

## Example: Adding a New Feature with Spec-Kit

### Scenario: Add Molecule Testing Support

**Step 1: Create Spec**
```bash
specify new "Molecule Testing Integration"
cd specs/002-molecule-testing
```

**Step 2: Use Claude Code to specify**
```
/speckit.specify

Goal: Add optional Molecule testing for generated playbooks before Git publishing.

User stories:
- As an operator, I want critical playbooks tested with Molecule before publishing
- As a developer, I want to configure which event types require Molecule testing
- As a reviewer, I want to see Molecule test results in the Git commit message

Non-goals:
- Testing every single playbook (too slow)
- Running Molecule on the Ansible Maya server (should use containers)
```

**Step 3: Plan**
```
/speckit.plan
```

Claude Code will create detailed implementation plan.

**Step 4: Generate Tasks**
```
/speckit.tasks
```

Gets actionable, ordered task list.

**Step 5: Implement**
```
Implement Task 1 from specs/002-molecule-testing/tasks.md
```

Claude Code implements following the spec and plan.

---

## Integration with Existing Ansible Maya

Spec-kit complements existing development:

```
ansible-maya/
├── .specify/              # Spec-kit configuration
│   └── memory/
│       └── constitution.md
├── specs/                 # Feature specifications
│   ├── 001-git-publisher/
│   ├── 002-molecule-testing/
│   └── 003-openai-provider/
├── sage/                  # Actual implementation
├── tests/                 # Test suite
├── CLAUDE.md             # Developer guide (references constitution)
├── WORKFLOW.md           # Process docs (references specs)
└── README.md
```

**Workflow**:
1. Spec-kit for **new features** (structured approach)
2. Direct development for **bug fixes** (too small for spec)
3. CLAUDE.md for **general development guidance**
4. Constitution drives **architectural decisions**

---

## Conclusion

Spec-Kit provides:
- ✅ Structured, repeatable development process
- ✅ AI agent efficiency (clear context)
- ✅ Quality assurance built-in
- ✅ Documentation as byproduct
- ✅ Team alignment on features

Perfect for Ansible Maya's systematic, safety-critical development needs.

**Next Steps**:
1. `npm install -g @github/spec-kit`
2. `specify init ansible-maya`
3. Create constitution (use template above)
4. Start specifying features with `/speckit.specify`
