# AI-Gamemaster: FastAPI Migration & Service-Oriented Architecture Plan

This comprehensive plan guides the transformation of the AI-Gamemaster application from Flask to FastAPI while establishing a service-oriented architecture. Every task is designed with sufficient context for junior engineers to execute without ambiguity.

## Executive Summary

### Goals
1. **Migrate from Flask to FastAPI** for improved performance, type safety, and automatic API documentation
2. **Establish Service-Oriented Architecture** with clear boundaries between services
3. **Enforce Development Principles** (KISS, YAGNI, DRY, SRP) throughout the codebase
4. **Improve Type Safety** by eliminating Dict[str, Any] usage where possible
5. **Simplify Complex Patterns** like SharedStateManager that violate KISS

### Architecture Vision
```
app/
├── interfaces/           # All abstract interfaces (contracts)
├── domain/              # Core business logic
├── orchestration/       # Coordination layer
├── providers/           # External system integrations
│   ├── ai/             # AI service providers
│   ├── tts/            # Text-to-speech providers
│   └── storage/        # Storage providers
├── api/                # FastAPI routes
├── models/             # Pydantic models (request/response DTOs)
└── content/            # D&D 5e content (already well-organized)
```

---

## Phase 0: Foundation Strengthening

**Goal:** Prepare the codebase for major changes by consolidating configuration and ensuring type safety.

### Task 0.1: Configuration Consolidation

**Why:** Currently, configuration is spread between `app/config.py`, `app/settings.py`, and various `to_service_config_dict()` conversions. This violates DRY and makes configuration management complex.

**Context for Junior Engineers:**
- `app/settings.py` uses Pydantic Settings for type-safe configuration
- `app/config.py` is a legacy file that should be removed
- The container currently uses a complex `_get_config_value` method that maps between different config formats

**Implementation Steps:**

1. **Delete the legacy config file:**
   ```bash
   rm app/config.py
   ```

2. **Update `app/core/container.py`:**
   
   **File:** `app/core/container.py`
   
   **Current State:** The `ServiceContainer.__init__` accepts various config types and has a complex `_get_config_value` method.
   
   **Changes Required:**
   ```python
   # Update imports
   from app.settings import Settings, get_settings
   
   # Update __init__ method
   def __init__(self, config: Optional[Union[Dict[str, Any], ServiceConfigModel, Settings]] = None):
       """Initialize the service container with settings."""
       # Convert all config types to Settings
       if isinstance(config, Settings):
           self.settings = config
       elif isinstance(config, dict):
           # For backward compatibility during migration
           self.settings = get_settings()
           # Log warning about deprecated dict config
           logging.warning("Dict config is deprecated, use Settings object")
       elif isinstance(config, ServiceConfigModel):
           # For backward compatibility during migration
           self.settings = get_settings()
           logging.warning("ServiceConfigModel config is deprecated, use Settings object")
       else:
           self.settings = get_settings()
       
       self._services: Dict[str, Any] = {}
       self._initialized = False
   
   # Delete the entire _get_config_value method
   # It's overly complex and violates KISS
   ```

3. **Update all `_create_*` methods in ServiceContainer:**
   
   **Pattern to Apply:**
   ```python
   # BEFORE (example from _create_game_state_repository)
   repo_type = self._get_config_value("GAME_STATE_REPO_TYPE", "memory")
   base_save_dir = str(self._get_config_value("SAVES_DIR", "saves"))
   
   # AFTER
   repo_type = self.settings.storage.game_state_repo_type
   base_save_dir = self.settings.storage.saves_dir
   ```
   
   **Complete the following replacements:**
   - `_create_game_state_repository`: Use `self.settings.storage.*`
   - `_create_campaign_repository`: Use `self.settings.storage.campaigns_dir`
   - `_create_character_repository`: Use `self.settings.storage.character_templates_dir`
   - `_create_database_manager`: Use `self.settings.database.content_db_path`
   - `_create_rag_service`: Use `self.settings.rag.enabled`, `self.settings.rag.provider`
   - `_create_event_queue`: Use `self.settings.system.event_queue_max_size`
   - `_create_tts_service`: Use `self.settings.tts.provider`, `self.settings.tts.cache_dir`

4. **Update `app/__init__.py`:**
   
   **File:** `app/__init__.py`
   
   **Changes:**
   ```python
   def create_app(test_config: Optional[Settings] = None) -> Flask:
       """Flask application factory."""
       app = Flask(__name__, static_folder="../static", static_url_path="/static")
       
       # Use Settings directly
       settings = test_config or get_settings()
       
       # For Flask compatibility (temporary during migration)
       app.config.update(settings.to_service_config_dict())
       
       # ... rest of function ...
       
       # Pass Settings object to container
       from .core.container import initialize_container
       initialize_container(settings)
   ```

**Verification:**
```bash
# Run tests
pytest tests/

# Start the application
python run.py

# Verify no import errors or config access errors
```

### Task 0.2: Type Safety Audit

**Why:** The codebase uses `Dict[str, Any]` in many places, losing type safety. This makes the code harder to understand and maintain.

**Context for Junior Engineers:**
- `Dict[str, Any]` means "a dictionary with string keys and any values"
- This provides no information about what keys exist or what types the values should be
- Pydantic models provide type safety and validation

**Implementation Steps:**

1. **Identify all Dict[str, Any] usage:**
   ```bash
   grep -r "Dict\[str, Any\]" app/ --include="*.py" | grep -v "__pycache__" > dict_any_usage.txt
   ```

