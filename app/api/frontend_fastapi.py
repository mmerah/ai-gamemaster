"""Frontend routes for serving the Vue.js SPA - FastAPI version."""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter(tags=["frontend"])

# Get the path to the Vue.js built files
DIST_PATH = Path(os.getcwd()) / "static" / "dist"
INDEX_PATH = DIST_PATH / "index.html"


def serve_spa() -> FileResponse:
    """Serve the Vue.js SPA index.html."""
    if not INDEX_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Frontend not built. Run 'npm --prefix frontend run build'",
        )
    return FileResponse(INDEX_PATH, media_type="text/html")


# SPA routes that all serve index.html for client-side routing
@router.get("/")
async def index() -> FileResponse:
    """Serve the Vue.js SPA root."""
    return serve_spa()


@router.get("/campaigns")
async def campaign_manager() -> FileResponse:
    """Serve the Vue.js SPA (client-side routing will handle this)."""
    return serve_spa()


@router.get("/campaign-manager")
async def campaign_manager_alt() -> FileResponse:
    """Serve the Vue.js SPA (client-side routing will handle this)."""
    return serve_spa()


@router.get("/game")
async def game() -> FileResponse:
    """Serve the Vue.js SPA (client-side routing will handle this)."""
    return serve_spa()


@router.get("/characters")
async def characters() -> FileResponse:
    """Serve the Vue.js SPA (client-side routing will handle this)."""
    return serve_spa()


@router.get("/configuration")
async def configuration() -> FileResponse:
    """Serve the Vue.js SPA (client-side routing will handle this)."""
    return serve_spa()


# Note: Static file serving for /static/dist/* and /assets/* is handled by
# the FastAPI mount in factory.py, so we don't need those routes here.


# SPA fallback route - must be registered last to catch all other routes
@router.get("/{path:path}")
async def spa_fallback(path: str) -> FileResponse:
    """Fallback route for Vue.js SPA client-side routing.

    This must be registered last to ensure it doesn't override other routes.
    """
    # Don't interfere with API routes
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    # Don't interfere with static files
    if path.startswith(("static/", "assets/")):
        raise HTTPException(status_code=404, detail="Static file not found")

    # Serve the Vue.js app for all other routes
    return serve_spa()
