#!/bin/bash
# Test Case: Database Performance Degradation
# Use Case: PostgreSQL queries running slow

set -e

echo "=========================================="
echo "Test: Database Performance Tuning"
echo "=========================================="
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "database_slow",
    "description": "PostgreSQL database queries running 5x slower than baseline. Response time degraded from 50ms to 250ms average.",
    "host": "db-master-01.prod.example.com",
    "severity": "high",
    "metadata": {
      "database": "postgresql",
      "version": "14.5",
      "avg_query_time": "250ms",
      "baseline_time": "50ms",
      "connections": 180,
      "max_connections": 200,
      "cache_hit_ratio": 0.75
    },
    "tags": ["database", "postgresql", "performance", "slow-query"]
  }')

if echo "$response" | grep -q "detail"; then
  echo "❌ Error:"
  echo "$response" | python3 -m json.tool
  exit 1
fi

echo "$response" | python3 << 'PYEOF'
import sys, json
data = json.loads(sys.stdin.read())

print(f"✅ Database Tuning Playbook Generated!")
print(f"")
print(f"📊 Stats:")
print(f"  Confidence:  {data['confidence_score']*100}%")
print(f"  Model:       {data['generation_metadata']['model']}")
print(f"  Tokens:      {data['generation_metadata']['tokens_used']}")
print(f"  Mode:        {data['mode']}")
print(f"")

import os
os.makedirs("playbooks", exist_ok=True)
with open("playbooks/database_performance_tuning.yml", 'w') as f:
    f.write(data['playbook'])

print("💾 Saved to: playbooks/database_performance_tuning.yml")
print(f"📝 Lines: {len(data['playbook'].split(chr(10)))}")
PYEOF

echo ""
echo "✅ Test completed!"