2. **Create specific models for common patterns:**
   
   **File:** `app/models/common.py` (new file)
   ```python
   """Common type-safe models to replace Dict[str, Any] usage."""
   
   from typing import Optional, List
   from pydantic import BaseModel, Field
   
   
   class MessageDict(BaseModel):
       """Type-safe message for AI interactions."""
       role: str = Field(..., description="Message role (system/user/assistant)")
       content: str = Field(..., description="Message content")
   
   
   class ErrorResponse(BaseModel):
       """Type-safe error response."""
       error: str = Field(..., description="Error message")
       status_code: int = Field(..., description="HTTP status code")
       details: Optional[dict] = Field(None, description="Additional error details")
   
   
   class SuccessResponse(BaseModel):
       """Type-safe success response."""
       message: str = Field(..., description="Success message")
       data: Optional[dict] = Field(None, description="Response data")
   ```

3. **Replace Dict[str, Any] in critical interfaces:**
   
   **Example - Update AI interfaces:**
   ```python
   # In app/core/ai_interfaces.py
   from app.models.common import MessageDict
   
   # BEFORE
   def generate_response(self, messages: List[Dict[str, str]], ...) -> Optional[AIResponse]:
   
   # AFTER
   def generate_response(self, messages: List[MessageDict], ...) -> Optional[AIResponse]:
   ```

**Note:** Complete type replacement will be ongoing throughout the migration. Focus on interfaces first.

---

## Phase 1: Flask to FastAPI Migration

**Goal:** Replace Flask with FastAPI while maintaining all functionality.

### Task 1.1: FastAPI Setup

**Why:** FastAPI provides better performance, automatic API documentation, and native async support.

