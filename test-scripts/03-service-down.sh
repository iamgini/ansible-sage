#!/bin/bash
# Test Case: Service Down
# Use Case: Nginx web server stopped unexpectedly

set -e

echo "=========================================="
echo "Test: Service Down - Nginx Restart"
echo "=========================================="
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "service_down",
    "description": "Nginx service is not running. Health check failed on load balancer.",
    "host": "lb01.prod.example.com",
    "severity": "critical",
    "metadata": {
      "service_name": "nginx",
      "service_state": "inactive",
      "last_restart": "2026-06-01T10:30:00Z",
      "error_log": "Connection refused on port 80"
    },
    "tags": ["nginx", "webserver", "service"]
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
print(f"Confidence: {data['confidence_score']*100}%")
print(f"Mode: {data['mode']}")
print(f"")

import os
os.makedirs("playbooks", exist_ok=True)
filename = "playbooks/service_down_nginx.yml"
with open(filename, 'w') as f:
    f.write(data['playbook'])

print(f"💾 Saved to: {filename}")
print(f"\n📋 Playbook length: {len(data['playbook'].split(chr(10)))} lines")
print(f"⚡ Generated in: {data['generation_metadata']['latency_ms']} ms")
PYEOF

echo ""
echo "✅ Test completed!"
