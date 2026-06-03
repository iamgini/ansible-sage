#!/usr/bin/env python3
"""Test session context functionality."""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add ansible_maya to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ansible_maya.core.session_context import SessionContext, EventRecord


def test_session_context():
    """Test session context event tracking and correlation."""

    print("Testing Session Context for Event Correlation")
    print("=" * 70)

    session = SessionContext(ttl_minutes=60)
    all_passed = True

    # Test 1: Add events
    print("\n## Test 1: Add Events")
    print("-" * 70)

    event1 = session.add_event(
        event_type="disk_full",
        host="web-01.example.com",
        description="Disk usage at 92% on /var/log",
        metadata={"disk_usage": 92, "mount_point": "/var/log"},
    )
    print(f"✓ Added event 1: {event1.event_type} on {event1.host}")

    event2 = session.add_event(
        event_type="service_down",
        host="web-01.example.com",
        service="nginx",
        description="Nginx service failed",
        metadata={"service": "nginx", "status": "failed"},
    )
    print(f"✓ Added event 2: {event2.event_type} on {event2.host}")

    event3 = session.add_event(
        event_type="high_cpu",
        host="db-01.example.com",
        description="CPU usage at 95%",
        metadata={"cpu_percent": 95},
    )
    print(f"✓ Added event 3: {event3.event_type} on {event3.host}")

    # Test 2: Get host history
    print("\n## Test 2: Get Host History")
    print("-" * 70)

    web_history = session.get_host_history("web-01.example.com")
    if len(web_history) == 2:
        print(f"✓ Found {len(web_history)} events for web-01.example.com")
        print(f"  - {web_history[0].event_type}")
        print(f"  - {web_history[1].event_type}")
    else:
        print(f"✗ Expected 2 events for web-01, got {len(web_history)}")
        all_passed = False

    db_history = session.get_host_history("db-01.example.com")
    if len(db_history) == 1:
        print(f"✓ Found {len(db_history)} event for db-01.example.com")
    else:
        print(f"✗ Expected 1 event for db-01, got {len(db_history)}")
        all_passed = False

    # Test 3: Get service history
    print("\n## Test 3: Get Service History")
    print("-" * 70)

    nginx_history = session.get_service_history("nginx")
    if len(nginx_history) == 1:
        print(f"✓ Found {len(nginx_history)} event for nginx service")
    else:
        print(f"✗ Expected 1 event for nginx, got {len(nginx_history)}")
        all_passed = False

    # Test 4: Format context for prompt
    print("\n## Test 4: Format Context for Prompt")
    print("-" * 70)

    context = session.format_context_for_prompt(
        host="web-01.example.com",
        current_event_type="disk_full",
        limit=3
    )

    checks = [
        ("Previous Events section", "Previous Events on web-01.example.com" in context),
        ("Event type mentioned", "disk_full" in context or "service_down" in context),
        ("Success indicator", "Success" in context or "Failed" in context),
        ("Metadata included", "Service: nginx" in context or "Disk:" in context),
    ]

    for check_name, check_result in checks:
        status = "✓" if check_result else "✗"
        print(f"{status} {check_name}")
        if not check_result:
            all_passed = False

    print(f"\nContext length: {len(context)} chars")

    # Test 5: Has recent events
    print("\n## Test 5: Has Recent Events Check")
    print("-" * 70)

    has_recent = session.has_recent_events("web-01.example.com", minutes=30)
    if has_recent:
        print(f"✓ Correctly detected recent events for web-01.example.com")
    else:
        print(f"✗ Failed to detect recent events")
        all_passed = False

    no_recent = session.has_recent_events("nonexistent-host.example.com", minutes=30)
    if not no_recent:
        print(f"✓ Correctly reported no events for nonexistent host")
    else:
        print(f"✗ False positive for nonexistent host")
        all_passed = False

    # Test 6: Session statistics
    print("\n## Test 6: Session Statistics")
    print("-" * 70)

    stats = session.get_stats()
    print(f"Total events: {stats['total_events']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Unique hosts: {stats['unique_hosts']}")
    print(f"Unique services: {stats['unique_services']}")
    print(f"Event types: {stats['event_types']}")

    if stats['total_events'] == 3:
        print(f"✓ Correct event count")
    else:
        print(f"✗ Expected 3 events, got {stats['total_events']}")
        all_passed = False

    if stats['unique_hosts'] == 2:
        print(f"✓ Correct unique host count")
    else:
        print(f"✗ Expected 2 unique hosts, got {stats['unique_hosts']}")
        all_passed = False

    # Test 7: Event correlation scenario
    print("\n## Test 7: Event Correlation Scenario")
    print("-" * 70)
    print("Scenario: Multiple disk_full events on same host")

    # Add another disk_full event
    session.add_event(
        event_type="disk_full",
        host="web-01.example.com",
        description="Disk usage at 95% on /var/log",
        success=False,  # Previous remediation didn't work
        metadata={"disk_usage": 95, "mount_point": "/var/log"},
    )

    context = session.format_context_for_prompt(
        host="web-01.example.com",
        current_event_type="disk_full",
        limit=5
    )

    if "This host has had" in context and "disk_full" in context:
        print(f"✓ Context includes correlation note about recurring issues")
    else:
        print(f"✗ Missing correlation note")
        all_passed = False

    if "Failed" in context:
        print(f"✓ Context shows previous remediation failed")
    else:
        print(f"✗ Missing failure indicator")
        all_passed = False

    # Test 8: Clear session
    print("\n## Test 8: Clear Session")
    print("-" * 70)

    session.clear()
    stats_after = session.get_stats()

    if stats_after['total_events'] == 0:
        print(f"✓ Session cleared successfully")
    else:
        print(f"✗ Session not cleared, {stats_after['total_events']} events remain")
        all_passed = False

    print("\n" + "=" * 70)

    if all_passed:
        print("✓ All session context tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(test_session_context())
