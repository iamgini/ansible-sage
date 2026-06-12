"""
Pytest configuration and shared fixtures.
"""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external dependencies)")
    config.addinivalue_line(
        "markers", "integration: Integration tests (may require services/API keys)"
    )
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "molecule: Tests requiring Molecule/Docker")


@pytest.fixture
def mock_event_data():
    """Sample event data for testing."""
    return {
        "event_id": "test-evt-001",
        "event_type": "disk_full",
        "description": "Disk usage at 95% on /var partition",
        "host": "test-server-01.example.com",
        "severity": "high",
        "timestamp": "2026-06-12T10:00:00Z",
        "metadata": {"partition": "/var", "usage_percent": 95, "available_mb": 512},
    }


@pytest.fixture
def mock_playbook_content():
    """Sample generated playbook for testing."""
    return """---
- name: Clean up disk space on /var
  hosts: test-server-01.example.com
  become: true

  tasks:
    - name: Find old log files
      ansible.builtin.find:
        paths: /var/log
        age: 30d
        patterns: "*.log"
      register: old_logs

    - name: Remove old log files
      ansible.builtin.file:
        path: "{{ item.path }}"
        state: absent
      loop: "{{ old_logs.files }}"
      when: old_logs.matched > 0
"""
