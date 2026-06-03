# Ansible Maya Test Scripts

Collection of test scripts to demonstrate Ansible Maya playbook generation capabilities.

## Prerequisites

- Ansible Maya container running: `podman ps | grep ansible-maya`
- API accessible on http://localhost:8000
- Python 3 with json module

## Quick Start

Make all scripts executable:
```bash
chmod +x *.sh
```

Run a single test:
```bash
./01-disk-full.sh
```

Run all tests:
```bash
./run-all-tests.sh
```

Interactive test (custom events):
```bash
./10-interactive-test.sh
```

## Test Cases

### 01-disk-full.sh
**Scenario:** /var/log partition at 95% capacity  
**Severity:** High  
**Expected Output:** Playbook to clean logs, rotate files, free up space

### 02-high-cpu.sh
**Scenario:** CPU spike to 98% on app server  
**Severity:** Critical  
**Expected Output:** Playbook to identify and manage high-CPU processes

### 03-service-down.sh
**Scenario:** Nginx web server stopped  
**Severity:** Critical  
**Expected Output:** Playbook to restart service and verify health

### 04-memory-leak.sh
**Scenario:** Memory increasing from 40% to 92%  
**Severity:** High  
**Expected Output:** Playbook to investigate and address memory leak

### 05-package-update.sh
**Scenario:** Critical OpenSSL security update  
**Severity:** Critical  
**Expected Output:** Playbook to patch OpenSSL with minimal downtime

### 06-ssl-expiry.sh
**Scenario:** SSL certificate expires in 7 days  
**Severity:** High  
**Expected Output:** Playbook to renew Let's Encrypt certificate

### 07-database-slow.sh
**Scenario:** PostgreSQL queries 5x slower  
**Severity:** High  
**Expected Output:** Playbook for database performance tuning

### 08-backup-failure.sh
**Scenario:** Nightly backup failed - disk quota  
**Severity:** High  
**Expected Output:** Playbook to clean backup volume and retry

### 09-network-latency.sh
**Scenario:** App-to-DB latency increased 75x  
**Severity:** High  
**Expected Output:** Playbook for network diagnostics

### 10-interactive-test.sh
**Scenario:** User-defined custom event  
**Severity:** User-selected  
**Expected Output:** Custom playbook based on input

## Output

All generated playbooks are saved to the `playbooks/` directory with descriptive filenames.

Example:
```
playbooks/
├── disk_full_web-server-01.yml
├── high_cpu_app-server-03.yml
├── service_down_nginx.yml
└── ...
```

## Viewing Results

**Quick preview:**
```bash
head -50 playbooks/disk_full_web-server-01.yml
```

**Full playbook:**
```bash
cat playbooks/disk_full_web-server-01.yml
```

**View all generated playbooks:**
```bash
ls -lh playbooks/
```

## Customization

Edit any test script to modify:
- Event type
- Description
- Target host
- Severity level
- Metadata fields
- Tags

## Troubleshooting

**Container not running:**
```bash
podman ps | grep ansible-maya
# If not running:
podman start ansible-maya
```

**API not responding:**
```bash
curl http://localhost:8000/health
```

**View container logs:**
```bash
podman logs ansible-maya
```

**Clean up old playbooks:**
```bash
rm -rf playbooks/*
```

## Advanced Usage

**Extract just the playbook (no metadata):**
```bash
curl -s -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{"event_type":"disk_full","description":"Disk at 95%","host":"web01","severity":"high"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['playbook'])"
```

**Get generation metadata only:**
```bash
curl -s -X POST http://localhost:8000/api/v1/events/generate \
  -H "Content-Type: application/json" \
  -d '{"event_type":"disk_full","description":"Disk at 95%","host":"web01","severity":"high"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"Model: {d['generation_metadata']['model']}\nTokens: {d['generation_metadata']['tokens_used']}\nLatency: {d['generation_metadata']['latency_ms']}ms\")"
```

## Integration with AAP

To upload a generated playbook to Ansible Automation Platform:

1. Copy playbook to AAP project directory
2. Commit to Git (if using SCM)
3. Create job template in AAP
4. Run the playbook

Or use the API (when AAP integration is enabled):
```bash
# Future feature - not yet implemented in demo
curl -X POST http://localhost:8000/api/v1/events/publish-to-aap \
  -H "Content-Type: application/json" \
  -d '{"event_id":"evt-123","playbook":"...","aap_template_id":42}'
```

## Support

For issues or questions:
- Check container logs: `podman logs ansible-maya-demo`
- Verify API health: `curl http://localhost:8000/health`
- Review main README: `/home/gmadappa/ansible/ansible-maya/README.md`
