# Example: OpenAI Provider Implementation with Spec-Kit

This directory contains a **complete example** of using Spec-Kit for feature development in Ansible Maya.

## What's Included

This example shows the full Spec-Kit workflow for adding OpenAI GPT-4 support:

1. **[spec.md](./spec.md)** - Feature Specification
   - User stories with acceptance criteria
   - Functional and non-functional requirements
   - Success metrics
   - Constraints and dependencies

2. **[plan.md](./plan.md)** - Implementation Plan
   - Architecture diagrams
   - Technology choices with rationale
   - Step-by-step implementation guide
   - Error handling strategy
   - Testing approach

3. **[tasks.md](./tasks.md)** - Actionable Task Breakdown
   - 12 concrete tasks with checklists
   - Time estimates for each task
   - Dependencies between tasks
   - Code snippets and verification steps

## How to Use This Example

### Option 1: Study the Pattern

Read through these files to understand the Spec-Kit approach:

```bash
# Read in order
cat specs/example-openai-provider/spec.md
cat specs/example-openai-provider/plan.md
cat specs/example-openai-provider/tasks.md
```

### Option 2: Actually Implement OpenAI Support

Use Claude Code to implement based on these specs:

```bash
# 1. Start with Task 1
Implement Task 1 from specs/example-openai-provider/tasks.md

# 2. Continue sequentially
Implement Task 2 from specs/example-openai-provider/tasks.md
Implement Task 3 from specs/example-openai-provider/tasks.md
# ... and so on

# OR implement in batches
Implement Tasks 1-3 (setup and structure) from specs/example-openai-provider/tasks.md
```

### Option 3: Use as Template for New Features

Copy this structure for your own features:

```bash
# Create new feature spec
mkdir specs/003-my-feature
cp specs/example-openai-provider/spec.md specs/003-my-feature/
cp specs/example-openai-provider/plan.md specs/003-my-feature/
cp specs/example-openai-provider/tasks.md specs/003-my-feature/

# Edit files for your feature
# Then implement with Claude Code
```

## Key Takeaways from This Example

### From spec.md (Specification)

✅ **User Stories** with acceptance criteria make requirements clear
- "As a [user], I want [goal], so that [benefit]"
- Testable acceptance criteria
- Clear success/failure conditions

✅ **Constraints** prevent scope creep
- Explicit non-goals
- Technical limitations
- Compatibility requirements

✅ **Success Metrics** define "done"
- Quantitative (coverage, performance)
- Qualitative (code quality, usability)

### From plan.md (Implementation Plan)

✅ **Architecture First** before coding
- High-level design
- Component interaction
- Data flow diagrams

✅ **Technology Decisions** with rationale
- Document *why*, not just *what*
- Compare alternatives
- Explain trade-offs

✅ **Step-by-Step Implementation**
- Logical order
- Dependencies clear
- Incremental progress

### From tasks.md (Task Breakdown)

✅ **Concrete, Actionable Tasks**
- Clear checklist items
- Estimated time
- Verification steps

✅ **Dependencies Mapped**
- What blocks what
- Critical path identified
- Parallelization opportunities

✅ **Code Snippets Included**
- Shows expected structure
- Reduces ambiguity
- Makes implementation faster

## Estimated Time

Following these specs, implementing OpenAI provider would take:

| Developer Experience | Estimated Time |
|---------------------|----------------|
| Senior (familiar with codebase) | 6-7 hours |
| Mid-level | 8-10 hours |
| Junior (with guidance) | 12-15 hours |
| **AI Agent (Claude Code)** | **4-6 hours** ⚡ |

The AI agent is faster because:
- Specs provide complete context
- No back-and-forth clarification needed
- Parallel task execution possible
- Tests included from start

## Comparison: With vs Without Spec-Kit

### Without Spec-Kit (Traditional)

```
Developer: "Add OpenAI support"
           ↓
       (starts coding)
           ↓
       "Wait, which models?"
           ↓
       "How should errors work?"
           ↓
       "What about token tracking?"
           ↓
       (many iterations)
           ↓
       "Oh, I should have structured it differently"
           ↓
       (refactor)
           ↓
       Done (maybe)
```

**Problems**:
- Unclear requirements
- Many iterations
- Inconsistent implementation
- Missed edge cases
- Documentation as afterthought

### With Spec-Kit (This Example)

```
Developer: "Add OpenAI support"
           ↓
   Write spec.md (user stories, requirements)
           ↓
   Write plan.md (architecture, decisions)
           ↓
   Write tasks.md (actionable steps)
           ↓
   Review specs with team
           ↓
   Implement task-by-task
           ↓
   Done (confident)
```

**Benefits**:
- Clear requirements upfront
- Fewer iterations
- Consistent with existing patterns
- Edge cases considered
- Documentation built-in

## Real-World Usage

### Scenario 1: You're Adding a Feature

1. Copy this example structure
2. Replace OpenAI with your feature
3. Think through user stories
4. Plan architecture
5. Break into tasks
6. Implement with Claude Code

### Scenario 2: Code Review

Reviewer can check:
- ✅ Does implementation match spec?
- ✅ Are all acceptance criteria met?
- ✅ Are tasks completed?
- ✅ Are edge cases handled per plan?

Much faster than reviewing code with no context!

### Scenario 3: Onboarding New Developer

New developer reads:
1. Constitution (.specify/memory/constitution.md)
2. Example spec (this directory)
3. Existing implementations

Understands:
- Project principles
- Development process
- Code patterns
- Quality standards

## Try It Yourself

### Quick Exercise (30 minutes)

Add a simple feature using this pattern:

**Feature**: Add `/api/v1/events/validate` endpoint to validate playbook YAML without generating

1. **Spec** (10 min): What should it do?
   - Input: playbook YAML string
   - Output: validation result
   - Edge cases: invalid YAML, empty input

2. **Plan** (10 min): How to implement?
   - Reuse existing validation code
   - New API endpoint
   - Pydantic request/response models

3. **Tasks** (5 min): Break it down
   - Task 1: Create request/response models
   - Task 2: Add endpoint to routes/events.py
   - Task 3: Write tests
   - Task 4: Update API docs

4. **Implement** (5 min): Let Claude Code do it
   ```
   Implement validation endpoint following this plan:
   [paste your plan]
   ```

## Questions?

- **Q**: Do I need Spec-Kit for small changes?
- **A**: No. Bug fixes and tiny changes don't need specs. Use for features.

- **Q**: Can I skip the plan and just write tasks?
- **A**: You could, but the plan helps you think through architecture first.

- **Q**: What if requirements change mid-implementation?
- **A**: Update the spec first, then the plan, then the tasks. Keep them in sync.

- **Q**: How detailed should specs be?
- **A**: Detailed enough that an AI agent (or new team member) can implement without asking questions.

## Next Steps

1. Read through this example thoroughly
2. Check out [SPEC-KIT.md](../../../SPEC-KIT.md) for setup
3. Copy [.specify-constitution-template.md](../../../.specify-constitution-template.md) to `.specify/memory/constitution.md`
4. Try creating a spec for a feature you want to add
5. Use Claude Code to implement it following your spec

---

**Remember**: The goal is not perfect specs, but **clear communication** between humans and AI agents about what to build and how to build it.

This example demonstrates that clearly!
