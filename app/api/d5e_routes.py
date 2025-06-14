"""
D&D 5e reference data API routes using the comprehensive D5e service layer.

This module provides REST API endpoints for all D&D 5e data categories
with advanced filtering and search capabilities.
"""

import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, cast

from flask import Blueprint, Response, jsonify, request

from app.content.service import ContentService
from app.core.container import get_container
from app.exceptions import (
    ApplicationError,
    EntityNotFoundError,
    HTTPException,
    NotFoundError,
    ValidationError,
    map_to_http_exception,
)

logger = logging.getLogger(__name__)

# Create blueprint for D&D 5e reference data routes
d5e_bp = Blueprint("d5e", __name__, url_prefix="/api/d5e")


def get_d5e_service() -> ContentService:
    """Get the content service from the container."""
    container = get_container()
    return container.get_content_service()


def _handle_service_error(operation: str, error: Exception) -> Tuple[Response, int]:
    """Handle service errors consistently."""
    # Map to appropriate HTTP exception
    http_error = map_to_http_exception(error)

    # Log the error with appropriate level
    if http_error.status_code >= 500:
        logger.error(
            f"Error in {operation}: {error}",
            exc_info=True,
            extra={"operation": operation, "error_type": type(error).__name__},
        )
    else:
        logger.warning(
            f"Client error in {operation}: {error}",
            extra={"operation": operation, "error_type": type(error).__name__},
        )

    return jsonify(http_error.to_dict()), http_error.status_code


def _serialize_entities(entities: Sequence[Any]) -> List[Dict[str, Any]]:
    """Serialize D5e entities to JSON-compatible dictionaries."""
    return [entity.model_dump() for entity in entities]


def _serialize_entity(entity: Optional[Any]) -> Optional[Dict[str, Any]]:
    """Serialize a single D5e entity to JSON-compatible dictionary."""
    return entity.model_dump() if entity else None


# Core Mechanics Endpoints
@d5e_bp.route("/ability-scores")
def get_ability_scores() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e ability scores."""
    try:
        service = get_d5e_service()
        abilities = service._hub.ability_scores.list_all()
        return jsonify(_serialize_entities(abilities))
    except Exception as e:
        return _handle_service_error("get ability scores", e)


@d5e_bp.route("/ability-scores/<string:index>")
def get_ability_score(index: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific ability score by index."""
    try:
        service = get_d5e_service()
        ability = service._hub.ability_scores.get_by_index(index)
        if not ability:
            raise NotFoundError(
                f"Ability score '{index}' not found", resource_type="AbilityScore"
            )
        return jsonify(_serialize_entity(ability))
    except Exception as e:
        return _handle_service_error("get ability score", e)


@d5e_bp.route("/skills")
def get_skills() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e skills."""
    try:
        service = get_d5e_service()
        skills = service._hub.skills.list_all()
        return jsonify(_serialize_entities(skills))
    except Exception as e:
        return _handle_service_error("get skills", e)


@d5e_bp.route("/skills/<string:index>")
def get_skill(index: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific skill by index."""
    try:
        service = get_d5e_service()
        skill = service._hub.skills.get_by_index(index)
        if not skill:
            raise NotFoundError(f"Skill '{index}' not found", resource_type="Skill")
        return jsonify(_serialize_entity(skill))
    except Exception as e:
        return _handle_service_error("get skill", e)


@d5e_bp.route("/proficiencies")
def get_proficiencies() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e proficiencies."""
    try:
        service = get_d5e_service()
        proficiencies = service._hub.proficiencies.list_all()
        return jsonify(_serialize_entities(proficiencies))
    except Exception as e:
        return _handle_service_error("get proficiencies", e)


@d5e_bp.route("/proficiencies/<string:index>")
def get_proficiency(index: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific proficiency by index."""
    try:
        service = get_d5e_service()
        proficiency = service._hub.proficiencies.get_by_index(index)
        if not proficiency:
            return jsonify({"error": "Proficiency not found"}), 404
        return jsonify(_serialize_entity(proficiency))
    except Exception as e:
        return _handle_service_error("get proficiency", e)


