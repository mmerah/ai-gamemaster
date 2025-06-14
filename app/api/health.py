"""Health check endpoints for monitoring system status."""

import time
from typing import Any, Dict

from flask import Blueprint, jsonify
from sqlalchemy import text

from app.core.container import get_container

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health_check() -> Any:
    """Basic health check endpoint."""
    return jsonify({"status": "healthy", "service": "ai-gamemaster"})


@health_bp.route("/api/health/database", methods=["GET"])
def database_health() -> Any:
    """
    Check database connectivity and content status.

    Returns:
        JSON with database status, table counts, and any issues
    """
    start_time = time.time()
    container = get_container()

    try:
        db_manager = container.get_database_manager()

        with db_manager.get_session() as session:
            # Check basic connectivity
            session.execute(text("SELECT 1")).scalar()

            # Get table counts for key tables
            tables = ["spells", "monsters", "equipment", "classes", "features"]
            counts: Dict[str, int] = {}

            for table in tables:
                try:
                    count = session.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    ).scalar()
                    counts[table] = count or 0
                except Exception:
                    counts[table] = -1  # Table doesn't exist

            # Check embeddings status
            embedding_stats = {}
            try:
                total_with_embeddings = session.execute(
                    text("SELECT COUNT(*) FROM spells WHERE embedding IS NOT NULL")
                ).scalar()
                total_spells = counts.get("spells", 0)
                total_with_embeddings_int = total_with_embeddings or 0
                embedding_stats["spells_indexed"] = total_with_embeddings_int
                embedding_stats["spells_total"] = total_spells
                embedding_stats["indexing_percent"] = (
                    round((total_with_embeddings_int / total_spells) * 100, 1)
                    if total_spells > 0
                    else 0
                )
            except Exception:
                embedding_stats["error"] = "Could not query embeddings"

            # Check content packs
            content_packs = []
            try:
                packs = session.execute(
                    text("SELECT id, name, version, is_active FROM content_packs")
                ).fetchall()
                for pack in packs:
                    content_packs.append(
                        {
                            "id": pack[0],
                            "name": pack[1],
                            "version": pack[2],
                            "is_active": bool(pack[3]),
                        }
                    )
            except Exception:
                content_packs = []

            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            return jsonify(
                {
                    "status": "healthy",
                    "database": {
                        "connected": True,
                        "table_counts": counts,
                        "content_packs": content_packs,
                        "embeddings": embedding_stats,
                        "response_time_ms": elapsed_ms,
                    },
                }
            )

    except Exception as e:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        return jsonify(
            {
                "status": "unhealthy",
                "database": {
                    "connected": False,
                    "error": str(e),
                    "response_time_ms": elapsed_ms,
                },
            }
        ), 503


@health_bp.route("/api/health/rag", methods=["GET"])
def rag_health() -> Any:
    """
    Check RAG system status.

    Returns:
        JSON with RAG configuration and status
    """
    container = get_container()

    try:
        rag_service = container.get_rag_service()
        rag_enabled = rag_service.__class__.__name__ != "NoOpRAGService"

        status = {
            "enabled": rag_enabled,
            "service_type": rag_service.__class__.__name__,
        }

        if rag_enabled and hasattr(rag_service, "kb_manager"):
            kb_manager = rag_service.kb_manager
            status["knowledge_base_type"] = kb_manager.__class__.__name__

            # Check if using database or in-memory
            if "Db" in kb_manager.__class__.__name__:
                status["backend"] = "database"
            else:
                status["backend"] = "in-memory"

        return jsonify({"status": "healthy", "rag": status})

    except Exception as e:
        return jsonify(
            {"status": "unhealthy", "rag": {"enabled": False, "error": str(e)}}
        ), 503
