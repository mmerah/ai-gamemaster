"""
In-memory implementation of campaign instance repository for testing.
"""
import json
import os
import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone
from app.game.unified_models import CampaignInstanceModel

logger = logging.getLogger(__name__)


class InMemoryCampaignInstanceRepository:
    """In-memory repository for managing campaign instance metadata."""
    
    def __init__(self, base_dir: str = "saves/campaigns"):
        self._instances: Dict[str, CampaignInstanceModel] = {}
        self.base_dir = base_dir
        self.instances_file = os.path.join(base_dir, "instances.json")
        # Load existing instances from file system for read-only access
        self._load_from_file()
    
    def get_all_instances(self) -> List[CampaignInstanceModel]:
        """Get all campaign instances."""
        return list(self._instances.values())
    
    def get_instance(self, instance_id: str) -> Optional[CampaignInstanceModel]:
        """Get a specific campaign instance by ID."""
        return self._instances.get(instance_id)
    
    def create_instance(self, instance: CampaignInstanceModel) -> bool:
        """Create a new campaign instance."""
        if instance.id in self._instances:
            logger.error(f"Campaign instance {instance.id} already exists")
            return False
        
        self._instances[instance.id] = instance
        return True
    
    def update_instance(self, instance: CampaignInstanceModel) -> bool:
        """Update an existing campaign instance."""
        if instance.id not in self._instances:
            logger.error(f"Campaign instance {instance.id} not found")
            return False
        
        # Update last_played timestamp
        instance.last_played = datetime.now(timezone.utc)
        self._instances[instance.id] = instance
        return True
    
    def delete_instance(self, instance_id: str) -> bool:
        """Delete a campaign instance."""
        if instance_id not in self._instances:
            logger.error(f"Campaign instance {instance_id} not found")
            return False
        
        del self._instances[instance_id]
        return True
    
    def get_instances_by_template(self, template_id: str) -> List[CampaignInstanceModel]:
        """Get all instances created from a specific template."""
        return [
            instance for instance in self._instances.values()
            if instance.template_id == template_id
        ]
    
    def get_instances_with_character(self, character_template_id: str) -> List[CampaignInstanceModel]:
        """Get all instances that include a specific character template."""
        return [
            instance for instance in self._instances.values()
            if character_template_id in instance.character_ids
        ]
    
    def _load_from_file(self):
        """Load existing instances from file system for read-only access."""
        if not os.path.exists(self.instances_file):
            logger.info("No instances.json file found, starting with empty repository")
            return
        
        try:
            with open(self.instances_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for instance_id, instance_data in data.items():
                try:
                    self._instances[instance_id] = CampaignInstanceModel(**instance_data)
                    logger.info(f"Loaded campaign instance {instance_id} into memory")
                except Exception as e:
                    logger.error(f"Error loading campaign instance {instance_id}: {e}")
            
            logger.info(f"Loaded {len(self._instances)} campaign instances from file")
        except Exception as e:
            logger.error(f"Error loading campaign instances from file: {e}")