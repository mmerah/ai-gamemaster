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

The project uses **FastAPI**. Use `main.py` as the entry point.

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
            -   `*_routes.py`: Route definitions for each domain (e.g., `campaign_routes.py`).
            -   `dependencies.py`: FastAPI dependency injection functions.
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
    -   `frontend/`: **Frontend Application (Vue.js 3 + TypeScript)**
        -   `src/`:
            -   `views/`: Top-level page components (e.g., `GameView.vue`, `LaunchScreen.vue`).
            -   `components/`: Reusable UI components organized by domain:
                -   `base/`: **Base Component Library** - Foundational UI components (buttons, inputs, modals, etc.)
                -   `campaign/`: Campaign and character management components
                -   `content/`: Content pack and RAG testing components
                -   `game/`: Game session components (chat, dice, combat, etc.)
                -   `layout/`: Layout and navigation components
            -   `stores/`: Pinia stores for state management (e.g., `gameStore.ts`, `combatStore.ts`).
            -   `services/`: API clients for communicating with the backend.
            -   `composables/`: Vue composition functions for shared logic.
            -   `types/`: TypeScript interfaces.
                -   `unified.ts`: **(Auto-generated)** Interfaces matching backend Pydantic models.
            -   `styles/`: Global styles and theme system with CSS variables for light/dark mode support.
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

### Frontend Design System

The frontend uses a comprehensive design system built on **Vue.js 3**, **TypeScript**, and **Tailwind CSS**. The system provides a consistent, theme-aware, and maintainable UI across the entire application.

#### Architecture Principles

The frontend follows these key architectural principles:

1. **Component-Based Architecture**: Reusable base components provide consistency and reduce code duplication
2. **Theme-First Design**: All styling uses CSS variables for seamless light/dark mode support
3. **Type Safety**: Full TypeScript integration with strict type checking
4. **Per-Character Content Packs**: Content selection is character-specific, not global
5. **Progressive Enhancement**: Features degrade gracefully when services are unavailable

#### Base Component Library

Located in `frontend/src/components/base/`, these components form the foundation of the UI:

**Form Components:**
- `AppInput.vue` - Text input with label, validation, and theme support
- `AppTextarea.vue` - Multi-line text input with auto-resize
- `AppSelect.vue` - Dropdown selection with search and filtering
- `AppNumberInput.vue` - Number input with increment/decrement controls
- `AppCheckboxGroup.vue` - Grouped checkboxes with select all/none
- `AppButton.vue` - Flexible button with variants (`primary`, `secondary`, `danger`) and sizes

**Layout Components:**
- `AppCard.vue` - Container component with consistent padding and styling
- `AppModal.vue` - Modal dialog with backdrop and named slots (`header`, `body`, `footer`)
- `AppTabs.vue` - Tab navigation with badge support
- `AppFormSection.vue` - Collapsible form sections with titles and descriptions
- `BasePanel.vue` - Lightweight panel for grouping content

**Feedback Components:**
- `BaseAlert.vue` - Alert messages with variants (`info`, `success`, `warning`, `error`)
- `BaseBadge.vue` - Status indicators and labels
- `BaseLoader.vue` - Loading spinners with size options
- `NotificationToast.vue` - Toast notifications for user feedback

#### Usage Examples

```vue
<!-- Basic form with validation -->
<template>
  <AppCard class="max-w-md">
    <AppFormSection title="Character Details">
      <AppInput
        v-model="character.name"
        label="Character Name"
        :error="errors.name"
        required
      />
      
      <AppSelect
        v-model="character.class"
        label="Class"
        :options="availableClasses"
        placeholder="Choose a class..."
      />
      
      <AppButton 
        variant="primary" 
        :loading="saving"
        @click="saveCharacter"
      >
        Save Character
      </AppButton>
    </AppFormSection>
  </AppCard>
</template>
```

