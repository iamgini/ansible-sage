#!/usr/bin/env python3
"""Test temperature tuning for different event types."""

import sys
from pathlib import Path

# Add ansible_maya to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ansible_maya.core.prompt_templates import get_optimal_temperature, TEMPERATURE_BY_EVENT


def test_temperature_tuning():
    """Test that different event types get appropriate temperatures."""

    print("Testing Event-Specific Temperature Tuning")
    print("=" * 60)

    # Test all event types
    test_cases = [
        ('disk_full', 0.2, 'Deterministic cleanup tasks'),
        ('service_down', 0.3, 'Service-specific with some variation'),
        ('high_cpu', 0.5, 'Investigative, needs creativity'),
        ('high_memory', 0.4, 'Investigative but constrained'),
        ('generic', 0.3, 'Balanced default'),
        ('unknown_event', 0.3, 'Falls back to default'),
    ]

    all_passed = True

    for event_type, expected_temp, description in test_cases:
        actual_temp = get_optimal_temperature(event_type)
        status = "✓" if actual_temp == expected_temp else "✗"

        if actual_temp != expected_temp:
            all_passed = False

        print(f"{status} {event_type:20s} -> {actual_temp:.1f} (expected {expected_temp:.1f})")
        print(f"   {description}")

    print("\n" + "=" * 60)

    # Test refinement mode
    print("\nRefinement Mode (70% of base temperature):")
    print("-" * 60)

    refinement_cases = [
        ('disk_full', 0.14),
        ('service_down', 0.21),
        ('high_cpu', 0.35),
    ]

    for event_type, expected_temp in refinement_cases:
        actual_temp = get_optimal_temperature(event_type, is_refinement=True)
        status = "✓" if abs(actual_temp - expected_temp) < 0.01 else "✗"

        if abs(actual_temp - expected_temp) >= 0.01:
            all_passed = False

        print(f"{status} {event_type:20s} -> {actual_temp:.2f} (expected {expected_temp:.2f})")

    print("\n" + "=" * 60)

    if all_passed:
        print("✓ All temperature tests passed!")
        return 0
    else:
        print("✗ Some temperature tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(test_temperature_tuning())
