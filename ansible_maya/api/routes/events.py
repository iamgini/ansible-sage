# Copyright 2026 Ansible Maya Contributors
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

"""API routes for event handling and playbook generation."""

import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ansible_maya.core.exceptions import PlaybookGenerationError, ValidationError
from ansible_maya.core.providers import get_provider
from ansible_maya.handlers.orchestrator import (
    AIOpsEvent,
    AutomationMode,
    EventSeverity,
    PlaybookOrchestrator,
)

router = APIRouter()


# Request/Response Models


class EventRequest(BaseModel):
    """Request model for event handling."""

    event_type: str = Field(..., description="Type of infrastructure event")
    description: str = Field(..., description="Detailed event description")
    host: str = Field(..., description="Target host or hostname")
    severity: EventSeverity = Field(
        default=EventSeverity.MEDIUM, description="Event severity level"
    )
    metadata: Optional[dict] = Field(default=None, description="Additional event metadata")
    tags: Optional[List[str]] = Field(default=None, description="Event tags")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "disk_full",
                "description": "Disk usage at 95% on /var partition",
                "host": "web-server-01.example.com",
                "severity": "high",
                "metadata": {"partition": "/var", "usage_percent": 95},
                "tags": ["disk", "storage", "critical"],
            }
        }


class PlaybookGenerationResponse(BaseModel):
    """Response model for playbook generation."""

    event_id: str
    playbook: str
    mode: str
    confidence_score: float
    confidence_level: str
    requires_approval: bool
    recommended_action: str
    validation_passed: bool
    validation_issues: List[dict]
    generation_metadata: dict


class EventListRequest(BaseModel):
    """Request model for batch event handling."""

    events: List[EventRequest]
    parallel: bool = Field(
        default=False, description="Process events in parallel (experimental)"
    )


# Routes


@router.post(
    "/generate",
    response_model=PlaybookGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate playbook from event",
    description="Generate an Ansible playbook from an infrastructure event using AI",
)
async def generate_playbook_from_event(request: EventRequest):
    """
    Generate Ansible playbook from infrastructure event.

    This endpoint:
    1. Receives an infrastructure event
    2. Classifies the event (known/complex/unknown)
    3. Generates appropriate Ansible playbook using LLM
    4. Validates with ansible-lint
    5. Returns playbook with execution recommendation
    """
    # Get LLM provider from environment
    provider_name = os.getenv("LLM_PROVIDER", "claude").lower()
    provider_config = {}

    if provider_name in ["claude", "anthropic"]:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ANTHROPIC_API_KEY not configured",
            )
        provider_config["api_key"] = api_key
    elif provider_name == "custom":
        # Custom OpenAI-compatible provider (LiteLLM, vLLM, etc.)
        endpoint = os.getenv("CUSTOM_LLM_ENDPOINT")
        if not endpoint:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="CUSTOM_LLM_ENDPOINT not configured",
            )
        provider_config["endpoint"] = endpoint
        provider_config["api_key"] = os.getenv("CUSTOM_LLM_API_KEY", "dummy-key")
        provider_config["model"] = os.getenv("CUSTOM_LLM_MODEL", "gpt-4")

    try:
        provider = get_provider(provider_name, config=provider_config)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Create event object
    event = AIOpsEvent(
        event_id=f"evt-{int(datetime.now().timestamp())}",
        event_type=request.event_type,
        description=request.description,
        host=request.host,
        severity=request.severity,
        timestamp=datetime.now(),
        metadata=request.metadata,
        tags=request.tags,
    )

    # Initialize orchestrator
    # For demo: disable ansible-lint validation (not in minimal container)
    orchestrator = PlaybookOrchestrator(
        provider=provider,
        auto_fix_lint=False,
        strict_validation=False,
    )

    # Handle event
    try:
        response = await orchestrator.handle_event(event)
    except PlaybookGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Playbook generation failed: {str(e)}",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed: {str(e)}",
        )

    # Format validation issues
    validation_issues = [
        {
            "rule_id": issue.rule_id,
            "message": issue.message,
            "severity": issue.severity,
            "line": issue.line,
            "column": issue.column,
            "task_name": issue.task_name,
        }
        for issue in response.validation_result.issues
    ]

    return PlaybookGenerationResponse(
        event_id=event.event_id,
        playbook=response.playbook,
        mode=response.mode.value,
        confidence_score=response.confidence_score,
        confidence_level=response.confidence_level,
        requires_approval=response.requires_approval,
        recommended_action=response.recommended_action,
        validation_passed=response.validation_result.passed,
        validation_issues=validation_issues,
        generation_metadata=response.generation_metadata,
    )


@router.post(
    "/batch",
    summary="Generate playbooks for multiple events",
    description="Generate Ansible playbooks for multiple infrastructure events",
)
async def generate_playbooks_batch(request: EventListRequest):
    """
    Generate playbooks for multiple events.

    Useful for processing multiple events from monitoring systems.
    """
    results = []
    errors = []

    for idx, event_req in enumerate(request.events):
        try:
            result = await generate_playbook_from_event(event_req)
            results.append({"index": idx, "event_type": event_req.event_type, "result": result})
        except HTTPException as e:
            errors.append(
                {"index": idx, "event_type": event_req.event_type, "error": e.detail}
            )
        except Exception as e:
            errors.append(
                {"index": idx, "event_type": event_req.event_type, "error": str(e)}
            )

    return {
        "total": len(request.events),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }


@router.get(
    "/event-types",
    summary="List supported event types",
    description="Get list of known event types and their automation modes",
)
async def list_event_types():
    """
    List supported event types.

    Returns known event types and their default automation modes.
    """
    return {
        "known_safe_events": list(PlaybookOrchestrator.KNOWN_SAFE_EVENTS),
        "approval_required_events": list(PlaybookOrchestrator.APPROVAL_REQUIRED_EVENTS),
        "automation_modes": {
            "auto": "High confidence - automated execution",
            "approval": "Medium confidence - requires approval",
            "collaborative": "Low confidence - human collaboration needed",
        },
        "confidence_levels": {
            "high": ">=80% - Production ready",
            "medium": "50-80% - Review recommended",
            "low": "<50% - Testing required",
        },
        "severity_levels": [s.value for s in EventSeverity],
    }


