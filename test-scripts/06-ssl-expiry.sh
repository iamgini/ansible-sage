#!/bin/bash
# Test Case: SSL Certificate Expiring Soon
# Use Case: Website SSL certificate expires in 7 days

set -e

echo "=========================================="
echo "Test: SSL Certificate Renewal"
echo "=========================================="
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "ssl_expiring",
    "description": "SSL certificate for www.example.com expires in 7 days. Certificate must be renewed.",
    "host": "web-server-01.example.com",
    "severity": "high",
    "metadata": {
      "domain": "www.example.com",
      "days_remaining": 7,
      "expiry_date": "2026-06-09",
      "issuer": "Lets Encrypt",
      "certificate_type": "DV"
    },
    "tags": ["ssl", "certificate", "security", "https"]
  }')

if echo "$response" | grep -q "detail"; then
  echo "❌ Error:"
  echo "$response" | python3 -m json.tool
  exit 1
fi

echo "$response" | python3 << 'PYEOF'
import sys, json
data = json.loads(sys.stdin.read())

print(f"✅ SSL Renewal Playbook Generated!")
print(f"Event ID: {data['event_id']}")
print(f"Confidence: {data['confidence_score']*100}%")

import os
os.makedirs("playbooks", exist_ok=True)
with open("playbooks/ssl_renewal.yml", 'w') as f:
    f.write(data['playbook'])

print("\n💾 Saved to: playbooks/ssl_renewal.yml")
PYEOF

echo ""
echo "✅ Test completed!"
