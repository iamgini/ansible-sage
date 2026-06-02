#!/bin/bash
# Copyright 2026 Ansible Sage Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# API Usage Examples for Ansible Sage
# Demonstrates how to interact with the REST API

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API endpoint
API_URL="${API_URL:-http://localhost:8000}"

echo -e "${BLUE}===================================================================="
echo "Ansible Sage - API Usage Examples"
echo -e "====================================================================${NC}\n"

# Check if API is running
echo -e "${BLUE}1. Checking API Health...${NC}"
health=$(curl -s "${API_URL}/health")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ API is running${NC}"
    echo "$health" | jq .
else
    echo -e "${RED}✗ API is not running${NC}"
    echo "Start the API with: make run"
    echo "Or: uvicorn sage.api.server:app --reload"
    exit 1
fi

# List supported event types
echo -e "\n${BLUE}2. Listing Supported Event Types...${NC}"
curl -s "${API_URL}/api/v1/events/event-types" | jq .

# Generate playbook for disk full event
echo -e "\n${BLUE}3. Generating Playbook for Disk Full Event...${NC}"
disk_full_response=$(curl -s -X POST "${API_URL}/api/v1/events/generate" \
    -H "Content-Type: application/json" \
    -d '{
      "event_type": "disk_full",
      "description": "Disk usage at 95% on /var partition, logs consuming most space",
      "host": "web-server-01.example.com",
      "severity": "high",
      "metadata": {
        "partition": "/var",
        "usage_percent": 95,
        "largest_dir": "/var/log"
      },
      "tags": ["disk", "storage", "production"]
    }')

echo "$disk_full_response" | jq .

# Extract and save playbook
event_id=$(echo "$disk_full_response" | jq -r '.event_id')
playbook=$(echo "$disk_full_response" | jq -r '.playbook')

if [ ! -z "$playbook" ] && [ "$playbook" != "null" ]; then
    echo -e "\n${GREEN}✓ Playbook generated successfully!${NC}"

    # Save to file
    filename="generated_${event_id}.yml"
    echo "$playbook" > "$filename"
    echo -e "${GREEN}✓ Saved to: $filename${NC}"

    # Show validation status
    validation_passed=$(echo "$disk_full_response" | jq -r '.validation_passed')
    if [ "$validation_passed" = "true" ]; then
        echo -e "${GREEN}✓ Playbook passed validation${NC}"
    else
        echo -e "${RED}⚠ Playbook has validation issues:${NC}"
        echo "$disk_full_response" | jq '.validation_issues'
    fi

    # Show recommendation
    echo -e "\n${BLUE}Recommendation:${NC}"
    echo "$disk_full_response" | jq -r '.recommended_action'
else
    echo -e "${RED}✗ Playbook generation failed${NC}"
fi

# Generate playbook for service down event
echo -e "\n${BLUE}4. Generating Playbook for Service Down Event...${NC}"
service_down_response=$(curl -s -X POST "${API_URL}/api/v1/events/generate" \
    -H "Content-Type: application/json" \
    -d '{
      "event_type": "service_down",
      "description": "Nginx service is not responding on port 80",
      "host": "web-server-02.example.com",
      "severity": "critical",
      "metadata": {
        "service": "nginx",
        "port": 80,
        "status": "inactive"
      }
    }')

echo "$service_down_response" | jq -r '.playbook'

# Batch generation example
echo -e "\n${BLUE}5. Batch Playbook Generation (Multiple Events)...${NC}"
batch_response=$(curl -s -X POST "${API_URL}/api/v1/events/batch" \
    -H "Content-Type: application/json" \
    -d '{
      "events": [
        {
          "event_type": "disk_cleanup_tmp",
          "description": "Clean /tmp directory",
          "host": "app-server-01",
          "severity": "low"
        },
        {
          "event_type": "service_restart_nginx",
          "description": "Restart nginx after config change",
          "host": "web-server-01",
          "severity": "medium"
        },
        {
          "event_type": "high_memory",
          "description": "Memory usage at 92%",
          "host": "db-server-01",
          "severity": "high",
          "metadata": {
            "memory_percent": 92,
            "available_mb": 200
          }
        }
      ]
    }')

echo "$batch_response" | jq '{ total, successful, failed }'

echo -e "\n${BLUE}6. Accessing API Documentation...${NC}"
echo "Interactive API docs available at:"
echo "  • Swagger UI: ${API_URL}/docs"
echo "  • ReDoc:      ${API_URL}/redoc"

echo -e "\n${GREEN}===================================================================="
echo "Examples Complete!"
echo -e "====================================================================${NC}\n"
