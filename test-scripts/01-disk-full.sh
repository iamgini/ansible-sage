#!/bin/bash
# Test Case: Disk Full Event
# Use Case: /var/log partition is at 95% capacity

set -e

echo "=========================================="
echo "Test: Disk Full Remediation"
echo "=========================================="
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "disk_full",
    "description": "Disk usage at 95% on /var/log partition. Need to clean up old log files.",
    "host": "web-server-01.example.com",
    "severity": "high",
    "metadata": {
      "filesystem": "/var/log",
      "usage_percent": 95,
      "available_gb": 2.3
    },
    "tags": ["disk", "storage", "logs"]
  }')

# Check if response has error
if echo "$response" | grep -q "detail"; then
  echo "❌ Error occurred:"
  echo "$response" | python3 -m json.tool
  exit 1
fi

# Extract and display key info
echo "$response" | python3 << 'PYEOF'
import sys, json
try:
    data = json.loads(sys.stdin.read())

    print(f"✅ Playbook Generated!")
    print(f"")
    print(f"Event ID:     {data['event_id']}")
    print(f"Confidence:   {data['confidence_score']*100}% ({data['confidence_level']})")
    print(f"Mode:         {data['mode']}")
    print(f"Target Branch: {data['target_branch']}")
    print(f"Validation:   {'✅ Passed' if data['validation_passed'] else '❌ Failed'}")
    print(f"")
    print(f"Model:        {data['generation_metadata']['model']}")
    print(f"Tokens Used:  {data['generation_metadata']['tokens_used']}")
    print(f"Latency:      {data['generation_metadata']['latency_ms']} ms")
    print(f"")
    print(f"📝 Playbook Preview (first 40 lines):")
    print("=" * 60)

    lines = data['playbook'].split('\n')
    for i, line in enumerate(lines[:40], 1):
        print(f"{i:3d} | {line}")

    if len(lines) > 40:
        print(f"... ({len(lines) - 40} more lines)")

    print("=" * 60)
    print(f"\n💡 Recommendation: {data['recommended_action']}")

    # Save to file
    filename = "playbooks/disk_full_web-server-01.yml"
    import os
    os.makedirs("playbooks", exist_ok=True)
    with open(filename, 'w') as f:
        f.write(data['playbook'])
    print(f"\n💾 Saved to: {filename}")

except json.JSONDecodeError as e:
    print(f"❌ Failed to parse JSON response: {e}")
    sys.exit(1)
PYEOF

echo ""
echo "✅ Test completed!"
