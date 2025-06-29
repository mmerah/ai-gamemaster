"""Configuration routes for exposing safe-to-view settings - FastAPI version."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_settings
from app.settings import Settings

# Create router for config API routes
router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config", response_model=Settings, response_model_by_alias=False)
async def get_configuration(
    settings: Settings = Depends(get_settings),
) -> Settings:
    """Get application configuration settings.

    Returns the full Settings object directly, allowing the frontend
    to access all configuration values in a structured format.
    """
    return settings