```vue
<!-- Modal with structured content -->
<template>
  <AppModal v-model="showModal">
    <template #header>
      <h2 class="text-xl font-cinzel font-semibold">Create Campaign</h2>
    </template>
    
    <template #body>
      <BaseAlert type="info" class="mb-4">
        Select characters to include in your campaign.
      </BaseAlert>
      
      <!-- Form content -->
    </template>
    
    <template #footer>
      <div class="flex justify-end space-x-2">
        <AppButton variant="secondary" @click="showModal = false">
          Cancel
        </AppButton>
        <AppButton variant="primary" @click="createCampaign">
          Create Campaign
        </AppButton>
      </div>
    </template>
  </AppModal>
</template>
```

#### Theme System

The theme system uses CSS variables for colors and supports automatic light/dark mode switching:

```css
/* Theme variables in frontend/src/styles/main.css */
:root {
  --color-background: 244 241 232; /* parchment */
  --color-foreground: 29 25 22;    /* dark text */
  --color-primary: 96 72 48;       /* fantasy brown */
  --color-accent: 212 175 55;      /* gold */
  --color-card: 248 245 238;       /* light parchment */
  --color-border: 212 175 55;      /* gold border */
}

.dark {
  --color-background: 29 25 22;    /* dark background */
  --color-foreground: 232 226 208; /* light text */
  /* ... other dark mode colors */
}
```

**Using Theme Colors:**
```vue
<template>
  <!-- Use theme-aware classes -->
  <div class="bg-background text-foreground border-border">
    <h1 class="text-primary">Title</h1>
    <p class="text-accent">Accent text</p>
  </div>
</template>
```

#### Character Creation System

The character creation system uses a 7-step wizard approach:

1. **Content Pack Selection** - Choose which content packs to use for this character
2. **Basic Information** - Name, alignment, background
3. **Race & Class Selection** - With subrace/subclass options
4. **Ability Scores** - Point buy, standard array, or rolling
5. **Skills & Proficiencies** - Class and background skills
6. **Equipment & Spells** - Starting gear and spellcaster options
7. **Review & Confirm** - Final validation and character creation

**Key Features:**
- **Per-Character Content Packs**: Each character selects their own content packs during creation
- **Dynamic Loading**: All options (races, classes, spells, etc.) are loaded from selected content packs
- **Visual Indicators**: Content pack badges show the source of each option
- **Validation**: Real-time validation ensures D&D 5e rule compliance

#### Campaign Management

Campaign creation includes content pack compatibility features:

- **Character Selection**: Rich previews showing class, race, level, and content packs
- **Compatibility Indicators**: Visual indicators show character-template compatibility
  - 🟢 Green: Perfect match (all content packs compatible)
  - 🟡 Yellow: Partial match (some content pack differences)
  - 🔴 Red: Incompatible (major content pack conflicts)
- **Filtering**: Search and filter characters by class, level, and compatibility

#### Best Practices

**Component Development:**
1. **Always use base components** instead of creating custom form elements
2. **Follow the theme system** - use CSS variables, not hardcoded colors
3. **Add proper TypeScript types** for all props and emits
4. **Use semantic HTML** with proper accessibility attributes
5. **Test with both light and dark themes**

**Content Pack Integration:**
1. **Always show content pack sources** using `ContentPackBadge.vue`
2. **Load options dynamically** from selected content packs
3. **Provide fallbacks** when content packs are unavailable
4. **Validate selections** against available content

**State Management:**
1. **Use Pinia stores** for shared state
2. **Keep component state local** when possible
3. **Emit events** for parent-child communication
4. **Use computed properties** for derived state

#### Development Workflow

```bash
# Frontend development commands
npm --prefix frontend run dev      # Start development server
npm --prefix frontend run build    # Build for production
npm --prefix frontend run lint     # Run ESLint
npm --prefix frontend run format   # Format with Prettier

# Type generation (run after backend model changes)
python scripts/dev/generate_ts.py
```

The frontend build process automatically:
- Generates TypeScript types from backend models
- Optimizes assets and applies tree-shaking
- Validates all TypeScript and Vue files
- Applies consistent code formatting