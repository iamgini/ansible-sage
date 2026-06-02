#!/bin/bash
# Test Case: Security Package Update
# Use Case: Critical OpenSSL vulnerability needs patching

set -e

echo "=========================================="
echo "Test: Security Package Update"
echo "=========================================="
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "package_update",
    "description": "Critical security updates available for OpenSSL (CVE-2024-XXXXX). Affected versions must be patched immediately.",
    "host": "prod-web-cluster",
    "severity": "critical",
    "metadata": {
      "package": "openssl",
      "current_version": "1.1.1k",
      "patched_version": "1.1.1w",
      "cve": "CVE-2024-XXXXX",
      "severity_score": 9.8
    },
    "tags": ["security", "cve", "openssl", "patch"]
  }')

if echo "$response" | grep -q "detail"; then
  echo "❌ Error:"
  echo "$response" | python3 -m json.tool
  exit 1
fi

echo "$response" | python3 << 'PYEOF'
import sys, json
data = json.loads(sys.stdin.read())

print(f"✅ Security Remediation Playbook Generated!")
print(f"")
print(f"🔒 Security Details:")
print(f"  Confidence:      {data['confidence_score']*100}%")
print(f"  Approval Needed: {data['requires_approval']}")
print(f"  Target Branch:   {data['target_branch']}")
print(f"")
print(f"📋 Recommendation:")
print(f"  {data['recommended_action']}")
print(f"")

import os
os.makedirs("playbooks", exist_ok=True)
with open("playbooks/security_openssl_update.yml", 'w') as f:
    f.write(data['playbook'])

print("💾 Saved to: playbooks/security_openssl_update.yml")

# Show first 25 lines
print("\n📝 Preview:")
for i, line in enumerate(data['playbook'].split('\n')[:25], 1):
    print(f"{i:3d} | {line}")
print("...")
PYEOF

echo ""
echo "✅ Test completed!"
