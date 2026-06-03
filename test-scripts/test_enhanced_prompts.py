#!/usr/bin/env python3
"""Test enhanced general-purpose prompts."""

import sys
from pathlib import Path

# Add ansible_maya to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ansible_maya.core.prompt_templates import get_event_prompt


def test_prompts():
    """Test that prompts are general-purpose and contain key patterns."""

    print("Testing Enhanced General-Purpose Prompts")
    print("=" * 70)

    # Key patterns that should be in all prompts
    general_patterns = [
        "General Patterns to Follow",  # Section header
        "appropriate",                  # Generic language
        "Requirements",                 # Structured requirements
    ]

    test_events = [
        {
            "type": "disk_full",
            "host": "web-01",
            "usage": "92",
            "mount_point": "/var",
        },
        {
            "type": "service_down",
            "host": "app-01",
            "service": "application",
            "status": "failed",
        },
        {
            "type": "high_cpu",
            "host": "api-01",
            "cpu_percent": "95",
            "duration": "10m",
        },
        {
            "type": "high_memory",
            "host": "db-01",
            "memory_percent": "88",
            "available_mb": "256",
        },
    ]

    all_passed = True

    for event in test_events:
        event_type = event.pop("type")
        prompt = get_event_prompt(event_type, **event)

        print(f"\n{event_type.upper()}")
        print("-" * 70)

        # Check for general patterns
        missing_patterns = []
        for pattern in general_patterns:
            if pattern.lower() not in prompt.lower():
                missing_patterns.append(pattern)
                all_passed = False

        if missing_patterns:
            print(f"✗ Missing patterns: {', '.join(missing_patterns)}")
        else:
            print(f"✓ Contains all general patterns")

        # Check it's not overly specific
        overly_specific = [
            "systemctl",  # Too specific - should say "service management"
            "journalctl", # Too specific - should say "logs"
            "nginx",      # Service-specific
            "postgresql", # Service-specific
            "port 80",    # Port-specific
            "apt-get",    # Package manager specific
            "yum",        # Package manager specific
        ]

        found_specific = [s for s in overly_specific if s in prompt.lower()]
        if found_specific:
            print(f"⚠ Contains specific terms: {', '.join(found_specific)}")
            print(f"  (Should be general-purpose)")
        else:
            print(f"✓ Appropriately general (no over-specific terms)")

        # Show length
        print(f"  Prompt length: {len(prompt)} chars, {len(prompt.split())} words")

    print("\n" + "=" * 70)

    if all_passed:
        print("✓ All prompts contain general patterns!")
    else:
        print("✗ Some prompts missing general patterns")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(test_prompts())
