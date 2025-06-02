"""
Repository for managing campaign instance metadata.

Campaign instances are active/saved games created from campaign templates.
This repository manages the metadata about these instances, while the actual
game state is managed by GameStateRepository.
"""
import json
import os
import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone
from app.game.unified_models import CampaignInstanceModel

logger = logging.getLogger(__name__)


class CampaignInstanceRepository:
    """Repository for managing campaign instance metadata."""
    
    def __init__(self, base_dir: str = "saves/campaigns"):
        self.base_dir = base_dir
        self.instances_file = os.path.join(base_dir, "instances.json")
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self):
        """Ensure the campaigns directory exists."""
        os.makedirs(self.base_dir, exist_ok=True)
    
    def _load_instances(self) -> Dict[str, CampaignInstanceModel]:
        """Load all campaign instances from the instances file."""
        if not os.path.exists(self.instances_file):
            return {}
        
        try:
            with open(self.instances_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            instances = {}
            for instance_id, instance_data in data.items():
                try:
                    instances[instance_id] = CampaignInstanceModel(**instance_data)
                except Exception as e:
                    logger.error(f"Error loading campaign instance {instance_id}: {e}")
            
            return instances
        except Exception as e:
            logger.error(f"Error loading campaign instances: {e}")
            return {}
    
    def _save_instances(self, instances: Dict[str, CampaignInstanceModel]) -> bool:
        """Save all campaign instances to the instances file."""
        try:
            # Convert to serializable format
            data = {
                instance_id: instance.model_dump(mode='json')
                for instance_id, instance in instances.items()
            }
            
            # Write to file
            with open(self.instances_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logger.error(f"Error saving campaign instances: {e}")
            return False
    
    def get_all_instances(self) -> List[CampaignInstanceModel]:
        """Get all campaign instances."""
        instances = self._load_instances()
        return list(instances.values())
    
    def get_instance(self, instance_id: str) -> Optional[CampaignInstanceModel]:
        """Get a specific campaign instance by ID."""
        instances = self._load_instances()
        return instances.get(instance_id)
    
    def create_instance(self, instance: CampaignInstanceModel) -> bool:
        """Create a new campaign instance."""
        instances = self._load_instances()
        
        if instance.id in instances:
            logger.error(f"Campaign instance {instance.id} already exists")
            return False
        
        instances[instance.id] = instance
        return self._save_instances(instances)
    
    def update_instance(self, instance: CampaignInstanceModel) -> bool:
        """Update an existing campaign instance."""
        instances = self._load_instances()
        
        if instance.id not in instances:
            logger.error(f"Campaign instance {instance.id} not found")
            return False
        
        # Update last_played timestamp
        instance.last_played = datetime.now(timezone.utc)
        instances[instance.id] = instance
        
        return self._save_instances(instances)
    
    def delete_instance(self, instance_id: str) -> bool:
        """Delete a campaign instance."""
        instances = self._load_instances()
        
        if instance_id not in instances:
            logger.error(f"Campaign instance {instance_id} not found")
            return False
        
        del instances[instance_id]
        
        # Also delete the campaign directory if it exists
        campaign_dir = os.path.join(self.base_dir, instance_id)
        if os.path.exists(campaign_dir):
            try:
                import shutil
                shutil.rmtree(campaign_dir)
            except Exception as e:
                logger.error(f"Error deleting campaign directory {campaign_dir}: {e}")
        
        return self._save_instances(instances)
    
    def get_instances_by_template(self, template_id: str) -> List[CampaignInstanceModel]:
        """Get all instances created from a specific template."""
        instances = self._load_instances()
        return [
            instance for instance in instances.values()
            if instance.template_id == template_id
        ]
    
    def get_active_instances(self, days: int = 30) -> List[CampaignInstanceModel]:
        """Get instances that have been played recently."""
        from datetime import timedelta
        
        instances = self._load_instances()
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        return [
            instance for instance in instances.values()
            if instance.last_played and instance.last_played > cutoff_date
        ]