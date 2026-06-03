# Copyright 2026 Ansible Maya Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

# Multi-stage build for Ansible Maya

# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM python:3.11-slim AS builder

# Build arguments
ARG PYTHON_VERSION=3.11

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
WORKDIR /build
COPY requirements-minimal.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements-minimal.txt

# ============================================================================
# Stage 2: Runtime - Create final image
# ============================================================================
FROM python:3.11-slim

# Metadata
LABEL org.opencontainers.image.title="Ansible Maya"
LABEL org.opencontainers.image.description="AI-powered Ansible playbook generator with validation and best practices"
LABEL org.opencontainers.image.vendor="Ansible Maya Contributors"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.source="https://github.com/your-org/ansible-maya"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    rsync \
    sshpass \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r sage && \
    useradd -r -g sage -u 1000 -d /app -s /bin/bash sage && \
    mkdir -p /app && \
    chown -R sage:sage /app

# Switch to non-root user
USER sage
WORKDIR /app

# Copy application code
COPY --chown=sage:sage sage/ ./sage/
COPY --chown=sage:sage pyproject.toml ./
COPY --chown=sage:sage README.md ./
COPY --chown=sage:sage LICENSE ./
COPY --chown=sage:sage NOTICE ./

# Create directories for runtime
RUN mkdir -p \
    /app/logs \
    /app/generated_playbooks \
    /app/config

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "sage.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
