# Copyright 2026 Ansible Maya Contributors
# Licensed under the Apache License, Version 2.0

"""Multi-agent review pipeline for quality improvement."""

from typing import List, Dict, Any
from pydantic import BaseModel


class ReviewFinding(BaseModel):
    """Single review finding."""
    category: str  # security, best-practices, idempotency, etc.
    severity: str  # high, medium, low
    issue: str
    suggestion: str
    line_range: str = ""


class ReviewResult(BaseModel):
    """Review results from an agent."""
    agent: str
    findings: List[ReviewFinding]
    overall_score: int  # 0-100


class MultiAgentPipeline:
    """Pipeline: Draft → Security → Best Practices → Refine."""

    def __init__(self, llm_provider):
        self.llm_provider = llm_provider

    async def generate_with_review(
        self,
        draft_playbook: str,
        event_description: str
    ) -> Dict[str, Any]:
        """Run multi-agent review pipeline.

        Args:
            draft_playbook: Initial generated playbook
            event_description: Original event description

        Returns:
            Dict with refined playbook and review results
        """

        # Agent 2: Security Review
        security_review = await self._security_review(draft_playbook)

        # Agent 3: Best Practices Review
        bp_review = await self._best_practices_review(draft_playbook)

        # Agent 4: Refine based on feedback
        refined_playbook = await self._refine_playbook(
            draft_playbook,
            security_review,
            bp_review,
            event_description
        )

        return {
            "playbook": refined_playbook,
            "reviews": {
                "security": security_review.dict(),
                "best_practices": bp_review.dict()
            },
            "confidence_boost": self._calculate_boost(security_review, bp_review)
        }

    async def _security_review(self, playbook: str) -> ReviewResult:
        """Security-focused review."""

        prompt = f"""Review this Ansible playbook for SECURITY issues only.

Playbook:
{playbook}

Find:
- Hardcoded passwords/secrets
- Unsafe shell commands (command injection risk)
- Excessive sudo/become usage
- Unvalidated user input
- File permission issues

Return findings as JSON array:
[{{"category": "security", "severity": "high|medium|low", "issue": "description", "suggestion": "fix"}}]

If no issues, return empty array: []"""

        response = await self.llm_provider.generate(prompt, model="haiku")

        # Parse findings (simplified - real implementation would use structured output)
        findings = self._parse_findings(response, "security")

        score = 100 - (len([f for f in findings if f.severity == "high"]) * 20)
        score -= len([f for f in findings if f.severity == "medium"]) * 10

        return ReviewResult(
            agent="security_reviewer",
            findings=findings,
            overall_score=max(0, score)
        )

    async def _best_practices_review(self, playbook: str) -> ReviewResult:
        """Best practices review."""

        prompt = f"""Review this Ansible playbook for BEST PRACTICES compliance.

Playbook:
{playbook}

Check:
- FQCN (Fully Qualified Collection Names) usage
- Idempotency (state-based, not command-based)
- Proper use of handlers vs tasks
- Task naming (descriptive, imperative)
- Error handling (failed_when, changed_when)
- No use of shell/command when module exists

Return findings as JSON array:
[{{"category": "best-practices", "severity": "high|medium|low", "issue": "description", "suggestion": "fix"}}]

If no issues, return empty array: []"""

        response = await self.llm_provider.generate(prompt, model="haiku")

        findings = self._parse_findings(response, "best-practices")

        score = 100 - (len([f for f in findings if f.severity == "high"]) * 15)
        score -= len([f for f in findings if f.severity == "medium"]) * 8

        return ReviewResult(
            agent="best_practices_reviewer",
            findings=findings,
            overall_score=max(0, score)
        )

    async def _refine_playbook(
        self,
        draft: str,
        security_review: ReviewResult,
        bp_review: ReviewResult,
        event_description: str
    ) -> str:
        """Refine playbook based on reviews."""

        # Combine findings
        all_findings = security_review.findings + bp_review.findings

        if not all_findings:
            # No issues found, return draft
            return draft

        # Build refinement prompt
        findings_text = "\n".join([
            f"- [{f.severity.upper()}] {f.category}: {f.issue}\n  Fix: {f.suggestion}"
            for f in all_findings
        ])

        prompt = f"""Improve this Ansible playbook by addressing the review findings.

Original Event: {event_description}

Current Playbook:
{draft}

Review Findings:
{findings_text}

Return the IMPROVED playbook addressing all findings. Keep the same functionality, just fix the issues.
Return ONLY the playbook YAML, no explanations."""

        refined = await self.llm_provider.generate(prompt, max_tokens=4000)

        # Clean up response
        refined = self._clean_playbook_output(refined)

        return refined

    def _parse_findings(self, response: str, category: str) -> List[ReviewFinding]:
        """Parse LLM response into findings (simplified)."""
        import json
        import re

        # Extract JSON array from response
        try:
            # Try to find JSON array in response
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                findings_data = json.loads(match.group())
                return [ReviewFinding(**f) for f in findings_data]
        except Exception:
            pass

        # If parsing fails, return empty (real implementation would be more robust)
        return []

    def _clean_playbook_output(self, text: str) -> str:
        """Clean LLM output to extract playbook."""
        # Remove markdown fences
        text = text.replace("```yaml", "").replace("```", "")

        # Find start of YAML
        if "---" in text:
            text = "---" + text.split("---", 1)[1]

        return text.strip()

    def _calculate_boost(
        self,
        security: ReviewResult,
        bp: ReviewResult
    ) -> int:
        """Calculate confidence boost from reviews."""

        # If both scores are high, boost confidence
        avg_score = (security.overall_score + bp.overall_score) / 2

        if avg_score >= 90:
            return 15  # +15% confidence
        elif avg_score >= 75:
            return 10  # +10% confidence
        elif avg_score >= 60:
            return 5   # +5% confidence
        else:
            return 0   # No boost if many issues
