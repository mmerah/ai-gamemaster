"""Root-level conftest to ensure early patching of AI service."""

import os

os.environ["TESTING"] = "true"
# Only set RAG_ENABLED if not already set (to allow --with-rag to work)
os.environ.setdefault("RAG_ENABLED", "false")
os.environ.setdefault("TTS_PROVIDER", "disabled")

# Import the test conftest to ensure patching happens early
from tests.conftest import *
