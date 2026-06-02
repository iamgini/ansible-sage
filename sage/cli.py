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

"""Command-line interface for Ansible Sage."""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

import click

from sage import __version__
from sage.core.providers import get_provider
from sage.handlers.orchestrator import (
    AIOpsEvent,
    EventSeverity,
    PlaybookOrchestrator,
)


@click.group()
@click.version_option(version=__version__)
def cli():
    """Ansible Sage - AI-powered event-driven playbook generation."""
    pass


@cli.command()
@click.option(
    "--event-type",
    "-t",
    required=True,
    help="Type of infrastructure event (e.g., disk_full, service_down)",
)
@click.option(
    "--description",
    "-d",
    required=True,
    help="Detailed event description",
)
@click.option(
    "--host",
    "-h",
    required=True,
    help="Target host or hostname",
)
@click.option(
    "--severity",
    "-s",
    type=click.Choice(["low", "medium", "high", "critical"]),
    default="medium",
    help="Event severity level",
)
@click.option(
    "--provider",
    "-p",
    default="claude",
    help="LLM provider to use (claude, openai, ollama)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (default: stdout)",
)
@click.option(
    "--save-dir",
    type=click.Path(),
    help="Directory to save generated playbooks",
)
def generate(event_type, description, host, severity, provider, output, save_dir):
    """Generate Ansible playbook from infrastructure event."""

    async def _generate():
        # Get provider configuration
        provider_config = {}
        if provider.lower() in ["claude", "anthropic"]:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                click.echo("❌ Error: ANTHROPIC_API_KEY environment variable not set", err=True)
                sys.exit(1)
            provider_config["api_key"] = api_key
        elif provider.lower() == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                click.echo("❌ Error: OPENAI_API_KEY environment variable not set", err=True)
                sys.exit(1)
            provider_config["api_key"] = api_key

        # Initialize provider
        try:
            llm_provider = get_provider(provider, config=provider_config)
        except ValueError as e:
            click.echo(f"❌ Error: {str(e)}", err=True)
            sys.exit(1)

        # Create event
        event = AIOpsEvent(
            event_id=f"cli-{int(datetime.now().timestamp())}",
            event_type=event_type,
            description=description,
            host=host,
            severity=EventSeverity(severity),
            timestamp=datetime.now(),
        )

        # Generate playbook
        click.echo(f"🤖 Generating playbook for {event_type} on {host}...")

        orchestrator = PlaybookOrchestrator(provider=llm_provider)

        try:
            response = await orchestrator.handle_event(event)
        except Exception as e:
            click.echo(f"❌ Generation failed: {str(e)}", err=True)
            sys.exit(1)

        # Display results
        click.echo("\n" + "=" * 60)
        click.echo(f"Event ID: {event.event_id}")
        click.echo(f"Mode: {response.mode.value}")
        click.echo(f"Model: {response.generation_metadata.get('model', 'unknown')}")
        click.echo(f"Validation: {'✓ Passed' if response.validation_result.passed else '✗ Failed'}")

        if response.validation_result.issues:
            click.echo(f"Issues: {len(response.validation_result.issues)}")

        click.echo("=" * 60 + "\n")

        # Output playbook
        if output:
            output_path = Path(output)
            output_path.write_text(response.playbook)
            click.echo(f"✓ Playbook saved to: {output_path}")
        elif save_dir:
            save_path = Path(save_dir)
            save_path.mkdir(parents=True, exist_ok=True)
            filename = f"{event.event_id}_{event_type}_{int(datetime.now().timestamp())}.yml"
            playbook_path = save_path / filename
            playbook_path.write_text(response.playbook)
            click.echo(f"✓ Playbook saved to: {playbook_path}")
        else:
            click.echo(response.playbook)

        click.echo(f"\n{response.recommended_action}\n")

        # Show validation issues if any
        if response.validation_result.issues:
            click.echo("\n⚠️  Validation Issues:")
            for issue in response.validation_result.issues:
                location = f" (line {issue.line})" if issue.line else ""
                click.echo(f"  - [{issue.rule_id}] {issue.message}{location}")

    asyncio.run(_generate())


@cli.command()
def list_events():
    """List supported event types."""
    click.echo("Known Safe Events (Auto Mode):")
    for event in PlaybookOrchestrator.KNOWN_SAFE_EVENTS:
        click.echo(f"  • {event}")

    click.echo("\nApproval Required Events:")
    for event in PlaybookOrchestrator.APPROVAL_REQUIRED_EVENTS:
        click.echo(f"  • {event}")

    click.echo("\nSeverity Levels:")
    for severity in EventSeverity:
        click.echo(f"  • {severity.value}")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host, port, reload):
    """Start the API server."""
    import uvicorn

    click.echo(f"🚀 Starting Ansible Sage API server on {host}:{port}")
    click.echo(f"📚 API docs: http://{host}:{port}/docs")

    uvicorn.run(
        "sage.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@cli.command()
@click.argument("playbook_file", type=click.Path(exists=True))
@click.option("--fix", is_flag=True, help="Automatically fix issues")
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
def validate(playbook_file, fix, strict):
    """Validate an Ansible playbook with ansible-lint."""

    async def _validate():
        from sage.validation.ansible_lint import validate_playbook

        playbook_path = Path(playbook_file)
        content = playbook_path.read_text()

        click.echo(f"🔍 Validating {playbook_file}...")

        result = await validate_playbook(content, auto_fix=fix, strict=strict)

        if result.passed:
            click.echo("✓ Playbook passed validation!")
        else:
            click.echo(f"✗ Validation failed with {len(result.issues)} issues:")
            for issue in result.issues:
                location = f" (line {issue.line})" if issue.line else ""
                severity_icon = "⚠️" if issue.severity == "warning" else "❌"
                click.echo(f"  {severity_icon} [{issue.rule_id}] {issue.message}{location}")

            sys.exit(1)

    asyncio.run(_validate())


if __name__ == "__main__":
    cli()
