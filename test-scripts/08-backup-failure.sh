#!/bin/bash
# Test Case: Backup Job Failed
# Use Case: Nightly database backup did not complete

set -e

echo "=========================================="
echo "Test: Backup Failure Recovery"
echo "=========================================="
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "backup_failed",
    "description": "Nightly PostgreSQL backup job failed with error: disk quota exceeded on backup volume.",
    "host": "backup-server-01.example.com",
    "severity": "high",
    "metadata": {
      "backup_type": "postgresql",
      "scheduled_time": "02:00",
      "failure_time": "02:45",
      "error": "disk quota exceeded",
      "backup_size_expected": "50GB",
      "backup_volume": "/backup",
      "last_successful_backup": "2026-06-01"
    },
    "tags": ["backup", "postgresql", "storage", "disaster-recovery"]
  }')

if echo "$response" | grep -q "detail"; then
  echo "❌ Error:"
  echo "$response" | python3 -m json.tool
  exit 1
fi

echo "$response" | python3 << 'PYEOF'
import sys, json
data = json.loads(sys.stdin.read())

print(f"✅ Backup Recovery Playbook Generated!")
print(f"")
print(f"💾 Details:")
print(f"  Event ID:    {data['event_id']}")
print(f"  Confidence:  {data['confidence_score']*100}%")
print(f"  Validation:  {'✅ Passed' if data['validation_passed'] else '❌ Failed'}")
print(f"")

import os
os.makedirs("playbooks", exist_ok=True)
with open("playbooks/backup_failure_recovery.yml", 'w') as f:
    f.write(data['playbook'])

print("📁 Saved to: playbooks/backup_failure_recovery.yml")
PYEOF

echo ""
echo "✅ Test completed!"
