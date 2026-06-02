#!/usr/bin/env python3
# Copyright 2026 Ansible Sage Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Basic usage example for Ansible Sage.

This demonstrates:
1. Creating an event
2. Generating a playbook using Claude
3. Validating the playbook
4. Displaying results
"""

import asyncio
import os
from datetime import datetime

from sage.core.providers import get_provider
from sage.handlers.orchestrator import AIOpsEvent, EventSeverity, PlaybookOrchestrator


async def main():
    """Main example function."""
    print("=" * 70)
    print("Ansible Sage - Basic Usage Example")
    print("=" * 70)

    # 1. Configure LLM Provider
    print("\n1. Configuring LLM Provider (Claude)...")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("   Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        return

    provider = get_provider("claude", config={"api_key": api_key})
    print("✓ Provider configured")

    # 2. Create an Infrastructure Event
    print("\n2. Creating Infrastructure Event...")

    event = AIOpsEvent(
        event_id="example-001",
        event_type="disk_full",
        description="Disk usage at 95% on /var partition due to log accumulation",
        host="web-server-01.production.example.com",
        severity=EventSeverity.HIGH,
        timestamp=datetime.now(),
        metadata={
            "partition": "/var",
            "usage_percent": 95,
            "available_mb": 500,
            "largest_dirs": ["/var/log", "/var/cache"],
        },
        tags=["disk", "storage", "logs", "production"],
    )

    print(f"✓ Event created: {event.event_type} on {event.host}")
    print(f"  Severity: {event.severity.value}")
    print(f"  Description: {event.description}")

    # 3. Initialize Orchestrator
    print("\n3. Initializing Playbook Orchestrator...")

    orchestrator = PlaybookOrchestrator(
        provider=provider,
        auto_fix_lint=True,  # Automatically fix ansible-lint issues
        strict_validation=False,  # Warnings don't fail validation
    )

    print("✓ Orchestrator ready")

    # 4. Generate Playbook
    print("\n4. Generating Ansible Playbook...")
    print("   (This may take 5-10 seconds...)")

    try:
        response = await orchestrator.handle_event(event)
    except Exception as e:
        print(f"❌ Generation failed: {str(e)}")
        return

    print(f"✓ Playbook generated successfully!")

    # 5. Display Results
    print("\n" + "=" * 70)
    print("GENERATION RESULTS")
    print("=" * 70)

    print(f"\nMode: {response.mode.value}")
    print(f"Model: {response.generation_metadata.get('model', 'unknown')}")
    print(f"Tokens Used: {response.generation_metadata.get('tokens_used', 'N/A')}")
    print(f"Latency: {response.generation_metadata.get('latency_ms', 'N/A')}ms")

    print(f"\nValidation: {'✓ PASSED' if response.validation_result.passed else '✗ FAILED'}")
    if response.validation_result.issues:
        print(f"Issues: {len(response.validation_result.issues)}")
        for issue in response.validation_result.issues[:3]:  # Show first 3
            print(f"  - [{issue.rule_id}] {issue.message}")
        if len(response.validation_result.issues) > 3:
            print(f"  ... and {len(response.validation_result.issues) - 3} more")

    print(f"\nRequires Approval: {'Yes' if response.requires_approval else 'No'}")
    print(f"Recommendation: {response.recommended_action}")

    # 6. Display Generated Playbook
    print("\n" + "=" * 70)
    print("GENERATED PLAYBOOK")
    print("=" * 70)
    print()
    print(response.playbook)
    print()
    print("=" * 70)

    # 7. Optional: Save to file
    output_file = f"generated_playbook_{event.event_id}.yml"
    with open(output_file, "w") as f:
        f.write(response.playbook)

    print(f"\n✓ Playbook saved to: {output_file}")
    print("\nYou can now:")
    print(f"  1. Review the playbook: cat {output_file}")
    print(f"  2. Validate manually: ansible-lint {output_file}")
    print(f"  3. Execute: ansible-playbook {output_file} -i your-inventory")


if __name__ == "__main__":
    asyncio.run(main())
