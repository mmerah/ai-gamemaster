"""
FastAPI application entry point.
"""

import os

import uvicorn

from app import create_app

# Create FastAPI application
app = create_app()

if __name__ == "__main__":
    # Get debug mode from environment
    is_debug = os.getenv("DEBUG", "False").lower() in ("true", "1")

    # Configure Uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=5000,
        reload=is_debug,
        log_level="debug" if is_debug else "info",
        access_log=True,
    )
