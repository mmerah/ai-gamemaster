# CLAUDE.md

This file provides guidance to Claude when working on the AI Game Master repository.

## 1. Guiding Principles

This project adheres to a set of core development principles to ensure a maintainable, robust, and simple codebase.

-   **Keep It Simple, Stupid (KISS)**: Favor straightforward solutions. Code should be readable and easily understood by new developers.
-   **You Aren't Gonna Need It (YAGNI)**: Only implement features that are explicitly required. Focus on the current specification.
-   **Don't Repeat Yourself (DRY)**: Abstract common logic into reusable functions or services. The "rule of three" is a good guideline.
-   **Strong Typing & Explicit Contracts**: Write code that is clear, self-documenting, and robust. Always use the most specific type hint possible. This allows `mypy` to catch bugs before runtime, improves IDE autocompletion, and makes the code easier to reason about.
-   **SOLID Principles & Modularity**: Create a system that is easy to maintain, extend, and test by adhering to SOLID principles.
    -   **S - Single Responsibility Principle**: "A class or module should have one, and only one, reason to change."
    -   **O - Open/Closed Principle**: "Software entities should be open for extension, but closed for modification."
    -   **L - Liskov Substitution Principle**: "Subtypes must be substitutable for their base types without altering the correctness of the program."
    -   **I - Interface Segregation Principle**: "Clients should not be forced to depend on interfaces they do not use."
    -   **D - Dependency Inversion Principle**: "High-level modules should not depend on low-level modules. Both should depend on abstractions. This is the core of our architecture. High-level services in `app/services/` depend on interfaces from `app/core/` (abstractions). The `ServiceContainer` in `app/core/container.py` is responsible for injecting the concrete implementations (details) at runtime."
-   **RESTful API Conventions**: Use plural, kebab-case nouns for resources (e.g., `/api/character-templates`). Use standard HTTP methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).

## 2. Project Overview

The AI Game Master is an open-source web application that acts as an AI-powered Game Master for Dungeons & Dragons 5th Edition. It uses Large Language Models (LLMs) for adaptive storytelling and game management, providing an immersive single-player TTRPG experience.

-   **Backend**: A service-oriented application built with **Python** and **FastAPI**, using **Pydantic** for rigorous data modeling. It features an event-driven architecture with Server-Sent Events (SSE) for real-time updates.
-   **Frontend**: A modern, responsive single-page application built with **Vue.js 3** and **TypeScript**, using Pinia for state management.
-   **Database**: **SQLite** is used for D&D 5e content, with a dual-database architecture (system vs. user content) and native vector search capabilities via the `sqlite-vec` extension.
-   **AI Integration**: A modular system supporting various LLMs through an OpenAI-compatible API, with a focus on structured JSON outputs for reliable game state management.

## 3. Essential Commands

The project is migrating from Flask to **FastAPI**. Use `main.py` as the entry point.

| Command                                             | Description                                                                  |
| --------------------------------------------------- | ---------------------------------------------------------------------------- |
| `./launch.sh` or `launch.bat`                       | **Quick Start**: Automatically sets up and runs the entire application.      |
| `python main.py`                                    | Runs the **FastAPI** backend server (development mode).                      |
| `npm --prefix frontend run dev`                     | Runs the **Vue.js** frontend development server with hot-reloading.            |
| `python tests/run_all_tests.py --with-rag`          | **Runs all tests**, including the RAG (semantic search) integration tests.   |
| `mypy app/ tests/ --strict`                         | **Type-checks** the entire project. Expects **0 errors**.                    |
| `ruff check . --fix`                                | **Lints and auto-fixes** code quality issues.                                |
| `ruff format .`                                     | **Formats** all Python code according to project standards.                  |
| `python scripts/dev/generate_ts.py`                 | **Generates TypeScript** interfaces from Python's Pydantic models.           |
| `python -m app.content.scripts.migrate_content`     | **(Re)generates** the D&D 5e content database from source JSON files.        |
| `python -m app.content.scripts.index_for_rag`       | **Generates vector embeddings** for the content database for semantic search.  |
| `python -m app.content.scripts.migrate_user_content`| **Migrates** custom content from the old single-DB to the new user DB.         |

## 4. Key Dependencies

-   **AI/ML**: `langchain`, `langchain-openai`, `sentence-transformers`, `torch`, `faiss-cpu`
-   **Web Framework**: `fastapi`, `uvicorn`
-   **Data Modeling**: `pydantic`, `pydantic-settings`
-   **Database**: `sqlalchemy`, `alembic`, `sqlite-vec`
-   **Code Quality**: `ruff`, `mypy`, `pre-commit`

## 5. Architecture & Code Layout

This project is built on a service-oriented, domain-driven, and event-driven architecture. The goal is to separate concerns, making the system easier to understand, maintain, and test.

### Core Architectural Principles

-   **Domain-Driven Design (DDD)**: The code is organized by its business domain (e.g., `app/domain/characters`, `app/domain/combat`). This keeps related logic together.
-   **Service-Oriented Architecture (SOA)**: Functionality is encapsulated in services that have clear responsibilities (e.g., `ContentService`, `CampaignService`).
-   **Dependency Injection (DI)**: Services and repositories are managed by a central `ServiceContainer` (`app/core/container.py`). This decouples components and simplifies testing by allowing for easy mocking.
-   **Event-Driven Architecture (EDA)**: Game state changes are communicated through an `EventQueue` (`app/core/event_queue.py`). The frontend subscribes to these events via Server-Sent Events (SSE) for real-time updates, eliminating the need for polling.

