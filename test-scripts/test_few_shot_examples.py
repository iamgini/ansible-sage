#!/usr/bin/env python3
"""Test few-shot examples in event prompts."""

import sys
from pathlib import Path

# Add ansible_maya to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ansible_maya.core.prompt_templates import (
    EVENT_DISK_FULL_PROMPT,
    EVENT_SERVICE_DOWN_PROMPT,
    EVENT_HIGH_CPU_PROMPT,
    EVENT_MEMORY_HIGH_PROMPT,
    EVENT_GENERIC_PROMPT,
)


def test_few_shot_examples():
    """Test that all event prompts contain few-shot examples."""

    print("Testing Few-Shot Examples in Event Prompts")
    print("=" * 70)

    prompts = {
        'disk_full': EVENT_DISK_FULL_PROMPT,
        'service_down': EVENT_SERVICE_DOWN_PROMPT,
        'high_cpu': EVENT_HIGH_CPU_PROMPT,
        'high_memory': EVENT_MEMORY_HIGH_PROMPT,
        'generic': EVENT_GENERIC_PROMPT,
    }

    all_passed = True

    for prompt_name, prompt_template in prompts.items():
        print(f"\n{prompt_name.upper()}")
        print("-" * 70)

        # Check for example section
        has_example_section = "## Example Pattern" in prompt_template
        if not has_example_section:
            print(f"✗ Missing '## Example Pattern' section")
            all_passed = False
        else:
            print(f"✓ Contains '## Example Pattern' section")

        # Check for YAML code block
        has_yaml_block = "```yaml" in prompt_template
        if not has_yaml_block:
            print(f"✗ Missing YAML code block")
            all_passed = False
        else:
            print(f"✓ Contains YAML code block")

        # Check for key Ansible patterns in example
        ansible_patterns = [
            "hosts:",
            "tasks:",
            "ansible.builtin.",
            "register:",
        ]

        missing_patterns = []
        for pattern in ansible_patterns:
            if pattern not in prompt_template:
                missing_patterns.append(pattern)
                all_passed = False

        if missing_patterns:
            print(f"✗ Missing patterns: {', '.join(missing_patterns)}")
        else:
            print(f"✓ Contains key Ansible patterns")

        # Check example shows best practices
        best_practices = [
            "when:",       # Conditional execution
            "block:",      # Error handling (most prompts)
            "changed_when: false",  # Idempotency marker
        ]

        found_practices = [bp for bp in best_practices if bp in prompt_template]
        if found_practices:
            print(f"✓ Shows best practices: {', '.join(found_practices)}")
        else:
            print(f"⚠ Could show more best practices")

        # Count lines in example
        if has_yaml_block:
            yaml_start = prompt_template.find("```yaml")
            yaml_end = prompt_template.find("```", yaml_start + 7)
            example_yaml = prompt_template[yaml_start:yaml_end]
            lines = len(example_yaml.split("\n"))
            print(f"  Example size: ~{lines} lines")

    print("\n" + "=" * 70)

    if all_passed:
        print("✓ All prompts have valid few-shot examples!")
        return 0
    else:
        print("✗ Some prompts missing required elements")
        return 1


if __name__ == "__main__":
    sys.exit(test_few_shot_examples())
