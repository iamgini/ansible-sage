# Copyright 2026 Ansible Maya Contributors
# Licensed under the Apache License, Version 2.0

"""Events API routes."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ansible_maya.core.multi_agent_pipeline import MultiAgentPipeline
from ansible_maya.core.providers import get_provider
from ansible_maya.handlers.orchestrator import AIOpsEvent, PlaybookOrchestrator

router = APIRouter()


@router.post("/generate")
async def generate_playbook(
    event: AIOpsEvent,
    multi_agent_review: bool = Query(False, description="Enable multi-agent review pipeline"),
):
    """Generate playbook from event.

    Args:
        event: Infrastructure event
        multi_agent_review: Enable multi-agent quality review (slower, higher quality)
    """
    provider = get_provider()
    orchestrator = PlaybookOrchestrator(provider=provider)

    # Generate initial playbook
    response = await orchestrator.handle_event(event)

    # If multi-agent review enabled, refine playbook
    if multi_agent_review:
        pipeline = MultiAgentPipeline(provider)

        refined = await pipeline.generate_with_review(
            draft_playbook=response.playbook, event_description=event.description
        )

        # Update response with refined playbook
        response.playbook = refined["playbook"]
        response.confidence_score = min(
            1.0, response.confidence_score + (refined["confidence_boost"] / 100)
        )
        response.generation_metadata["multi_agent_review"] = refined["reviews"]
        response.generation_metadata["confidence_boost"] = refined["confidence_boost"]

    return response.dict()