### Code Structure Map

This map highlights the key directories and files, explaining their role in the application architecture.

-   `ai-gamemaster/`
    -   `app/`: **Backend Application Core**
        -   `api/`: **API Layer** - FastAPI routers defining all HTTP endpoints.
            -   `*_fastapi.py`: Route definitions for each domain (e.g., `campaign_fastapi.py`).
            -   `dependencies_fastapi.py`: FastAPI dependency injection functions.
        -   `content/`: **D&D 5e Content Subsystem** - A self-contained module for all game content.
            -   `alembic/`: Database management and versioning
            -   `data/knowledge/`: Contains the `5e-database` submodule with the 5e SRD content (as .json) and `lores.json` with `lore/`
            -   `service.py`: `ContentService`, the primary facade for accessing D&D data.
            -   `repositories/`: Data access layer for the content database.
            -   `rag/`: Retrieval-Augmented Generation (semantic search) system.
            -   `schemas/`: Pydantic models for D&D content (spells, monsters, etc.).
            -   `models.py`: SQLAlchemy ORM models for the content database.
            -   `scripts/`: Scripts for database migration and indexing.
        -   `core/`: **Core Interfaces & DI Container** - The architectural backbone.
            -   `container.py`: `ServiceContainer` for dependency injection.
            -   `*_interfaces.py`: Abstract base classes defining contracts for services and repositories.
        -   `domain/`: **Business Logic** - Core game rules and logic, independent of frameworks.
            -   `campaigns/`, `characters/`, `combat/`: Domain-specific services and factories.
        -   `models/`: **Unified Data Models (Single Source of Truth)**
            -   `*.py`: Pydantic models defining all runtime data structures (game state, characters, events).
        -   `providers/`: **External Service Integrations**
            -   `ai/`: Connectors for AI services (OpenAI, Llama.cpp).
            -   `tts/`: Connectors for Text-to-Speech services.
        -   `repositories/`: **Data Persistence (Game State)**
            -   `*.py`: Repositories for saving/loading campaign and character data (JSON files).
        -   `services/`: **Application Services & Orchestration**
            -   `game_orchestrator.py`: Central coordinator for game events.
            -   `action_handlers/`: Logic for handling specific player actions.
            -   `ai_response_processor.py`: Parses structured AI responses and updates game state.
        -   `factory.py`: FastAPI application factory (`create_app`).
        -   `settings.py`: Type-safe application configuration using Pydantic.
    -   `data/`: `content.db` SQLite database with the 5e SRD (System pack) and `user_content.db` for all user content packs
    -   `frontend/`: **Frontend Application (Vue.js)**
        -   `src/`:
            -   `views/`: Top-level page components (e.g., `GameView.vue`).
            -   `components/`: Reusable UI components.
            -   `stores/`: Pinia stores for state management (e.g., `gameStore.ts`, `combatStore.ts`).
            -   `services/`: API clients for communicating with the backend.
            -   `types/`: TypeScript interfaces.
                -   `unified.ts`: **(Auto-generated)** Interfaces matching backend Pydantic models.
    -   `tests/`: **Automated Tests** - Mirrors the `app/` structure for unit and integration tests.
    -   `docs/`: **Project Documentation** (Architecture, Guides, etc.).
    -   `.env.example`: Settings as environment variables. Example that can be used as reference by users.
    -   `.pre-commit-config.yaml`: pre-commit hook configuration (mypy, ruff, pytest)
    -   `main.py`: **Application Entry Point** - Starts the FastAPI server.

## 6. Engineering Standards & Best Practices

We enforce a high standard of code quality through automation and a structured development process.

### The RIDACT Process
For problem-solving and feature development, we follow the **RIDACT** process:
1.  **R**esearch & **I**dentify: Understand the problem and identify the affected components.
2.  **D**iagnose & **A**nalyze: Determine the root cause and plan the implementation.
3.  **A**ct & **I**mplement: Write clean, simple, and well-tested code.
4.  **C**heck & **V**alidate: Run all tests, type checks, and linters to ensure quality.
5.  **T**rack & **I**terate: Commit the work and monitor its impact.

### Quality Gates
The following checks **must pass** before any code is merged:
1.  **Strict Type Safety**: `mypy . --strict` must report **0 errors**. All code is strongly typed.
2.  **Comprehensive Testing**: `python tests/run_all_tests.py --with-rag` must pass with **0 failures**. This includes unit, integration, and RAG tests. We practice **Test-Driven Development (TDD)** where applicable.
3.  **Code Quality & Formatting**: `ruff check .` and `ruff format .` are used to enforce a consistent style and catch common errors. All code is formatted with `ruff`.

### Pre-commit Hooks
The project uses `pre-commit` to automate quality checks before every commit. The hooks are defined in `.pre-commit-config.yaml` and will automatically run `ruff` and `mypy` to enforce standards.
-   **Installation**: `pip install pre-commit && pre-commit install`

### TypeScript Synchronization
The frontend's TypeScript interfaces are **auto-generated** from the backend's Pydantic models. This ensures perfect type alignment between the frontend and backend.
-   **To Update**: Run `python scripts/dev/generate_ts.py` whenever you change a model in `app/models/`.