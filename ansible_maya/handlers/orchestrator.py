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

"""
Main orchestrator for event-driven playbook generation.

Implements multi-mode automation:
1. Known events → Auto-execute (if approved)
2. Complex events → Generate + Human approval
3. Unknown events → Collaborative investigation
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ansible_maya.core.ansible_context import AnsibleContextProcessor
from ansible_maya.core.exceptions import (
    EventClassificationError,
    PlaybookGenerationError,
    ValidationError,
)
from ansible_maya.core.providers.base import (
    BaseLLMProvider,
    GenerationRequest,
    ModelTier,
)
from ansible_maya.validation.ansible_lint import validate_playbook, LintResult

logger = logging.getLogger(__name__)


class EventSeverity(Enum):
    """Event severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AutomationMode(Enum):
    """Automation execution modes."""

    AUTO = "auto"  # Automatically execute for known safe events
    APPROVAL = "approval"  # Generate but require human approval
    COLLABORATIVE = "collaborative"  # Work with human for unknown events


@dataclass
class AIOpsEvent:
    """Infrastructure event from monitoring systems."""

    event_id: str
    event_type: str
    description: str
    host: str
    severity: EventSeverity
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


@dataclass
class PlaybookResponse:
    """Response from playbook generation and validation."""

    playbook: str
    event: AIOpsEvent
    mode: AutomationMode
    validation_result: LintResult
    generation_metadata: Dict[str, Any]
    confidence_score: float  # 0.0 - 1.0
    confidence_level: str  # "high", "medium", "low"
    requires_approval: bool = False
    recommended_action: Optional[str] = None


