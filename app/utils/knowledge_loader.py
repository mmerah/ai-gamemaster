"""
Utility functions for loading knowledge data (lore, rulesets, etc.)
Replaces the minimal LoreRepository and RulesetRepository classes.
"""
import json
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


def load_lore_info(lore_id: str, index_file_path: str = "knowledge/lores.json") -> Optional[Dict]:
    """
    Load information about a specific lore entry.
    
    Args:
        lore_id: The ID of the lore to load
        index_file_path: Path to the lores index file
        
    Returns:
        Dict with lore information or None if not found
    """
    try:
        with open(index_file_path, "r", encoding="utf-8") as f:
            lores = json.load(f)
            
        for lore in lores:
            if lore.get("id") == lore_id:
                return lore
                
        logger.warning(f"Lore {lore_id} not found in {index_file_path}")
        return None
        
    except Exception as e:
        logger.error(f"Error loading lore info: {e}")
        return None


def load_all_lores(index_file_path: str = "knowledge/lores.json") -> List[Dict]:
    """
    Load all available lore entries.
    
    Args:
        index_file_path: Path to the lores index file
        
    Returns:
        List of lore dictionaries
    """
    try:
        with open(index_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading lores: {e}")
        return []


def load_ruleset_info(ruleset_id: str, index_file_path: str = "knowledge/rulesets.json") -> Optional[Dict]:
    """
    Load information about a specific ruleset.
    
    Args:
        ruleset_id: The ID of the ruleset to load
        index_file_path: Path to the rulesets index file
        
    Returns:
        Dict with ruleset information or None if not found
    """
    try:
        with open(index_file_path, "r", encoding="utf-8") as f:
            rulesets = json.load(f)
            
        for ruleset in rulesets:
            if ruleset.get("id") == ruleset_id:
                return ruleset
                
        logger.warning(f"Ruleset {ruleset_id} not found in {index_file_path}")
        return None
        
    except Exception as e:
        logger.error(f"Error loading ruleset info: {e}")
        return None


def load_all_rulesets(index_file_path: str = "knowledge/rulesets.json") -> List[Dict]:
    """
    Load all available rulesets.
    
    Args:
        index_file_path: Path to the rulesets index file
        
    Returns:
        List of ruleset dictionaries
    """
    try:
        with open(index_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading rulesets: {e}")
        return []