@d5e_bp.route("/alignments")
def get_alignments() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e alignments."""
    try:
        service = get_d5e_service()
        alignments = service._hub.alignments.list_all()
        return jsonify(_serialize_entities(alignments))
    except Exception as e:
        return _handle_service_error("get alignments", e)


@d5e_bp.route("/conditions")
def get_conditions() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e conditions."""
    try:
        service = get_d5e_service()
        conditions = service.get_conditions()
        return jsonify(_serialize_entities(conditions))
    except Exception as e:
        return _handle_service_error("get conditions", e)


@d5e_bp.route("/damage-types")
def get_damage_types() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e damage types."""
    try:
        service = get_d5e_service()
        damage_types = service._hub.damage_types.list_all()
        return jsonify(_serialize_entities(damage_types))
    except Exception as e:
        return _handle_service_error("get damage types", e)


@d5e_bp.route("/languages")
def get_languages() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e languages."""
    try:
        service = get_d5e_service()
        language_type = request.args.get("type")  # Optional filter by type
        languages = service.get_languages(language_type)
        return jsonify(_serialize_entities(languages))
    except Exception as e:
        return _handle_service_error("get languages", e)


# Character Options Endpoints
@d5e_bp.route("/classes")
def get_classes() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e classes."""
    try:
        service = get_d5e_service()
        classes = service._hub.classes.list_all()
        return jsonify(_serialize_entities(classes))
    except Exception as e:
        return _handle_service_error("get classes", e)


@d5e_bp.route("/classes/<string:index>")
def get_class(index: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific class by index."""
    try:
        service = get_d5e_service()
        # Get class data from database
        class_data = service._hub.classes.get_by_index(index)
        if not class_data:
            return jsonify({"error": "Class not found"}), 404
        return jsonify(class_data.model_dump())
    except Exception as e:
        return _handle_service_error("get class", e)


@d5e_bp.route("/classes/<string:index>/levels/<int:level>")
def get_class_at_level(index: str, level: int) -> Union[Response, Tuple[Response, int]]:
    """Get comprehensive class information at a specific level."""
    try:
        service = get_d5e_service()
        class_info = service.get_class_at_level(index, level)
        if not class_info:
            return jsonify({"error": "Class not found or invalid level"}), 404
        return jsonify(class_info)
    except Exception as e:
        return _handle_service_error("get class at level", e)


@d5e_bp.route("/subclasses")
def get_subclasses() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e subclasses."""
    try:
        service = get_d5e_service()
        subclasses = service._hub.subclasses.list_all()
        return jsonify(_serialize_entities(subclasses))
    except Exception as e:
        return _handle_service_error("get subclasses", e)


@d5e_bp.route("/races")
def get_races() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e races."""
    try:
        service = get_d5e_service()
        races = service._hub.races.list_all()
        return jsonify(_serialize_entities(races))
    except Exception as e:
        return _handle_service_error("get races", e)