**Context for Junior Engineers:**
- FastAPI uses ASGI (async) instead of WSGI (sync)
- Uvicorn is the ASGI server (replaces Flask's built-in server)
- FastAPI automatically generates OpenAPI/Swagger documentation

**Implementation Steps:**

1. **Install dependencies:**
   ```bash
   pip install "fastapi[all]" "uvicorn[standard]"
   
   # Add to requirements.txt
   fastapi==0.115.13
   uvicorn[standard]==0.34.3
   ```

2. **Create `main.py` in project root:**
   
   **File:** `main.py` (new)
   ```python
   """
   FastAPI application entry point.
   
   This replaces the Flask entry point in run.py during migration.
   """
   
   import os
   import uvicorn
   from app import create_app
   
   # Create FastAPI application
   app = create_app()
   
   if __name__ == "__main__":
       # Get debug mode from environment
       is_debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1')
       
       # Configure Uvicorn
       uvicorn.run(
           "main:app",
           host="127.0.0.1",
           port=5000,
           reload=is_debug,
           log_level="debug" if is_debug else "info",
           access_log=True
       )
   ```

3. **Update `run.py` for backward compatibility:**
   
   **File:** `run.py`
   ```python
   """
   Legacy entry point - redirects to new FastAPI application.
   
   This ensures existing scripts/documentation still work.
   """
   
   import os
   import uvicorn
   
   if __name__ == "__main__":
       print("Note: run.py is deprecated. Use 'python main.py' instead.")
       
       is_debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1')
       uvicorn.run(
           "main:app",
           host="127.0.0.1",
           port=5000,
           reload=is_debug
       )
   ```

### Task 1.2: Convert Application Factory

**Why:** The app factory needs to create a FastAPI instance instead of Flask.

**Context for Junior Engineers:**
- FastAPI uses `app.state` to store application-wide objects
- FastAPI doesn't have `app.config` like Flask
- Logging setup needs minor adjustments

**Implementation Steps:**

1. **Create new FastAPI factory:**
   
   **File:** `app/factory.py` (new - temporary during migration)
   ```python
   """
   FastAPI application factory.
   
   This is temporary during migration. Will replace app/__init__.py.
   """
   
   import logging
   from typing import Optional
   
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   from fastapi.staticfiles import StaticFiles
   
   from app.settings import Settings, get_settings
   from app.core.container import initialize_container, get_container
   
   
   def setup_logging(settings: Settings) -> None:
       """Configure application logging."""
       log_level = getattr(logging, settings.system.log_level.upper())
       
       logging.basicConfig(
           level=log_level,
           format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
           handlers=[
               logging.StreamHandler(),
               logging.FileHandler(settings.system.log_file) if settings.system.log_file else None
           ]
       )
       
       logger = logging.getLogger(__name__)
       logger.info(f"Logging configured. Level: {settings.system.log_level}")
   
   
   def create_fastapi_app(test_config: Optional[Settings] = None) -> FastAPI:
       """Create and configure FastAPI application."""
       
       # Load settings
       settings = test_config or get_settings()
       
       # Create FastAPI app
       app = FastAPI(
           title="AI Game Master",
           description="AI-powered D&D 5e game master",
           version="1.0.0",
           docs_url="/api/docs",
           redoc_url="/api/redoc"
       )
       
       # Store settings in app state
       app.state.settings = settings
       
       # Setup logging
       setup_logging(settings)
       
       # Initialize service container
       initialize_container(settings)
       app.state.container = get_container()
       
       # Configure CORS
       app.add_middleware(
           CORSMiddleware,
           allow_origins=["*"],  # Configure appropriately for production
           allow_credentials=True,
           allow_methods=["*"],
           allow_headers=["*"],
       )
       
       # Mount static files
       app.mount("/static", StaticFiles(directory="static"), name="static")
       
       # Initialize routes
       from app.api import initialize_fastapi_routes
       initialize_fastapi_routes(app)
       
       logging.info("FastAPI application created and configured")
       return app
   ```

2. **Update main.py to use new factory:**
   
   **File:** `main.py`
   ```python
   from app.factory import create_fastapi_app
   
   app = create_fastapi_app()
   
   # ... rest of file unchanged ...
   ```

### Task 1.3: Convert Routes (Incremental Approach)

**Why:** Converting routes incrementally allows testing each endpoint immediately.

**Context for Junior Engineers:**
- Flask uses `Blueprint` and `@bp.route()`
- FastAPI uses `APIRouter` and `@router.get()`, `@router.post()`, etc.
- FastAPI automatically handles JSON serialization/deserialization
- Request validation happens via Pydantic models in function parameters

**Step 1.3.1: Convert Health Routes (Simplest)**

1. **Convert health.py:**
   
   **File:** `app/api/health_fastapi.py` (new - temporary name)
   ```python
   """
   Health check endpoints for monitoring system status.
   
   FastAPI version - replaces Flask blueprint.
   """
   
   import time
   from typing import Dict
   
   from fastapi import APIRouter, Depends, HTTPException
   from sqlalchemy import text
   
   from app.api.dependencies import get_container_dep
   from app.core.container import ServiceContainer
   
   # Create router instead of blueprint
   router = APIRouter(
       prefix="/api",
       tags=["health"]
   )
   
   
   @router.get("/health")
   async def health_check() -> Dict[str, str]:
       """Basic health check endpoint."""
       return {"status": "healthy", "service": "ai-gamemaster"}
   
   
   @router.get("/health/database")
   async def database_health(
       container: ServiceContainer = Depends(get_container_dep)
   ) -> Dict[str, any]:
       """
       Check database connectivity and content status.
       
       Returns:
           Database status with table counts and timing
       """
       start_time = time.time()
       
       try:
           db_manager = container.get_database_manager()
           
           with db_manager.get_session() as session:
               # Check connectivity
               session.execute(text("SELECT 1")).scalar()
               
               # Get table counts
               tables = ["spells", "monsters", "equipment", "classes", "features"]
               counts = {}
               
               for table in tables:
                   try:
                       count = session.execute(
                           text(f"SELECT COUNT(*) FROM {table}")
                       ).scalar()
                       counts[table] = count or 0
                   except Exception:
                       counts[table] = -1
               
               # ... rest of logic ...
               
               elapsed_ms = round((time.time() - start_time) * 1000, 2)
               
               return {
                   "status": "healthy",
                   "database": {
                       "connected": True,
                       "table_counts": counts,
                       "response_time_ms": elapsed_ms
                   }
               }
               
       except Exception as e:
           elapsed_ms = round((time.time() - start_time) * 1000, 2)
           raise HTTPException(
               status_code=503,
               detail={
                   "status": "unhealthy",
                   "database": {
                       "connected": False,
                       "error": str(e),
                       "response_time_ms": elapsed_ms
                   }
               }
           )
   ```

2. **Create FastAPI dependencies:**
   
   **File:** `app/api/dependencies_fastapi.py` (new)
   ```python
   """
   FastAPI dependency injection functions.
   
   These replace the get_* functions used in Flask routes.
   """
   
   from typing import Generator
   
   from fastapi import Depends, Request
   
   from app.core.container import ServiceContainer, get_container
   from app.settings import Settings
   
   
   def get_settings(request: Request) -> Settings:
       """Get settings from app state."""
       return request.app.state.settings
   
   
   def get_container_dep() -> ServiceContainer:
       """Get service container."""
       return get_container()
   
   
   def get_game_orchestrator(
       container: ServiceContainer = Depends(get_container_dep)
   ):
       """Get game orchestrator service."""
       return container.get_game_orchestrator()
   
   
   def get_character_template_repository(
       container: ServiceContainer = Depends(get_container_dep)
   ):
       """Get character template repository."""
       return container.get_character_template_repository()
   
   # ... add other dependency functions as needed ...
   ```

3. **Create route initialization for FastAPI:**
   
   **File:** `app/api/init_fastapi.py` (new)
   ```python
   """
   FastAPI route initialization.
   
   Temporary during migration - will replace __init__.py.
   """
   
   from fastapi import FastAPI
   
   # Import routers as they're converted
   from .health_fastapi import router as health_router
   
   
   def initialize_fastapi_routes(app: FastAPI) -> None:
       """Initialize all FastAPI routes."""
       
       # Include routers
       app.include_router(health_router)
       
       # Add more routers as they're converted
       # app.include_router(character_router)
       # app.include_router(game_router)
       # etc.
   ```

**Verification for Task 1.3.1:**
```bash
# Start the application
python main.py

# In another terminal, test the endpoints
curl http://localhost:5000/api/health
curl http://localhost:5000/api/health/database

# Open browser to http://localhost:5000/api/docs
# You should see the health endpoints in the Swagger UI
```

**Step 1.3.2: Convert Character Routes (Complex Example)**

**Why:** Character routes demonstrate request body handling and validation.

1. **Create Pydantic models for requests:**
   
   **File:** `app/models/requests/character.py` (new)
   ```python
   """
   Request models for character endpoints.
   
   These replace request.get_json() validation.
   """
   
   from typing import Optional
   from pydantic import BaseModel, Field
   
   
   class CreateCharacterTemplateRequest(BaseModel):
       """Request model for creating character template."""
       name: str = Field(..., min_length=1, max_length=100)
       race_id: str = Field(..., description="D&D 5e race ID")
       class_id: str = Field(..., description="D&D 5e class ID")
       background_id: str = Field(..., description="D&D 5e background ID")
       level: int = Field(1, ge=1, le=20)
       ability_scores: dict = Field(..., description="STR, DEX, CON, INT, WIS, CHA")
       
       class Config:
           json_schema_extra = {
               "example": {
                   "name": "Gandalf",
                   "race_id": "human",
                   "class_id": "wizard",
                   "background_id": "sage",
                   "level": 20,
                   "ability_scores": {
                       "str": 10, "dex": 12, "con": 14,
                       "int": 20, "wis": 18, "cha": 16
                   }
               }
           }
   ```

2. **Convert character routes:**
   
   **File:** `app/api/character_fastapi.py` (new)
   ```python
   """Character management endpoints - FastAPI version."""
   
   from typing import List
   from fastapi import APIRouter, Depends, HTTPException, status
   
   from app.api.dependencies_fastapi import get_character_template_repository
   from app.core.repository_interfaces import ICharacterTemplateRepository
   from app.models.character import CharacterTemplateModel
   from app.models.requests.character import CreateCharacterTemplateRequest
   
   router = APIRouter(
       prefix="/api",
       tags=["characters"]
   )
   
   
   @router.get("/character_templates", response_model=List[CharacterTemplateModel])
   async def get_character_templates(
       repo: ICharacterTemplateRepository = Depends(get_character_template_repository)
   ) -> List[CharacterTemplateModel]:
       """Get all character templates."""
       try:
           templates = repo.list()
           return templates
       except Exception as e:
           raise HTTPException(
               status_code=500,
               detail=f"Failed to fetch templates: {str(e)}"
           )
   
   
   @router.post(
       "/character_templates",
       response_model=CharacterTemplateModel,
       status_code=status.HTTP_201_CREATED
   )
   async def create_character_template(
       request: CreateCharacterTemplateRequest,
       repo: ICharacterTemplateRepository = Depends(get_character_template_repository)
   ) -> CharacterTemplateModel:
       """Create a new character template."""
       try:
           # Convert request to domain model
           template = CharacterTemplateModel(
               name=request.name,
               race_id=request.race_id,
               class_id=request.class_id,
               background_id=request.background_id,
               level=request.level,
               ability_scores=request.ability_scores
           )
           
           # Save to repository
           saved_template = repo.create(template)
           return saved_template
           
       except ValueError as e:
           raise HTTPException(
               status_code=400,
               detail=str(e)
           )
       except Exception as e:
           raise HTTPException(
               status_code=500,
               detail=f"Failed to create template: {str(e)}"
           )
   ```

**Pattern for Converting Remaining Routes:**

For each route file:
1. Create request/response models in `app/models/requests/`
2. Create FastAPI router with appropriate prefix and tags
3. Convert Flask decorators to FastAPI decorators
4. Replace `request.get_json()` with Pydantic model parameters
5. Replace `jsonify()` with direct dict/model returns
6. Replace Flask error handling with HTTPException
7. Use Depends() for dependency injection
8. Add response_model to endpoints for automatic validation

### Task 1.4: Comprehensive Type Safety Refactoring

**Why:** After migrating all Flask routes to FastAPI, many endpoints still use Dict[str, Any] which defeats the purpose of FastAPI's type safety benefits.

**Context for Junior Engineers:**
- FastAPI's main advantage is automatic request/response validation through Pydantic models
- Dict[str, Any] provides no type safety and prevents automatic API documentation generation
- Custom response structures should have dedicated Pydantic models

**Implementation Steps:**

1. **Audit all FastAPI routes for Dict[str, Any] usage:**
   ```bash
   grep -r "Dict\[str, Any\]" app/api/*_fastapi.py
   ```

2. **Create response models for each endpoint:**
   
   **File:** `app/models/api/responses.py` (new)
   ```python
   """
   API response models for type-safe FastAPI endpoints.
   """
   
   from typing import List, Optional
   from pydantic import BaseModel, Field
   
   from app.models.character import CharacterTemplateModel
   
   
   class CharacterTemplatesResponse(BaseModel):
       """Response for GET /character_templates."""
       templates: List[CharacterTemplateModel]
   
   
   class CharacterCreationOptionsResponse(BaseModel):
       """Response for GET /character_templates/options."""
       options: 'CharacterCreationOptions'
       metadata: 'OptionsMetadata'
   
   
   class CharacterCreationOptions(BaseModel):
       """Character creation options."""
       races: List[dict]  # TODO: Replace with RaceModel when available
       classes: List[dict]  # TODO: Replace with ClassModel when available
       backgrounds: List[dict]  # TODO: Replace with BackgroundModel when available
       alignments: List[dict]
       languages: List[dict]
       skills: List[dict]
       ability_scores: List[dict]
   
   
   class OptionsMetadata(BaseModel):
       """Metadata for character creation options."""
       content_pack_ids: Optional[List[str]]
       total_races: int
       total_classes: int
       total_backgrounds: int
   
   
   class CharacterAdventuresResponse(BaseModel):
       """Response for GET /character_templates/{id}/adventures."""
       character_name: str
       adventures: List['AdventureInfo']
   
   
   class AdventureInfo(BaseModel):
       """Information about a character's adventure/campaign."""
       campaign_id: Optional[str]
       campaign_name: Optional[str]
       template_id: Optional[str]
       last_played: Optional[str]
       created_date: Optional[str]
       session_count: int
       current_location: Optional[str]
       in_combat: bool
       character_data: 'CharacterData'
   
   
   class CharacterData(BaseModel):
       """Character status data in a campaign."""
       current_hp: int
       max_hp: int
       level: int
       class: str
       experience: int
   ```

3. **Create request models for complex endpoints:**
   
   **File:** `app/models/api/requests.py` (new)
   ```python
   """
   API request models for type-safe FastAPI endpoints.
   """
   
   from typing import Optional
   from pydantic import BaseModel, Field
   
   
   class CharacterTemplateCreateRequest(BaseModel):
       """Request for creating character templates.
       
       Handles frontend-specific field mappings.
       """
       # Core character data - use the same fields as CharacterTemplateModel
       # but handle skill_proficiencies separately for frontend compatibility
       name: str
       race: str
       char_class: str
       # ... other fields ...
       skill_proficiencies: Optional[List[str]] = None
       
       # Add preprocessing logic as needed
   ```

4. **Update all FastAPI routes to use typed models:**
   
   **Pattern to apply:**
   ```python
   # BEFORE
   async def get_data() -> Dict[str, Any]:
       return {"key": "value"}
   
   # AFTER
   async def get_data() -> TypedResponseModel:
       return TypedResponseModel(key="value")
   ```

5. **Ensure all routes have proper response_model declarations:**
   ```python
   @router.get("/endpoint", response_model=TypedResponseModel)
   async def endpoint() -> TypedResponseModel:
       # Implementation
   ```

**Benefits:**
- Automatic API documentation generation with proper schemas
- Request/response validation at runtime
- Better IDE support and autocompletion
- Type safety throughout the application
- Clearer API contracts

**Verification:**
- No Dict[str, Any] in any FastAPI route file
- All endpoints have response_model declarations
- OpenAPI docs show proper schemas for all endpoints
- All type checking passes with mypy --strict

### Task 1.5: Error Response Format Consistency

**Why:** FastAPI's HTTPException uses `{"detail": "message"}` format by default, while the Flask application uses `{"error": "message"}`. This inconsistency could break frontend error handling that expects the "error" key.

**Context for Junior Engineers:**
- Flask routes return error responses as `jsonify({"error": "message"}), status_code`
- FastAPI HTTPException produces `{"detail": "message"}` format
- Frontend code may depend on the specific error key for displaying error messages
- We need to maintain backward compatibility during migration

**Implementation Steps:**

1. **Create custom exception handler:**
   
   **File:** `app/api/exception_handlers.py` (new)
   ```python
   """
   Custom exception handlers for FastAPI to maintain Flask compatibility.
   """
   
   from fastapi import Request, status
   from fastapi.exceptions import HTTPException, RequestValidationError
   from fastapi.responses import JSONResponse
   from pydantic import ValidationError
   
   
   async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
       """
       Custom handler for HTTPException to maintain Flask error format.
       
       Converts {"detail": "message"} to {"error": "message"} for compatibility.
       """
       # Get the detail message
       detail = exc.detail
       
       # If detail is a string, wrap it in error key
       if isinstance(detail, str):
           content = {"error": detail}
       # If detail is already a dict with "error" key, use as-is
       elif isinstance(detail, dict) and "error" in detail:
           content = detail
       # Otherwise, wrap the entire detail in error key
       else:
           content = {"error": detail}
       
       return JSONResponse(
           status_code=exc.status_code,
           content=content,
           headers=exc.headers,
       )
   
   
   async def validation_exception_handler(
       request: Request, exc: RequestValidationError
   ) -> JSONResponse:
       """
       Custom handler for request validation errors.
       
       Provides user-friendly error messages for Pydantic validation failures.
       """
       # Extract first error for simple message
       errors = exc.errors()
       if errors:
           first_error = errors[0]
           loc = " -> ".join(str(x) for x in first_error["loc"])
           msg = f"Validation error in {loc}: {first_error['msg']}"
       else:
           msg = "Request validation failed"
       
       return JSONResponse(
           status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
           content={"error": msg, "validation_errors": errors},
       )
   
   
   async def pydantic_validation_exception_handler(
       request: Request, exc: ValidationError
   ) -> JSONResponse:
       """
       Custom handler for Pydantic validation errors.
       
       This handles model validation errors in route handlers.
       """
       return JSONResponse(
           status_code=status.HTTP_400_BAD_REQUEST,
           content={"error": "Invalid request data", "details": exc.errors()},
       )
   ```

2. **Register exception handlers in FastAPI app:**
   
   **File:** `app/factory.py`
   
   **Add after app creation (around line 50):**
   ```python
   # Import at top of file
   from fastapi.exceptions import HTTPException, RequestValidationError
   from pydantic import ValidationError
   
   # After app creation, before middleware
   # Register custom exception handlers for Flask compatibility
   from app.api.exception_handlers import (
       http_exception_handler,
       validation_exception_handler,
       pydantic_validation_exception_handler,
   )
   
   app.add_exception_handler(HTTPException, http_exception_handler)
   app.add_exception_handler(RequestValidationError, validation_exception_handler)
   app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
   ```

3. **Update HTTPException usage in routes (optional):**
   
   For routes that need specific error formats, you can now use:
   ```python
   # Simple string error (will be wrapped in {"error": "..."})
   raise HTTPException(status_code=404, detail="Resource not found")
   
   # Complex error with additional fields
   raise HTTPException(
       status_code=400,
       detail={"error": "Validation failed", "fields": ["name", "email"]}
   )
   ```

**Verification:**
```bash
# Test error responses
curl -X GET http://localhost:5000/api/character_templates/invalid-id
# Should return: {"error": "Character template not found"}

# Test validation errors
curl -X POST http://localhost:5000/api/character_templates \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
# Should return: {"error": "Validation error...", "validation_errors": [...]}
```

**Benefits:**
- Maintains backward compatibility with Flask error format
- Frontend continues to work without changes
- Provides consistent error handling across all FastAPI routes
- Can be removed later when frontend is updated to handle FastAPI format

---

## Phase 2: Service-Oriented Architecture

**Goal:** Reorganize code into clear service boundaries following the content module pattern.

### Task 2.1: Create Service Modules

**Why:** Current code mixes concerns. Service modules provide clear boundaries and single responsibility.

**Context for Junior Engineers:**
- Each service module should be self-contained
- Services communicate through interfaces, not direct imports
- Follow the pattern established by `app/content/`

**Step 2.1.1: AI Service Module**

1. **Create directory structure:**
   ```bash
   mkdir -p app/services_v2/ai/{providers,prompts,processors}
   touch app/services_v2/ai/__init__.py
   ```

2. **Create AI service interface:**
   
   **File:** `app/services_v2/ai/interface.py`
   ```python
   """
   AI service interface definition.
   
   This defines the contract that all AI services must implement.
   """
   
   from abc import ABC, abstractmethod
   from typing import List, Optional
   
   from app.models.common import MessageDict
   from app.providers.ai.schemas import AIResponse
   
   
   class IAIService(ABC):
       """Abstract interface for AI services."""
       
       @abstractmethod
       async def generate_response(
           self,
           messages: List[MessageDict],
           system_prompt: Optional[str] = None,
           temperature: Optional[float] = None,
           max_tokens: Optional[int] = None
       ) -> AIResponse:
           """Generate AI response for messages."""
           pass
       
       @abstractmethod
       async def generate_with_retry(
           self,
           messages: List[MessageDict],
           system_prompt: Optional[str] = None,
           max_retries: Optional[int] = None
       ) -> AIResponse:
           """Generate response with automatic retry logic."""
           pass
       
       @abstractmethod
       def validate_response(self, response: AIResponse) -> bool:
           """Validate AI response format and content."""
           pass
   ```

3. **Create unified AI service:**
   
   **File:** `app/services_v2/ai/service.py`
   ```python
   """
   Unified AI service implementation.
   
   This orchestrates different AI providers and handles common logic.
   """
   
   import logging
   from typing import List, Optional, Dict, Any
   
   from app.services_v2.ai.interface import IAIService
   from app.models.common import MessageDict
   from app.providers.ai.schemas import AIResponse
   from app.settings import Settings
   
   logger = logging.getLogger(__name__)
   
   
   class AIService(IAIService):
       """Main AI service implementation."""
       
       def __init__(self, settings: Settings):
           self.settings = settings
           self._provider = self._create_provider()
           
       def _create_provider(self):
           """Create AI provider based on settings."""
           if self.settings.ai.provider == "openrouter":
               from app.services_v2.ai.providers.openrouter import OpenRouterProvider
               return OpenRouterProvider(self.settings)
           elif self.settings.ai.provider == "llamacpp_http":
               from app.services_v2.ai.providers.llamacpp import LlamaCppProvider
               return LlamaCppProvider(self.settings)
           else:
               raise ValueError(f"Unknown AI provider: {self.settings.ai.provider}")
       
       async def generate_response(
           self,
           messages: List[MessageDict],
           system_prompt: Optional[str] = None,
           temperature: Optional[float] = None,
           max_tokens: Optional[int] = None
       ) -> AIResponse:
           """Generate AI response."""
           # Apply defaults from settings
           temperature = temperature or self.settings.ai.temperature
           max_tokens = max_tokens or self.settings.ai.max_tokens
           
           # Log request
           logger.info(f"Generating AI response with {len(messages)} messages")
           
           try:
               response = await self._provider.generate(
                   messages=messages,
                   system_prompt=system_prompt,
                   temperature=temperature,
                   max_tokens=max_tokens
               )
               
               if not self.validate_response(response):
                   raise ValueError("Invalid AI response format")
                   
               return response
               
           except Exception as e:
               logger.error(f"AI generation failed: {e}")
               raise
       
       async def generate_with_retry(
           self,
           messages: List[MessageDict],
           system_prompt: Optional[str] = None,
           max_retries: Optional[int] = None
       ) -> AIResponse:
           """Generate with retry logic."""
           max_retries = max_retries or self.settings.ai.max_retries
           
           for attempt in range(max_retries):
               try:
                   return await self.generate_response(
                       messages=messages,
                       system_prompt=system_prompt
                   )
               except Exception as e:
                   if attempt == max_retries - 1:
                       raise
                   logger.warning(f"AI attempt {attempt + 1} failed: {e}")
                   # Add exponential backoff here
           
           raise RuntimeError("All retry attempts failed")
       
       def validate_response(self, response: AIResponse) -> bool:
           """Validate response format."""
           if not response or not response.content:
               return False
           
           # Add more validation based on response parsing mode
           if self.settings.ai.response_parsing_mode == "strict":
               # Validate JSON structure
               pass
               
           return True
   ```

4. **Move and refactor AI providers:**
   ```bash
   # Move existing providers
   mv app/providers/ai/openai_service.py app/services_v2/ai/providers/openrouter.py
   mv app/providers/ai/llamacpp_service.py app/services_v2/ai/providers/llamacpp.py
   
   # Update imports and refactor to match new structure
   ```

**Step 2.1.2: TTS Service Module**

Follow the same pattern:
1. Create directory structure
2. Define interface
3. Create unified service
4. Move providers

**Step 2.1.3: Game Orchestration Module**

1. **Create structure:**
   ```bash
   mkdir -p app/services_v2/orchestration/{handlers,processors,state}
   ```

2. **Move orchestration components:**
   ```bash
   mv app/services/game_orchestrator.py app/services_v2/orchestration/
   mv app/services/action_handlers/* app/services_v2/orchestration/handlers/
   mv app/services/ai_response_processors/* app/services_v2/orchestration/processors/
   ```

### Task 2.2: Simplify Request Context Management

**Why:** SharedStateManager is overly complex for a single-user application (violates KISS).

**Context for Junior Engineers:**
- Current SharedStateManager uses instance variables for a single-user app
- No need for complex state management
- Can be simplified to a basic context manager

1. **Create simplified context manager:**
   
   **File:** `app/services_v2/orchestration/context.py`
   ```python
   """
   Simple request context management.
   
   Replaces overly complex SharedStateManager.
   """
   
   import time
   from typing import Optional, List, Dict
   from dataclasses import dataclass, field
   from datetime import datetime
   
   from app.models.events import AIRequestContextModel
   
   
   @dataclass
   class RequestContext:
       """Simple request context for retry functionality."""
       messages: List[Dict[str, str]]
       instruction: Optional[str]
       timestamp: float = field(default_factory=time.time)
       
       def is_valid(self, timeout_seconds: int = 300) -> bool:
           """Check if context is still valid for retry."""
           return (time.time() - self.timestamp) < timeout_seconds
   
   
   class RequestContextManager:
       """
       Simple context manager for AI requests.
       
       Handles:
       - Processing state (prevents concurrent requests)
       - Retry context storage
       - Backend trigger flags
       """
       
       def __init__(self, timeout_seconds: int = 300):
           self.timeout_seconds = timeout_seconds
           self._is_processing = False
           self._last_context: Optional[RequestContext] = None
           self._needs_backend_trigger = False
       
       @property
       def is_processing(self) -> bool:
           """Check if currently processing a request."""
           return self._is_processing
       
       def start_processing(self) -> None:
           """Mark processing as started."""
           if self._is_processing:
               raise RuntimeError("Already processing a request")
           self._is_processing = True
       
       def end_processing(self) -> None:
           """Mark processing as completed."""
           self._is_processing = False
       
       def store_context(
           self,
           messages: List[Dict[str, str]],
           instruction: Optional[str] = None
       ) -> None:
           """Store context for potential retry."""
           self._last_context = RequestContext(
               messages=messages.copy(),  # Simple shallow copy
               instruction=instruction
           )
       
       def get_retry_context(self) -> Optional[AIRequestContextModel]:
           """Get stored context if still valid."""
           if not self._last_context:
               return None
               
           if not self._last_context.is_valid(self.timeout_seconds):
               self._last_context = None
               return None
           
           return AIRequestContextModel(
               messages=self._last_context.messages,
               initial_instruction=self._last_context.instruction
           )
       
       @property
       def needs_backend_trigger(self) -> bool:
           """Check if backend trigger is needed."""
           return self._needs_backend_trigger
       
       @needs_backend_trigger.setter
       def needs_backend_trigger(self, value: bool) -> None:
           """Set backend trigger flag."""
           self._needs_backend_trigger = value
       
       def reset(self) -> None:
           """Reset all state (useful for testing)."""
           self._is_processing = False
           self._last_context = None
           self._needs_backend_trigger = False
   ```

2. **Update container to use new manager:**
   
   **File:** `app/core/container.py`
   ```python
   # In _create_shared_state_manager method
   def _create_shared_state_manager(self) -> RequestContextManager:
       """Create request context manager."""
       from app.services_v2.orchestration.context import RequestContextManager
       
       timeout = self.settings.ai.retry_context_timeout
       return RequestContextManager(timeout_seconds=timeout)
   ```

3. **Update all handlers to use new API:**
   
   Pattern to apply:
   ```python
   # BEFORE
   if self._shared_state_manager.is_ai_processing():
       return error_response("AI is busy")
   
   self._shared_state_manager.set_ai_processing(True)
   try:
       # ... process ...
   finally:
       self._shared_state_manager.set_ai_processing(False)
   
   # AFTER
   if self._context_manager.is_processing:
       return error_response("AI is busy")
   
   self._context_manager.start_processing()
   try:
       # ... process ...
   finally:
       self._context_manager.end_processing()
   ```

---

## Phase 3: Testing & Migration Completion

### Task 3.1: Update Tests for FastAPI

**Why:** Tests need to use FastAPI's TestClient instead of Flask's test client.

**Context for Junior Engineers:**
- FastAPI uses `TestClient` from `fastapi.testclient`
- It supports async operations
- Request format is slightly different

1. **Update test fixtures:**
   
   **File:** `tests/conftest_fastapi.py` (new)
   ```python
   """FastAPI test configuration."""
   
   import pytest
   from fastapi.testclient import TestClient
   
   from app.factory import create_fastapi_app
   from app.settings import Settings
   
   
   @pytest.fixture
   def test_settings():
       """Create test settings."""
       return Settings(
           # Override settings for testing
           storage__game_state_repo_type="memory",
           rag__enabled=False,
           ai__provider="mock"
       )
   
   
   @pytest.fixture
   def test_app(test_settings):
       """Create test FastAPI app."""
       return create_fastapi_app(test_config=test_settings)
   
   
   @pytest.fixture
   def test_client(test_app):
       """Create test client."""
       return TestClient(test_app)
   ```

2. **Update test patterns:**
   
   Example conversion:
   ```python
   # BEFORE (Flask)
   def test_health_check(client):
       response = client.get('/api/health')
       assert response.status_code == 200
       data = response.get_json()
       assert data['status'] == 'healthy'
   
   # AFTER (FastAPI)
   def test_health_check(test_client):
       response = test_client.get('/api/health')
       assert response.status_code == 200
       data = response.json()
       assert data['status'] == 'healthy'
   ```

### Task 3.2: Parallel Running Strategy

**Why:** Run both Flask and FastAPI during migration to ensure nothing breaks.

1. **Create dual-mode runner:**
   
   **File:** `run_dual.py` (new)
   ```python
   """
   Run both Flask and FastAPI apps for testing during migration.
   
   Flask on port 5000, FastAPI on port 5001.
   """
   
   import multiprocessing
   import os
   
   
   def run_flask():
       """Run Flask app."""
       from app import create_app
       app = create_app()
       app.run(host='127.0.0.1', port=5000, debug=False)
   
   
   def run_fastapi():
       """Run FastAPI app."""
       import uvicorn
       uvicorn.run(
           "app.factory:create_fastapi_app",
           host="127.0.0.1",
           port=5001,
           reload=False
       )
   
   
   if __name__ == "__main__":
       # Create processes
       flask_process = multiprocessing.Process(target=run_flask)
       fastapi_process = multiprocessing.Process(target=run_fastapi)
       
       try:
           print("Starting Flask on http://127.0.0.1:5000")
           flask_process.start()
           
           print("Starting FastAPI on http://127.0.0.1:5001")
           print("FastAPI docs at http://127.0.0.1:5001/api/docs")
           fastapi_process.start()
           
           # Wait for processes
           flask_process.join()
           fastapi_process.join()
           
       except KeyboardInterrupt:
           print("\nShutting down...")
           flask_process.terminate()
           fastapi_process.terminate()
   ```

### Task 3.3: Frontend Update

**Why:** Frontend needs to point to new FastAPI endpoints.

1. **Update API base URL:**
   
   **File:** `frontend/src/config/api.js` (or similar)
   ```javascript
   // Add environment variable support
   const API_BASE_URL = process.env.VUE_APP_API_URL || 'http://127.0.0.1:5000';
   
   // During migration, can switch between Flask and FastAPI
   const USE_FASTAPI = process.env.VUE_APP_USE_FASTAPI === 'true';
   const API_PORT = USE_FASTAPI ? 5001 : 5000;
   ```

---

## Phase 4: Cleanup & Optimization

### Task 4.1: Remove Flask Dependencies

Once all routes are converted and tested:

1. **Remove Flask code:**
   ```bash
   # Remove old Flask routes
   rm app/api/*_routes.py
   
   # Remove Flask factory
   rm app/__init__.py
   mv app/factory.py app/__init__.py
   
   # Update imports
   ```

2. **Update dependencies:**
   ```bash
   # Remove from requirements.txt
   # - Flask
   # - Flask-CORS
   # - Flask-SSE
   
   # Keep only FastAPI dependencies
   ```

### Task 4.2: Performance Optimization

1. **Add async support where beneficial:**
   ```python
   # Convert CPU-bound operations to use thread pool
   from concurrent.futures import ThreadPoolExecutor
   import asyncio
   
   executor = ThreadPoolExecutor(max_workers=4)
   
   async def process_ai_response(data):
       # Run CPU-intensive parsing in thread pool
       loop = asyncio.get_event_loop()
       result = await loop.run_in_executor(
           executor,
           parse_complex_response,
           data
       )
       return result
   ```

2. **Add caching where appropriate:**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def get_spell_by_id(spell_id: str):
       # Cache frequently accessed data
       pass
   ```

### Task 4.3: Documentation Update

1. **Update README.md:**
   - Change all Flask references to FastAPI
   - Update setup instructions
   - Add API documentation URL

2. **Update API documentation:**
   - FastAPI generates OpenAPI spec automatically
   - Add descriptions to all endpoints
   - Include example requests/responses

3. **Update development guide:**
   - New project structure
   - Service module patterns
   - Testing with FastAPI

---

## Verification Checklist

After each phase, verify:

- [ ] All tests pass: `pytest tests/ --with-rag`
- [ ] Type checking passes: `mypy app --strict`
- [ ] Linting passes: `ruff check .`
- [ ] Frontend works with new endpoints
- [ ] API documentation is accessible at `/api/docs`
- [ ] No regression in functionality
- [ ] Performance is same or better
- [ ] Code follows KISS, YAGNI, DRY principles
- [ ] Each module has single responsibility
- [ ] No Dict[str, Any] in interfaces
- [ ] All configuration uses Settings object

---

## Common Pitfalls & Solutions

### Pitfall 1: Circular Imports
**Solution:** Use dependency injection and interfaces. Import interfaces, not implementations.

### Pitfall 2: Forgetting Async Context
**Solution:** Mark route handlers as `async def` when using async operations.

### Pitfall 3: Direct Service Access
**Solution:** Always use dependency injection with `Depends()`.

### Pitfall 4: Missing Request Validation
**Solution:** Create Pydantic models for all request bodies.

### Pitfall 5: Inconsistent Error Handling
**Solution:** Use HTTPException consistently, with proper status codes.

---

## Migration Timeline Estimate

- **Phase 0**: 1-2 days (Configuration & Type Safety)
- **Phase 1**: 4-7 days (FastAPI Migration)
  - Task 1.1-1.3: 3-5 days (Route Migration)
  - Task 1.4: 1-2 days (Type Safety Refactoring)
- **Phase 2**: 3-4 days (Service Architecture)
- **Phase 3**: 2-3 days (Testing & Validation)
- **Phase 4**: 1-2 days (Cleanup & Documentation)

**Total**: 11-18 days for complete migration

---

## Success Metrics

The migration is successful when:

1. All endpoints migrated to FastAPI
2. Zero Flask dependencies remain
3. Service modules have clear boundaries
4. All tests pass with >95% coverage
5. Type checking shows 0 errors
6. API documentation is auto-generated
7. Performance improved by >20%
8. Code complexity reduced (measurable via tools)
9. Junior engineers can understand and modify code easily
10. No Dict[str, Any] in public interfaces

This plan provides a clear, step-by-step path to modernize the AI-Gamemaster architecture while maintaining functionality and improving maintainability.