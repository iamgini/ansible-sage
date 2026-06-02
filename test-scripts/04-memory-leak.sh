#!/bin/bash
# Test Case: Memory Leak Detection
# Use Case: Memory usage increasing rapidly on app server

set -e

echo "=========================================="
echo "Test: Memory Leak Investigation"
echo "=========================================="
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "memory_leak",
    "description": "Memory usage increased from 40% to 92% over the last 2 hours. Application performance degrading.",
    "host": "app-server-05.prod.example.com",
    "severity": "high",
    "metadata": {
      "memory_percent": 92,
      "memory_used_gb": 29.5,
      "memory_total_gb": 32,
      "growth_rate": "2GB per hour",
      "suspect_process": "python"
    },
    "tags": ["memory", "leak", "performance"]
  }')

if echo "$response" | grep -q "detail"; then
  echo "❌ Error:"
  echo "$response" | python3 -m json.tool
  exit 1
fi

echo "$response" | python3 << 'PYEOF'
import sys, json
data = json.loads(sys.stdin.read())

print(f"✅ Playbook Generated!")
print(f"")
print(f"📊 Generation Stats:")
print(f"  Model:      {data['generation_metadata']['model']}")
print(f"  Confidence: {data['confidence_score']*100}%")
print(f"  Tokens:     {data['generation_metadata']['tokens_used']}")
print(f"  Time:       {data['generation_metadata']['latency_ms']/1000:.2f}s")
print(f"")

import os
os.makedirs("playbooks", exist_ok=True)
with open("playbooks/memory_leak_investigation.yml", 'w') as f:
    f.write(data['playbook'])

print("💾 Saved to: playbooks/memory_leak_investigation.yml")
print(f"📝 {len(data['playbook'].split(chr(10)))} lines generated")
PYEOF

echo ""
echo "✅ Test completed!"
