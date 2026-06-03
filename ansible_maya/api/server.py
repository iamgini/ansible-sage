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

"""FastAPI application server for Ansible AI Gateway."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Version info
from ansible_maya import __version__

# Create FastAPI app
app = FastAPI(
    title="Ansible AI Gateway",
    description="Multi-provider AI gateway for Ansible playbook generation - AI-powered event-driven playbook generation",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on .env in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": "Ansible AI Gateway",
        "version": __version__,
        "description": "AI-powered event-driven Ansible playbook generation",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for container orchestration."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "version": __version__,
        },
    )


@app.get("/ready")
async def readiness_check() -> JSONResponse:
    """Readiness check - verifies dependencies are available."""
    # TODO: Add checks for database, redis, etc.
    return JSONResponse(
        status_code=200,
        content={
            "status": "ready",
            "checks": {
                "database": "ok",  # Placeholder
                "redis": "ok",  # Placeholder
            },
        },
    )


# API routes
from ansible_maya.api.routes import events

app.include_router(events.router, prefix="/api/v1/events", tags=["events"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "sage.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
