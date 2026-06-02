#!/bin/bash
# Interactive Test Script
# Use Case: Custom event testing

set -e

echo "=========================================="
echo "Ansible Sage - Interactive Test"
echo "=========================================="
echo ""
echo "Create your own test event:"
echo ""

read -p "Event Type (e.g., disk_full, high_cpu): " event_type
read -p "Description: " description
read -p "Target Host: " host
read -p "Severity (low/medium/high/critical): " severity

echo ""
echo "🤖 Generating playbook with Qwen3.6-35B-A3B..."
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d "{
    \"event_type\": \"$event_type\",
    \"description\": \"$description\",
    \"host\": \"$host\",
    \"severity\": \"$severity\"
  }")

if echo "$response" | grep -q "detail"; then
  echo "❌ Error occurred:"
  echo "$response" | python3 -m json.tool
  exit 1
fi

echo "$response" | python3 << PYEOF
import sys, json
data = json.loads(sys.stdin.read())

print(f"✅ Playbook Generated Successfully!")
print(f"")
print(f"📊 Generation Details:")
print(f"  Event ID:      {data['event_id']}")
print(f"  Confidence:    {data['confidence_score']*100}% ({data['confidence_level']})")
print(f"  Mode:          {data['mode']}")
print(f"  Target Branch: {data['target_branch']}")
print(f"  Approval Req:  {data['requires_approval']}")
print(f"")
print(f"🤖 Model Info:")
print(f"  Model:    {data['generation_metadata']['model']}")
print(f"  Tokens:   {data['generation_metadata']['tokens_used']}")
print(f"  Latency:  {data['generation_metadata']['latency_ms']} ms")
print(f"")

# Save playbook
import os
os.makedirs("playbooks", exist_ok=True)
filename = f"playbooks/{data['event_type']}_{data['event_id']}.yml"
with open(filename, 'w') as f:
    f.write(data['playbook'])

print(f"💾 Playbook saved to: {filename}")
print(f"")
print(f"📝 Playbook Preview (first 35 lines):")
print("=" * 70)

lines = data['playbook'].split('\n')
for i, line in enumerate(lines[:35], 1):
    print(f"{i:3d} | {line}")

if len(lines) > 35:
    print(f"\n... ({len(lines) - 35} more lines)")

print("=" * 70)
print(f"\n💡 {data['recommended_action']}")
PYEOF

echo ""
echo "✅ Interactive test completed!"