class PlaybookOrchestrator:
    """
    Main orchestrator for event-driven Ansible playbook generation.

    Workflow:
    1. Receive event
    2. Classify event (known/complex/unknown)
    3. Determine automation mode
    4. Generate playbook using LLM
    5. Validate with ansible-lint
    6. Return for execution or approval
    """

    # Known safe event types that can auto-execute
    KNOWN_SAFE_EVENTS = {
        "disk_cleanup_tmp",
        "service_restart_nginx",
        "package_cache_clear",
        "log_rotation",
    }

    # Events requiring approval before execution
    APPROVAL_REQUIRED_EVENTS = {
        "disk_full",
        "service_down",
        "high_cpu",
        "high_memory",
        "database_connection_pool_full",
    }

    def __init__(
        self,
        provider: BaseLLMProvider,
        auto_fix_lint: bool = True,
        strict_validation: bool = False,
    ):
        """
        Initialize orchestrator.

        Args:
            provider: LLM provider for playbook generation
            auto_fix_lint: Automatically fix ansible-lint issues
            strict_validation: Treat lint warnings as errors
        """
        self.provider = provider
        self.auto_fix_lint = auto_fix_lint
        self.strict_validation = strict_validation
        self.context_processor = AnsibleContextProcessor()

    async def handle_event(
        self,
        event: AIOpsEvent,
        existing_playbooks: Optional[List[str]] = None,
    ) -> PlaybookResponse:
        """
        Main entry point for event handling.

        Args:
            event: Infrastructure event to remediate
            existing_playbooks: Optional existing playbooks for context

        Returns:
            PlaybookResponse with generated playbook and metadata

        Raises:
            EventClassificationError: If event cannot be classified
            PlaybookGenerationError: If generation fails
        """
        logger.info(
            f"Handling event: {event.event_id}",
            extra={
                "event_type": event.event_type,
                "host": event.host,
                "severity": event.severity.value,
            },
        )

        # Determine automation mode
        mode = self._classify_event(event)

        logger.info(f"Event classified as {mode.value} mode")

        # Generate playbook
        try:
            playbook, generation_metadata = await self._generate_playbook(
                event, existing_playbooks, mode
            )
        except Exception as e:
            logger.error(f"Playbook generation failed: {str(e)}")
            raise PlaybookGenerationError(f"Failed to generate playbook: {str(e)}")

        # Validate playbook
        try:
            validation_result = await self._validate_playbook(playbook)
        except Exception as e:
            logger.error(f"Playbook validation failed: {str(e)}")
            raise ValidationError(f"Validation failed: {str(e)}")

        # If validation failed and auto-fix is disabled, raise error
        if not validation_result.passed and not self.auto_fix_lint:
            raise ValidationError(
                f"Playbook validation failed with {len(validation_result.issues)} issues"
            )

        # If validation still failing after auto-fix attempts, try refinement
        if not validation_result.passed:
            logger.info("Attempting to refine playbook to fix validation issues")
            playbook, validation_result = await self._refine_playbook(
                playbook, validation_result
            )

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            event, mode, validation_result, generation_metadata
        )
        confidence_level = self._get_confidence_level(confidence_score)

        # Determine if approval is required
        requires_approval = mode != AutomationMode.AUTO or event.severity in (
            EventSeverity.HIGH,
            EventSeverity.CRITICAL,
        )

        # Generate recommended action
        recommended_action = self._generate_recommendation(
            event, mode, validation_result, confidence_score
        )

        return PlaybookResponse(
            playbook=playbook,
            event=event,
            mode=mode,
            validation_result=validation_result,
            generation_metadata=generation_metadata,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            requires_approval=requires_approval,
            recommended_action=recommended_action,
        )

    def _classify_event(self, event: AIOpsEvent) -> AutomationMode:
        """
        Classify event to determine automation mode.

        Args:
            event: Event to classify

        Returns:
            Appropriate AutomationMode
        """
        # Known safe events can auto-execute (unless critical severity)
        if event.event_type in self.KNOWN_SAFE_EVENTS:
            if event.severity == EventSeverity.CRITICAL:
                return AutomationMode.APPROVAL
            return AutomationMode.AUTO

        # Known events requiring approval
        if event.event_type in self.APPROVAL_REQUIRED_EVENTS:
            return AutomationMode.APPROVAL

        # Unknown events need collaborative investigation
        return AutomationMode.COLLABORATIVE

    async def _generate_playbook(
        self,
        event: AIOpsEvent,
        existing_playbooks: Optional[List[str]],
        mode: AutomationMode,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Generate playbook using LLM provider.

        Args:
            event: Event to remediate
            existing_playbooks: Existing playbooks for context
            mode: Automation mode

        Returns:
            Tuple of (playbook_content, generation_metadata)
        """
        # Select model tier based on complexity
        if mode == AutomationMode.AUTO:
            tier = ModelTier.FAST  # Simple known events
        elif mode == AutomationMode.APPROVAL:
            tier = ModelTier.BALANCED  # Standard events
        else:
            tier = ModelTier.PREMIUM  # Complex/unknown events

        # Build generation request
        request = GenerationRequest(
            event_description=event.description,
            event_type=event.event_type,
            host=event.host,
            existing_playbooks=existing_playbooks,
            model_tier=tier,
            temperature=0.3 if mode == AutomationMode.AUTO else 0.5,
            constraints=event.metadata,
        )

        # Generate using provider
        response = await self.provider.generate_playbook(request)

        metadata = {
            "model": response.model,
            "provider": response.provider,
            "tokens_used": response.tokens_used,
            "latency_ms": response.latency_ms,
            "mode": mode.value,
            **response.metadata,
        }

        return response.playbook, metadata

    async def _validate_playbook(self, playbook: str) -> LintResult:
        """
        Validate playbook with ansible-lint.

        Args:
            playbook: Playbook content to validate

        Returns:
            LintResult
        """
        return await validate_playbook(
            playbook,
            auto_fix=self.auto_fix_lint,
            strict=self.strict_validation,
        )

    async def _refine_playbook(
        self, playbook: str, validation_result: LintResult
    ) -> tuple[str, LintResult]:
        """
        Refine playbook to fix validation issues using LLM.

        Args:
            playbook: Original playbook
            validation_result: Validation result with issues

        Returns:
            Tuple of (refined_playbook, new_validation_result)
        """
        # Check if provider supports refinement
        if not hasattr(self.provider, "refine_playbook"):
            logger.warning("Provider does not support refinement, returning original")
            return playbook, validation_result

        # Format issues for LLM
        issues_text = "\n".join(
            [f"- [{issue.rule_id}] {issue.message}" for issue in validation_result.issues]
        )

        # Refine using LLM
        refinement_response = await self.provider.refine_playbook(
            original_playbook=playbook,
            issues=issues_text,
        )

        # Validate refined playbook
        new_validation = await self._validate_playbook(refinement_response.playbook)

        logger.info(
            f"Refinement result: {len(validation_result.issues)} → {len(new_validation.issues)} issues"
        )

        return refinement_response.playbook, new_validation

    def _calculate_confidence_score(
        self,
        event: AIOpsEvent,
        mode: AutomationMode,
        validation: LintResult,
        generation_metadata: Dict[str, Any],
    ) -> float:
        """
        Calculate confidence score for generated playbook.

        Factors:
        - Event type known: +0.3
        - Validation passed: +0.4
        - No validation errors (warnings ok): +0.2
        - Low severity: +0.1
        - Known safe event: +0.2

        Args:
            event: Original event
            mode: Automation mode
            validation: Validation result
            generation_metadata: Generation metadata

        Returns:
            Confidence score (0.0 - 1.0)
        """
        score = 0.0

        # Base score from mode
        if mode == AutomationMode.AUTO:
            score += 0.3  # Known safe event
        elif mode == AutomationMode.APPROVAL:
            score += 0.2  # Known event
        else:
            score += 0.1  # Unknown event

        # Validation score
        if validation.passed:
            score += 0.4  # Clean validation
        elif not any(issue.severity == "error" for issue in validation.issues):
            score += 0.2  # Only warnings

        # Issue count penalty
        if validation.issues:
            penalty = min(len(validation.issues) * 0.05, 0.2)
            score -= penalty

        # Severity bonus (lower severity = higher confidence)
        if event.severity == EventSeverity.LOW:
            score += 0.1
        elif event.severity == EventSeverity.CRITICAL:
            score -= 0.1

        # Known event type bonus
        if event.event_type in (
            self.KNOWN_SAFE_EVENTS | self.APPROVAL_REQUIRED_EVENTS
        ):
            score += 0.2

        # Ensure in range [0.0, 1.0]
        return max(0.0, min(1.0, score))

    def _get_confidence_level(self, score: float) -> str:
        """Get confidence level label from score."""
        if score >= 0.80:
            return "high"
        elif score >= 0.50:
            return "medium"
        else:
            return "low"

    def _generate_recommendation(
        self,
        event: AIOpsEvent,
        mode: AutomationMode,
        validation: LintResult,
        confidence_score: float,
    ) -> str:
        """
        Generate recommended action based on event and validation.

        Args:
            event: Original event
            mode: Determined automation mode
            validation: Validation result
            confidence_score: Calculated confidence score

        Returns:
            Human-readable recommendation
        """
        confidence_level = self._get_confidence_level(confidence_score)

        if not validation.passed:
            return (
                f"❌ Playbook has validation issues. "
                f"Review and fix before execution. "
                f"({len(validation.issues)} issues found)"
            )

        if confidence_level == "high":
            return (
                f"✓ High confidence ({confidence_score:.0%}). "
                f"Production ready - safe to execute."
            )

        if confidence_level == "medium":
            return (
                f"⚠️ Medium confidence ({confidence_score:.0%}). "
                f"Human review recommended before execution."
            )

        return (
            f"⚡ Low confidence ({confidence_score:.0%}). "
            f"Manual review and testing required before execution."
        )


# Convenience function for quick event handling
async def handle_infrastructure_event(
    event_description: str,
    event_type: str,
    host: str,
    provider: BaseLLMProvider,
    severity: EventSeverity = EventSeverity.MEDIUM,
) -> PlaybookResponse:
    """
    Quick helper to handle an infrastructure event.

    Args:
        event_description: Description of the event
        event_type: Type/category of event
        host: Target host
        provider: LLM provider to use
        severity: Event severity level

    Returns:
        PlaybookResponse with generated playbook

    Example:
        >>> from ansible_maya.core.providers import get_provider
        >>> provider = get_provider("claude", config={"api_key": "sk-..."})
        >>> response = await handle_infrastructure_event(
        ...     event_description="Disk usage is 95% on /var",
        ...     event_type="disk_full",
        ...     host="web-server-01",
        ...     provider=provider,
        ... )
        >>> print(response.playbook)
    """
    event = AIOpsEvent(
        event_id=f"evt-{int(datetime.now().timestamp())}",
        event_type=event_type,
        description=event_description,
        host=host,
        severity=severity,
        timestamp=datetime.now(),
    )

    orchestrator = PlaybookOrchestrator(provider=provider)
    return await orchestrator.handle_event(event)
