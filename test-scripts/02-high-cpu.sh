#!/bin/bash
# Test Case: High CPU Usage
# Use Case: CPU spike on application server

set -e

echo "=========================================="
echo "Test: High CPU Usage Remediation"
echo "=========================================="
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "high_cpu",
    "description": "CPU usage spiked to 98% on application server. Multiple Java processes consuming resources.",
    "host": "app-server-03.prod.example.com",
    "severity": "critical",
    "metadata": {
      "cpu_percent": 98,
      "load_average": "12.5, 10.2, 8.1",
      "top_process": "java",
      "process_count": 15
    },
    "tags": ["cpu", "performance", "java"]
  }')

if echo "$response" | grep -q "detail"; then
  echo "❌ Error occurred:"
  echo "$response" | python3 -m json.tool
  exit 1
fi

echo "$response" | python3 << 'PYEOF'
import sys, json
data = json.loads(sys.stdin.read())

print(f"✅ Playbook Generated!")
print(f"Event ID: {data['event_id']}")
print(f"Confidence: {data['confidence_score']*100}% ({data['confidence_level']})")
print(f"Tokens: {data['generation_metadata']['tokens_used']}")
print(f"")
print("📝 Playbook saved to: playbooks/high_cpu_app-server-03.yml")

import os
os.makedirs("playbooks", exist_ok=True)
with open("playbooks/high_cpu_app-server-03.yml", 'w') as f:
    f.write(data['playbook'])

print("\n✅ First 30 lines:")
for i, line in enumerate(data['playbook'].split('\n')[:30], 1):
    print(f"{i:3d} | {line}")
PYEOF

echo ""
echo "✅ Test completed!"
