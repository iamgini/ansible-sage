#!/usr/bin/env python3
"""Test multi-task chaining functionality."""

import sys
from pathlib import Path

# Add ansible_maya to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ansible_maya.core.prompt_templates import (
    parse_multi_task_prompt,
    format_multi_task_prompt,
    is_multi_task_prompt,
)


def test_multi_task_parsing():
    """Test multi-task prompt parsing."""

    print("Testing Multi-Task Chaining Support")
    print("=" * 70)

    test_cases = [
        {
            'input': 'Install nginx',
            'expected_tasks': ['Install nginx'],
            'is_multi': False,
            'description': 'Single task',
        },
        {
            'input': 'Install nginx & Configure site & Start service',
            'expected_tasks': ['Install nginx', 'Configure site', 'Start service'],
            'is_multi': True,
            'description': 'Three tasks',
        },
        {
            'input': 'Install postgresql & Setup database & Create user & Start service',
            'expected_tasks': ['Install postgresql', 'Setup database', 'Create user', 'Start service'],
            'is_multi': True,
            'description': 'Four tasks',
        },
        {
            'input': 'Check disk usage & Clean logs & Verify space',
            'expected_tasks': ['Check disk usage', 'Clean logs', 'Verify space'],
            'is_multi': True,
            'description': 'Three cleanup tasks',
        },
        {
            'input': '  Install package  &  Configure settings  &  Restart service  ',
            'expected_tasks': ['Install package', 'Configure settings', 'Restart service'],
            'is_multi': True,
            'description': 'With extra whitespace',
        },
    ]

    all_passed = True

    print("\n## Task Parsing Tests")
    print("-" * 70)

    for idx, test_case in enumerate(test_cases, 1):
        input_prompt = test_case['input']
        expected_tasks = test_case['expected_tasks']
        expected_multi = test_case['is_multi']
        description = test_case['description']

        # Test is_multi_task_prompt
        is_multi = is_multi_task_prompt(input_prompt)
        if is_multi != expected_multi:
            print(f"✗ Test {idx} ({description}): is_multi_task_prompt returned {is_multi}, expected {expected_multi}")
            all_passed = False
            continue

        # Test parse_multi_task_prompt
        parsed_tasks = parse_multi_task_prompt(input_prompt)
        if parsed_tasks != expected_tasks:
            print(f"✗ Test {idx} ({description}): Parsing failed")
            print(f"  Input: {input_prompt}")
            print(f"  Expected: {expected_tasks}")
            print(f"  Got: {parsed_tasks}")
            all_passed = False
            continue

        print(f"✓ Test {idx}: {description}")
        print(f"  Input: {input_prompt}")
        print(f"  Parsed: {len(parsed_tasks)} tasks - {parsed_tasks}")

    # Test multi-task prompt formatting
    print("\n## Multi-Task Prompt Formatting")
    print("-" * 70)

    sample_tasks = ['Install postgresql', 'Setup database', 'Start service']
    event_context = {
        'host': 'db-server-01',
        'timestamp': '2026-06-02T10:00:00Z',
    }

    formatted_prompt = format_multi_task_prompt(sample_tasks, event_context)

    # Check for key elements
    checks = [
        ('Host in prompt', 'db-server-01' in formatted_prompt),
        ('Task count', '3 related tasks' in formatted_prompt),
        ('Numbered tasks', '1. Install postgresql' in formatted_prompt),
        ('Numbered tasks', '2. Setup database' in formatted_prompt),
        ('Numbered tasks', '3. Start service' in formatted_prompt),
        ('Example pattern', 'Example Multi-Task Pattern' in formatted_prompt),
        ('YAML block', '```yaml' in formatted_prompt),
        ('Task chaining', 'register:' in formatted_prompt),
        ('Conditional', 'when:' in formatted_prompt),
        ('Error handling', 'block:' in formatted_prompt),
    ]

    print("\nFormatted prompt validation:")
    for check_name, check_result in checks:
        status = "✓" if check_result else "✗"
        print(f"{status} {check_name}")
        if not check_result:
            all_passed = False

    print(f"\nFormatted prompt length: {len(formatted_prompt)} chars")
    print(f"Formatted prompt lines: {len(formatted_prompt.split(chr(10)))} lines")

    print("\n" + "=" * 70)

    if all_passed:
        print("✓ All multi-task chaining tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(test_multi_task_parsing())
