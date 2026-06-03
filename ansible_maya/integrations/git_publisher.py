# Copyright 2026 Ansible AI Gateway Contributors
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
Git repository integration for publishing generated playbooks.

Pushes playbooks to configured Git repository based on confidence level:
- High confidence (>80%) → main branch
- Medium confidence (50-80%) → review branch
- Low confidence (<50%) → draft branch
"""

import logging
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence level for generated playbooks."""

    HIGH = "high"  # >80% - Safe for main branch
    MEDIUM = "medium"  # 50-80% - Needs review
    LOW = "low"  # <50% - Draft/experimental


@dataclass
class GitConfig:
    """Git repository configuration."""

    repo_url: str
    main_branch: str = "main"
    review_branch: str = "review"
    draft_branch: str = "draft"
    playbooks_dir: str = "playbooks/generated"
    username: Optional[str] = None
    email: Optional[str] = None
    ssh_key_path: Optional[str] = None
    token: Optional[str] = None  # For HTTPS with PAT


@dataclass
class PublishResult:
    """Result of publishing playbook to Git."""

    success: bool
    branch: str
    commit_sha: Optional[str] = None
    file_path: Optional[str] = None
    pull_request_url: Optional[str] = None
    error: Optional[str] = None


class GitPublisher:
    """
    Publishes generated playbooks to Git repository.

    Workflow:
    1. Clone/pull repo to temp directory
    2. Create/checkout appropriate branch based on confidence
    3. Add generated playbook file
    4. Commit with metadata
    5. Push to remote
    6. Optionally create pull request (for medium/low confidence)
    """

    def __init__(self, config: GitConfig):
        """
        Initialize Git publisher.

        Args:
            config: Git repository configuration
        """
        self.config = config
        self.working_dir: Optional[Path] = None

    async def publish_playbook(
        self,
        playbook_content: str,
        playbook_name: str,
        confidence: float,
        metadata: dict,
    ) -> PublishResult:
        """
        Publish playbook to Git repository.

        Args:
            playbook_content: Generated playbook YAML
            playbook_name: Name for the playbook file (e.g., "disk_cleanup_web01.yml")
            confidence: Confidence score (0.0 - 1.0)
            metadata: Event metadata for commit message

        Returns:
            PublishResult with status and details
        """
        # Determine confidence level and target branch
        confidence_level = self._calculate_confidence_level(confidence)
        target_branch = self._get_target_branch(confidence_level)

        logger.info(
            f"Publishing playbook to Git",
            extra={
                "playbook": playbook_name,
                "confidence": confidence,
                "level": confidence_level.value,
                "branch": target_branch,
            },
        )

        try:
            # Clone/update repository
            await self._prepare_repo()

            # Checkout appropriate branch
            await self._checkout_branch(target_branch)

            # Write playbook file
            playbook_path = self._write_playbook(playbook_name, playbook_content)

            # Commit changes
            commit_message = self._generate_commit_message(
                playbook_name, confidence_level, metadata
            )
            commit_sha = await self._commit_changes(playbook_path, commit_message)

            # Push to remote
            await self._push_to_remote(target_branch)

            # Create PR if medium/low confidence
            pr_url = None
            if confidence_level in (ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW):
                pr_url = await self._create_pull_request(
                    target_branch, playbook_name, confidence_level, metadata
                )

            return PublishResult(
                success=True,
                branch=target_branch,
                commit_sha=commit_sha,
                file_path=str(playbook_path),
                pull_request_url=pr_url,
            )

        except Exception as e:
            logger.error(f"Failed to publish playbook to Git: {str(e)}")
            return PublishResult(
                success=False,
                branch=target_branch,
                error=str(e),
            )
        finally:
            # Cleanup working directory
            self._cleanup()

    def _calculate_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """
        Calculate confidence level from score.

        Args:
            confidence: Confidence score (0.0 - 1.0)

        Returns:
            ConfidenceLevel enum
        """
        if confidence >= 0.80:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.50:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def _get_target_branch(self, level: ConfidenceLevel) -> str:
        """Get target branch for confidence level."""
        if level == ConfidenceLevel.HIGH:
            return self.config.main_branch
        elif level == ConfidenceLevel.MEDIUM:
            return self.config.review_branch
        else:
            return self.config.draft_branch

    async def _prepare_repo(self) -> None:
        """Clone or update the repository."""
        self.working_dir = Path(tempfile.mkdtemp(prefix="ansible-maya-git-"))

        # Build clone command
        repo_url = self._get_authenticated_url()

        # Clone repository
        cmd = ["git", "clone", repo_url, str(self.working_dir)]

        if self.config.ssh_key_path:
            # Use SSH with custom key
            git_ssh_cmd = f"ssh -i {self.config.ssh_key_path} -o StrictHostKeyChecking=no"
            env = {"GIT_SSH_COMMAND": git_ssh_cmd}
        else:
            env = None

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=self.working_dir.parent,
        )

        if result.returncode != 0:
            raise Exception(f"Git clone failed: {result.stderr}")

        # Configure user if provided
        if self.config.username:
            self._run_git_command(["config", "user.name", self.config.username])
        if self.config.email:
            self._run_git_command(["config", "user.email", self.config.email])

        logger.info(f"Repository cloned to {self.working_dir}")

    async def _checkout_branch(self, branch: str) -> None:
        """Checkout or create branch."""
        # Try to checkout existing branch
        result = self._run_git_command(["checkout", branch], check=False)

        if result.returncode != 0:
            # Branch doesn't exist, create from main
            self._run_git_command(["checkout", "-b", branch, f"origin/{self.config.main_branch}"])

        logger.info(f"Checked out branch: {branch}")

    def _write_playbook(self, playbook_name: str, content: str) -> Path:
        """Write playbook to repository."""
        playbooks_dir = self.working_dir / self.config.playbooks_dir
        playbooks_dir.mkdir(parents=True, exist_ok=True)

        # Add timestamp to filename to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}_{playbook_name}"
        if not filename.endswith(".yml"):
            filename += ".yml"

        playbook_path = playbooks_dir / filename
        playbook_path.write_text(content)

        logger.info(f"Playbook written to {playbook_path}")
        return playbook_path

    def _generate_commit_message(
        self,
        playbook_name: str,
        confidence: ConfidenceLevel,
        metadata: dict,
    ) -> str:
        """Generate commit message with metadata."""
        lines = [
            f"Add generated playbook: {playbook_name}",
            "",
            f"Confidence: {confidence.value}",
            f"Event Type: {metadata.get('event_type', 'unknown')}",
            f"Host: {metadata.get('host', 'unknown')}",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "Generated by Ansible AI Gateway",
        ]

        # Add validation info
        if "validation" in metadata:
            val = metadata["validation"]
            lines.append(f"Validation: {'Passed' if val.get('passed') else 'Failed'}")
            if val.get("issues"):
                lines.append(f"Issues: {val.get('issues')}")

        # Add model info
        if "model" in metadata:
            lines.append(f"Model: {metadata['model']}")

        return "\n".join(lines)

    async def _commit_changes(self, file_path: Path, message: str) -> str:
        """Commit changes and return commit SHA."""
        # Stage the file
        rel_path = file_path.relative_to(self.working_dir)
        self._run_git_command(["add", str(rel_path)])

        # Commit
        self._run_git_command(["commit", "-m", message])

        # Get commit SHA
        result = self._run_git_command(["rev-parse", "HEAD"])
        commit_sha = result.stdout.strip()

        logger.info(f"Committed changes: {commit_sha}")
        return commit_sha

    async def _push_to_remote(self, branch: str) -> None:
        """Push branch to remote."""
        self._run_git_command(["push", "-u", "origin", branch])
        logger.info(f"Pushed to origin/{branch}")

    async def _create_pull_request(
        self,
        branch: str,
        playbook_name: str,
        confidence: ConfidenceLevel,
        metadata: dict,
    ) -> Optional[str]:
        """
        Create pull request (GitHub/GitLab).

        Note: This is a placeholder. Actual implementation would use
        GitHub API, GitLab API, etc.
        """
        # TODO: Implement PR creation via API
        # For now, return None - users can create PRs manually
        logger.info(
            f"Pull request should be created for {branch} → {self.config.main_branch}"
        )
        return None

    def _get_authenticated_url(self) -> str:
        """Get repository URL with authentication."""
        if self.config.token and self.config.repo_url.startswith("https://"):
            # Insert token into HTTPS URL
            # https://github.com/user/repo.git → https://token@github.com/user/repo.git
            parts = self.config.repo_url.split("://", 1)
            return f"{parts[0]}://{self.config.token}@{parts[1]}"
        return self.config.repo_url

    def _run_git_command(self, args: list, check: bool = True) -> subprocess.CompletedProcess:
        """Run git command in working directory."""
        cmd = ["git"] + args
        result = subprocess.run(
            cmd,
            cwd=self.working_dir,
            capture_output=True,
            text=True,
            check=check,
        )
        return result

    def _cleanup(self) -> None:
        """Cleanup temporary working directory."""
        if self.working_dir and self.working_dir.exists():
            import shutil

            shutil.rmtree(self.working_dir, ignore_errors=True)
            logger.debug(f"Cleaned up {self.working_dir}")


# Convenience function
async def publish_to_git(
    playbook_content: str,
    playbook_name: str,
    confidence: float,
    metadata: dict,
    git_config: GitConfig,
) -> PublishResult:
    """
    Quick helper to publish playbook to Git.

    Args:
        playbook_content: Generated playbook YAML
        playbook_name: Playbook filename
        confidence: Confidence score (0.0 - 1.0)
        metadata: Event metadata
        git_config: Git repository configuration

    Returns:
        PublishResult
    """
    publisher = GitPublisher(git_config)
    return await publisher.publish_playbook(
        playbook_content, playbook_name, confidence, metadata
    )
