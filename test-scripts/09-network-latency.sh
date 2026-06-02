#!/bin/bash
# Test Case: Network Latency Issues
# Use Case: High latency between app and database servers

set -e

echo "=========================================="
echo "Test: Network Latency Investigation"
echo "=========================================="
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "network_latency",
    "description": "Network latency between app servers and database increased from 2ms to 150ms. Users experiencing slow page loads.",
    "host": "app-server-cluster",
    "severity": "high",
    "metadata": {
      "source": "app-server-01",
      "destination": "db-master-01",
      "current_latency_ms": 150,
      "baseline_latency_ms": 2,
      "packet_loss": "0.5%",
      "network_segment": "app-to-db"
    },
    "tags": ["network", "latency", "performance", "connectivity"]
  }')

if echo "$response" | grep -q "detail"; then
  echo "❌ Error:"
  echo "$response" | python3 -m json.tool
  exit 1
fi

echo "$response" | python3 << 'PYEOF'
import sys, json
data = json.loads(sys.stdin.read())

print(f"✅ Network Diagnostics Playbook Generated!")
print(f"Confidence: {data['confidence_score']*100}%")
print(f"Mode: {data['mode']}")

import os
os.makedirs("playbooks", exist_ok=True)
with open("playbooks/network_latency_diagnostics.yml", 'w') as f:
    f.write(data['playbook'])

print("\n💾 Saved to: playbooks/network_latency_diagnostics.yml")
print(f"⚡ Generated in {data['generation_metadata']['latency_ms']/1000:.1f}s")
PYEOF

echo ""
echo "✅ Test completed!"