@d5e_bp.route("/races/<string:index>")
def get_race(index: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific race by index."""
    try:
        service = get_d5e_service()
        race = service._hub.races.get_by_index(index)
        if not race:
            return jsonify({"error": "Race not found"}), 404
        return jsonify(_serialize_entity(race))
    except Exception as e:
        return _handle_service_error("get race", e)


@d5e_bp.route("/subraces")
def get_subraces() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e subraces."""
    try:
        service = get_d5e_service()
        subraces = service._hub.subraces.list_all()
        return jsonify(_serialize_entities(subraces))
    except Exception as e:
        return _handle_service_error("get subraces", e)


@d5e_bp.route("/backgrounds")
def get_backgrounds() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e backgrounds."""
    try:
        service = get_d5e_service()
        backgrounds = service._hub.backgrounds.list_all()
        return jsonify(_serialize_entities(backgrounds))
    except Exception as e:
        return _handle_service_error("get backgrounds", e)


@d5e_bp.route("/backgrounds/<string:index>")
def get_background(index: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific background by index."""
    try:
        service = get_d5e_service()
        background = service._hub.backgrounds.get_by_index(index)
        if not background:
            return jsonify({"error": "Background not found"}), 404
        return jsonify(_serialize_entity(background))
    except Exception as e:
        return _handle_service_error("get background", e)


@d5e_bp.route("/feats")
def get_feats() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e feats."""
    try:
        service = get_d5e_service()
        feats = service._hub.feats.list_all()
        return jsonify(_serialize_entities(feats))
    except Exception as e:
        return _handle_service_error("get feats", e)


@d5e_bp.route("/traits")
def get_traits() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e traits."""
    try:
        service = get_d5e_service()
        traits = service._hub.traits.list_all()
        return jsonify(_serialize_entities(traits))
    except Exception as e:
        return _handle_service_error("get traits", e)


# Character Progression Endpoints
@d5e_bp.route("/features")
def get_features() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e features."""
    try:
        service = get_d5e_service()
        features = service._hub.features.list_all()
        return jsonify(_serialize_entities(features))
    except Exception as e:
        return _handle_service_error("get features", e)


@d5e_bp.route("/levels")
def get_levels() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e level progression data."""
    try:
        service = get_d5e_service()
        levels = service._hub.levels.list_all()
        return jsonify(_serialize_entities(levels))
    except Exception as e:
        return _handle_service_error("get levels", e)


# Equipment & Items Endpoints
@d5e_bp.route("/equipment")
def get_equipment() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e equipment."""
    try:
        service = get_d5e_service()
        equipment = service._hub.equipment.list_all()
        return jsonify(_serialize_entities(equipment))
    except Exception as e:
        return _handle_service_error("get equipment", e)


@d5e_bp.route("/equipment/<string:index>")
def get_equipment_item(index: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific equipment item by index."""
    try:
        service = get_d5e_service()
        equipment = service._hub.equipment.get_by_index(index)
        if not equipment:
            return jsonify({"error": "Equipment not found"}), 404
        return jsonify(_serialize_entity(equipment))
    except Exception as e:
        return _handle_service_error("get equipment item", e)


@d5e_bp.route("/equipment-categories")
def get_equipment_categories() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e equipment categories."""
    try:
        service = get_d5e_service()
        categories = service._hub.equipment_categories.list_all()
        return jsonify(_serialize_entities(categories))
    except Exception as e:
        return _handle_service_error("get equipment categories", e)


@d5e_bp.route("/magic-items")
def get_magic_items() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e magic items."""
    try:
        service = get_d5e_service()
        magic_items = service._hub.magic_items.list_all()
        return jsonify(_serialize_entities(magic_items))
    except Exception as e:
        return _handle_service_error("get magic items", e)


@d5e_bp.route("/weapon-properties")
def get_weapon_properties() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e weapon properties."""
    try:
        service = get_d5e_service()
        properties = service._hub.weapon_properties.list_all()
        return jsonify(_serialize_entities(properties))
    except Exception as e:
        return _handle_service_error("get weapon properties", e)


@d5e_bp.route("/magic-schools")
def get_magic_schools() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e schools of magic."""
    try:
        service = get_d5e_service()
        schools = service._hub.magic_schools.list_all()
        return jsonify(_serialize_entities(schools))
    except Exception as e:
        return _handle_service_error("get magic schools", e)


# Spells & Monsters Endpoints
@d5e_bp.route("/spells")
def get_spells() -> Union[Response, Tuple[Response, int]]:
    """Get D&D 5e spells with optional filtering."""
    try:
        service = get_d5e_service()

        # Get filter parameters
        class_name = request.args.get("class_name")
        spell_level = request.args.get("level", type=int)
        school = request.args.get("school")

        # Validate parameters
        if spell_level is not None and (spell_level < 0 or spell_level > 9):
            return jsonify({"error": "Spell level must be between 0 and 9"}), 400

        if class_name:
            # Validate class name exists
            class_data = service._hub.classes.get_by_name(class_name)
            if not class_data:
                return jsonify({"error": f"Unknown class: {class_name}"}), 400
            # Filter by class and optionally by level
            spells = cast(
                List[Any], service.get_spells_for_class(class_name, spell_level)
            )
        elif spell_level is not None:
            # Filter by level only
            spells = cast(List[Any], service._hub.spells.get_by_level(spell_level))
        elif school:
            # Validate school exists
            school_data = service._hub.magic_schools.get_by_index(school)
            if not school_data:
                return jsonify({"error": f"Unknown magic school: {school}"}), 400
            # Filter by school
            spells = cast(List[Any], service._hub.spells.get_by_school(school))
        else:
            # Get all spells
            spells = cast(List[Any], service._hub.spells.list_all())

        return jsonify(_serialize_entities(spells))
    except Exception as e:
        return _handle_service_error("get spells", e)


@d5e_bp.route("/spells/<string:index>")
def get_spell(index: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific spell by index."""
    try:
        service = get_d5e_service()
        spell = service._hub.spells.get_by_index(index)
        if not spell:
            return jsonify({"error": "Spell not found"}), 404
        return jsonify(_serialize_entity(spell))
    except Exception as e:
        return _handle_service_error("get spell", e)


@d5e_bp.route("/monsters")
def get_monsters() -> Union[Response, Tuple[Response, int]]:
    """Get D&D 5e monsters with optional filtering."""
    try:
        service = get_d5e_service()

        # Get filter parameters
        min_cr = request.args.get("min_cr", type=float)
        max_cr = request.args.get("max_cr", type=float)
        monster_type = request.args.get("type")
        size = request.args.get("size")

        # Validate CR range
        if min_cr is not None and min_cr < 0:
            return jsonify({"error": "Minimum CR must be non-negative"}), 400
        if max_cr is not None and max_cr < 0:
            return jsonify({"error": "Maximum CR must be non-negative"}), 400
        if min_cr is not None and max_cr is not None and min_cr > max_cr:
            return jsonify(
                {"error": "Minimum CR cannot be greater than maximum CR"}
            ), 400

        # Validate size parameter
        if size is not None:
            valid_sizes = ["tiny", "small", "medium", "large", "huge", "gargantuan"]
            if size.lower() not in valid_sizes:
                return jsonify(
                    {
                        "error": f"Invalid size '{size}'. Valid sizes: {', '.join(valid_sizes)}"
                    }
                ), 400

        if min_cr is not None and max_cr is not None:
            # Filter by CR range
            monsters = cast(List[Any], service.get_monsters_by_cr(min_cr, max_cr))
        elif monster_type:
            # Filter by type
            monsters = cast(List[Any], service._hub.monsters.get_by_type(monster_type))
        elif size:
            # Filter by size
            monsters = cast(List[Any], service._hub.monsters.get_by_size(size))
        else:
            # Get all monsters
            monsters = cast(List[Any], service._hub.monsters.list_all())

        return jsonify(_serialize_entities(monsters))
    except Exception as e:
        return _handle_service_error("get monsters", e)


@d5e_bp.route("/monsters/<string:index>")
def get_monster(index: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific monster by index."""
    try:
        service = get_d5e_service()
        monster = service._hub.monsters.get_by_index(index)
        if not monster:
            return jsonify({"error": "Monster not found"}), 404
        return jsonify(_serialize_entity(monster))
    except Exception as e:
        return _handle_service_error("get monster", e)


# Rules Endpoints
@d5e_bp.route("/rules")
def get_rules() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e rules."""
    try:
        service = get_d5e_service()
        rules = service._hub.rules.list_all()
        return jsonify(_serialize_entities(rules))
    except Exception as e:
        return _handle_service_error("get rules", e)


@d5e_bp.route("/rule-sections")
def get_rule_sections() -> Union[Response, Tuple[Response, int]]:
    """Get all D&D 5e rule sections."""
    try:
        service = get_d5e_service()
        rule_sections = service._hub.rule_sections.list_all()
        return jsonify(_serialize_entities(rule_sections))
    except Exception as e:
        return _handle_service_error("get rule sections", e)


@d5e_bp.route("/rule-sections/<string:section>/text")
def get_rule_section_text(section: str) -> Union[Response, Tuple[Response, int]]:
    """Get formatted rule text for a specific section."""
    try:
        service = get_d5e_service()
        rule_text = service.get_rule_section(section)
        if not rule_text:
            return jsonify({"error": "Rule section not found"}), 404
        return jsonify({"section": section, "text": rule_text})
    except Exception as e:
        return _handle_service_error("get rule section text", e)


# Advanced Endpoints
@d5e_bp.route("/search")
def search_all_content() -> Union[Response, Tuple[Response, int]]:
    """Search across all D&D 5e content."""
    try:
        query = request.args.get("q")
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400

        categories_raw = request.args.getlist("categories")
        categories: Optional[List[str]] = categories_raw if categories_raw else None

        service = get_d5e_service()
        results = service.search_all_content(query, categories)

        # Serialize results
        serialized_results = {}
        for category, entities in results.items():
            serialized_results[category] = _serialize_entities(entities)

        return jsonify(
            {"query": query, "categories": categories, "results": serialized_results}
        )
    except Exception as e:
        return _handle_service_error("search content", e)


@d5e_bp.route("/character-options")
def get_character_options() -> Union[Response, Tuple[Response, int]]:
    """Get combined character creation data."""
    try:
        service = get_d5e_service()

        character_options = {
            "races": _serialize_entities(service._hub.races.list_all()),
            "classes": _serialize_entities(service._hub.classes.list_all()),
            "backgrounds": _serialize_entities(service._hub.backgrounds.list_all()),
            "ability_scores": _serialize_entities(
                service._hub.ability_scores.list_all()
            ),
            "skills": _serialize_entities(service._hub.skills.list_all()),
            "languages": _serialize_entities(service.get_languages()),
        }

        return jsonify(character_options)
    except Exception as e:
        return _handle_service_error("get character options", e)


@d5e_bp.route("/starting-equipment")
def get_starting_equipment() -> Union[Response, Tuple[Response, int]]:
    """Get starting equipment for a class and background combination."""
    try:
        class_name = request.args.get("class_name")
        background_name = request.args.get("background")

        if not class_name or not background_name:
            return jsonify(
                {"error": "Both 'class_name' and 'background' parameters are required"}
            ), 400

        service = get_d5e_service()
        equipment = service.get_starting_equipment(class_name, background_name)

        return jsonify(
            {
                "class_name": class_name,
                "background": background_name,
                "equipment": {
                    "class": _serialize_entities(equipment["class_"]),
                    "background": _serialize_entities(equipment["background"]),
                },
            }
        )
    except Exception as e:
        return _handle_service_error("get starting equipment", e)


@d5e_bp.route("/encounter-budget")
def get_encounter_budget() -> Union[Response, Tuple[Response, int]]:
    """Calculate encounter XP budget for a party."""
    try:
        # Parse party levels from comma-separated string
        levels_str = request.args.get("levels")
        difficulty = request.args.get("difficulty", "medium")

        if not levels_str:
            return jsonify({"error": "Parameter 'levels' is required"}), 400

        try:
            party_levels = [int(level.strip()) for level in levels_str.split(",")]
        except ValueError:
            return jsonify(
                {
                    "error": "Invalid levels format. Use comma-separated integers (e.g., '3,4,5,5')"
                }
            ), 400

        service = get_d5e_service()
        budget = service.get_encounter_xp_budget(party_levels, difficulty)

        return jsonify(
            {
                "party_levels": party_levels,
                "difficulty": difficulty,
                "xp_budget": budget,
            }
        )
    except Exception as e:
        return _handle_service_error("calculate encounter budget", e)


@d5e_bp.route("/content-statistics")
def get_content_statistics() -> Union[Response, Tuple[Response, int]]:
    """Get statistics about available D&D 5e content."""
    try:
        service = get_d5e_service()
        stats = service.get_content_statistics()
        return jsonify(stats)
    except Exception as e:
        return _handle_service_error("get content statistics", e)
