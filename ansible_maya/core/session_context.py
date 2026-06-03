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
Session Context for Event Correlation.

Tracks event history and provides context for related events on the same host
or service, enabling better playbook generation through awareness of previous
remediation attempts.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib


@dataclass
class EventRecord:
    """Record of a processed event."""

    event_id: str
    event_type: str
    host: str
    service: Optional[str] = None
    description: str = ""
    playbook_generated: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    success: bool = True
    metadata: Dict = field(default_factory=dict)


class SessionContext:
    """
    Manages session context for event correlation.

    Tracks event history and provides related event context for improved
    playbook generation. Useful for scenarios like:
    - Multiple remediation attempts on same host
    - Service failures that are related
    - Progressive troubleshooting workflows
    """

    def __init__(self, ttl_minutes: int = 60):
        """
        Initialize session context.

        Args:
            ttl_minutes: Time-to-live for events in minutes (default: 60)
        """
        self.events: List[EventRecord] = []
        self.ttl = timedelta(minutes=ttl_minutes)
        self._host_index: Dict[str, List[EventRecord]] = {}
        self._service_index: Dict[str, List[EventRecord]] = {}

    def add_event(
        self,
        event_type: str,
        host: str,
        description: str,
        playbook: str = "",
        service: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict] = None,
    ) -> EventRecord:
        """
        Add an event to the session context.

        Args:
            event_type: Type of event (disk_full, service_down, etc.)
            host: Target host
            description: Event description
            playbook: Generated playbook (if any)
            service: Service name (if applicable)
            success: Whether remediation was successful
            metadata: Additional event metadata

        Returns:
            Created EventRecord
        """
        # Generate event ID
        event_id = self._generate_event_id(event_type, host, description)

        # Create record
        record = EventRecord(
            event_id=event_id,
            event_type=event_type,
            host=host,
            service=service,
            description=description,
            playbook_generated=playbook,
            success=success,
            metadata=metadata or {},
        )

        # Add to main list
        self.events.append(record)

        # Update indices
        if host not in self._host_index:
            self._host_index[host] = []
        self._host_index[host].append(record)

        if service:
            if service not in self._service_index:
                self._service_index[service] = []
            self._service_index[service].append(record)

        # Clean up old events
        self._cleanup_expired()

        return record

    def get_related_events(
        self,
        host: Optional[str] = None,
        service: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[EventRecord]:
        """
        Get related events based on filters.

        Args:
            host: Filter by host
            service: Filter by service
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of related EventRecords, most recent first
        """
        # Start with all events or filtered by host
        if host and host in self._host_index:
            candidates = self._host_index[host]
        elif service and service in self._service_index:
            candidates = self._service_index[service]
        else:
            candidates = self.events

        # Apply additional filters
        results = []
        for event in reversed(candidates):  # Most recent first
            if service and event.service != service:
                continue
            if event_type and event.event_type != event_type:
                continue
            results.append(event)

            if len(results) >= limit:
                break

        return results

    def get_host_history(self, host: str, limit: int = 5) -> List[EventRecord]:
        """
        Get recent event history for a specific host.

        Args:
            host: Host to get history for
            limit: Maximum number of events

        Returns:
            List of EventRecords for this host, most recent first
        """
        return self.get_related_events(host=host, limit=limit)

    def get_service_history(self, service: str, limit: int = 5) -> List[EventRecord]:
        """
        Get recent event history for a specific service.

        Args:
            service: Service to get history for
            limit: Maximum number of events

        Returns:
            List of EventRecords for this service, most recent first
        """
        return self.get_related_events(service=service, limit=limit)

    def has_recent_events(self, host: str, minutes: int = 30) -> bool:
        """
        Check if host has had recent events.

        Args:
            host: Host to check
            minutes: Time window in minutes

        Returns:
            True if host has events within the time window
        """
        if host not in self._host_index:
            return False

        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        recent = [e for e in self._host_index[host] if e.timestamp > cutoff]
        return len(recent) > 0

    def format_context_for_prompt(
        self, host: str, current_event_type: str, limit: int = 3
    ) -> str:
        """
        Format related events as context string for LLM prompt.

        Args:
            host: Host for current event
            current_event_type: Type of current event
            limit: Maximum previous events to include

        Returns:
            Formatted context string for prompt
        """
        related = self.get_host_history(host, limit=limit)

        if not related:
            return ""

        context = f"\n## Previous Events on {host}\n"
        context += "Recent remediation history that may be relevant:\n\n"

        for idx, event in enumerate(related, 1):
            age = datetime.utcnow() - event.timestamp
            age_str = self._format_age(age)

            context += f"{idx}. **{event.event_type}** ({age_str} ago)\n"
            context += f"   - Description: {event.description[:100]}\n"
            if event.service:
                context += f"   - Service: {event.service}\n"
            context += f"   - Outcome: {'✓ Success' if event.success else '✗ Failed'}\n"

            # Add key metadata if available
            if event.metadata:
                if 'cpu_percent' in event.metadata:
                    context += f"   - CPU: {event.metadata['cpu_percent']}%\n"
                if 'memory_percent' in event.metadata:
                    context += f"   - Memory: {event.metadata['memory_percent']}%\n"
                if 'disk_usage' in event.metadata:
                    context += f"   - Disk: {event.metadata['disk_usage']}%\n"

            context += "\n"

        # Add correlation notes
        same_type = [e for e in related if e.event_type == current_event_type]
        if same_type:
            context += f"**Note**: This host has had {len(same_type)} {current_event_type} event(s) recently.\n"
            context += "Consider if this is a recurring issue that needs a different approach.\n\n"

        return context

    def clear(self):
        """Clear all events from session."""
        self.events.clear()
        self._host_index.clear()
        self._service_index.clear()

    def get_stats(self) -> Dict:
        """
        Get session statistics.

        Returns:
            Dictionary with session stats
        """
        total_events = len(self.events)
        successful = sum(1 for e in self.events if e.success)
        failed = total_events - successful

        event_types = {}
        for event in self.events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

        return {
            'total_events': total_events,
            'successful': successful,
            'failed': failed,
            'unique_hosts': len(self._host_index),
            'unique_services': len(self._service_index),
            'event_types': event_types,
        }

    # Private methods

    def _generate_event_id(self, event_type: str, host: str, description: str) -> str:
        """Generate unique event ID."""
        content = f"{event_type}:{host}:{description}:{datetime.utcnow().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _cleanup_expired(self):
        """Remove events older than TTL."""
        cutoff = datetime.utcnow() - self.ttl
        self.events = [e for e in self.events if e.timestamp > cutoff]

        # Rebuild indices
        self._host_index.clear()
        self._service_index.clear()

        for event in self.events:
            if event.host not in self._host_index:
                self._host_index[event.host] = []
            self._host_index[event.host].append(event)

            if event.service:
                if event.service not in self._service_index:
                    self._service_index[event.service] = []
                self._service_index[event.service].append(event)

    def _format_age(self, delta: timedelta) -> str:
        """Format timedelta as human-readable string."""
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            return f"{seconds // 3600}h"
        else:
            return f"{seconds // 86400}d"


# Global session context instance (can be replaced with Redis in production)
_global_session = SessionContext()


def get_session_context() -> SessionContext:
    """Get the global session context instance."""
    return _global_session


def reset_session_context():
    """Reset the global session context."""
    global _global_session
    _global_session = SessionContext()
