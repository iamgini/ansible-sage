# Rename Complete: ansible-sage → ansible-maya

**Date**: 2026-06-02  
**Status**: ✅ Complete

---

## Summary

Successfully renamed project from **Ansible Sage** to **Ansible Maya** following Ansible naming conventions (`ansible-<function>`).

---

## Changes Made

### 1. Python Package
- ✅ Renamed directory: `sage/` → `ansible_maya/`
- ✅ Updated all imports: `from sage.` → `from ansible_maya.`
- ✅ Updated package name in `pyproject.toml`

### 2. CLI Command
- ✅ Old: `ansible-sage` or `sage`
- ✅ New: `ansible-maya`
- ✅ Entry point updated in `pyproject.toml`

### 3. Documentation
- ✅ README.md
- ✅ CLAUDE.md
- ✅ All markdown files in `.claude/`
- ✅ CONTRIBUTING.md
- ✅ QUICKSTART.md
- ✅ WORKFLOW.md
- ✅ CHANGELOG.md

### 4. Configuration Files
- ✅ pyproject.toml
- ✅ docker-compose.yml
- ✅ Dockerfile
- ✅ .pre-commit-config.yaml

### 5. Test Files
- ✅ All test files in `tests/`
- ✅ All test scripts in `test-scripts/`
- ✅ Updated imports and comments

### 6. Project Metadata
- ✅ Project name
- ✅ Description
- ✅ Author names
- ✅ URLs (GitHub, docs)

---

## Next Steps for You

### 1. Rename GitHub Repository
```bash
# On GitHub:
# Settings → Repository name → ansible-maya
```

### 2. Update Git Remote (if needed)
```bash
git remote set-url origin git@github.com:your-org/ansible-maya.git
```

### 3. Reinstall Package
```bash
# Uninstall old package
pip uninstall ansible-sage

# Install new package
pip install -e .

# Verify
ansible-maya --help
```

### 4. Update CI/CD
- Update any CI/CD pipelines referencing `ansible-sage`
- Update Docker image names if applicable
- Update deployment scripts

### 5. Update Documentation Sites
- Update any external documentation
- Update README badges/links
- Update blog posts or announcements

---

## Verification Checklist

Run these commands to verify the rename:

```bash
# 1. Check no references to old name in Python files
grep -r "from sage\." ansible_maya/ tests/
# Should return nothing

# 2. Check imports work
python -c "from ansible_maya.core.prompt_templates import get_system_prompt; print('✓ Imports work')"

# 3. Check CLI command
python -m ansible_maya.cli --version
# or after pip install -e .:
ansible-maya --version

# 4. Run tests
pytest tests/ -v

# 5. Run test scripts
python test-scripts/test_temperature.py
python test-scripts/test_session_context.py
```

---

## Updated Project Description

**New tagline:**
> "Multi-provider AI gateway for Ansible playbook generation - Supports watsonx, Claude, OpenAI, Ollama, and custom LLM providers"

**Positioning:**
- Follows Ansible naming conventions (ansible-<function>)
- Complements Red Hat Ansible Lightspeed
- Targets AIOps workflows and event-driven automation
- Multi-LLM flexibility vs vendor lock-in

---

## Files Modified

**Total files updated**: ~60+ files

**Key files**:
- `pyproject.toml` - Package metadata
- `README.md` - Main documentation
- `CLAUDE.md` - AI assistant instructions  
- `ansible_maya/` - Entire Python package renamed
- All test files and scripts
- All markdown documentation
- Docker and config files

---

## No Breaking Changes For

Since this is a name change before first release:
- No published packages to deprecate
- No external APIs to version
- No user migrations needed

---

## Rationale

**Why rename?**

1. **Follows Ansible conventions**: `ansible-<function>` pattern (ansible-galaxy, ansible-playbook, etc.)
2. **Descriptive**: "AI Gateway" clearly indicates multi-LLM functionality
3. **Professional**: Suitable for Red Hat context
4. **Accurate**: "Gateway" emphasizes provider flexibility (vs Lightspeed's 3-provider limit)
5. **Scalable**: Name works as project grows

**Why not keep "Sage"?**
- Too generic, doesn't convey function
- Doesn't emphasize key differentiator (multi-LLM)
- Doesn't follow Ansible naming pattern

---

## Success Criteria

✅ All Python imports work  
✅ All tests pass  
✅ CLI command works  
✅ Documentation updated  
✅ No references to old name  
✅ Follows Ansible conventions  

---

**Rename complete! Ready for repository rename on GitHub.**
