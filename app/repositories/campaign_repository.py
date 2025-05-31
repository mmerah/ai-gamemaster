"""
Campaign repository implementation for managing campaign data persistence.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import List, Optional
from app.game.models import CampaignDefinition, CampaignMetadata

logger = logging.getLogger(__name__)


class CampaignRepository:
    """Repository for managing campaign JSON files."""
    
    def __init__(self, campaigns_dir: str = "saves/campaigns"):
        self.campaigns_dir = campaigns_dir
        self.campaigns_index_file = os.path.join(campaigns_dir, "campaigns.json")
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the campaigns directory exists."""
        os.makedirs(self.campaigns_dir, exist_ok=True)
    
    def get_all_campaigns(self) -> List[CampaignMetadata]:
        """Get metadata for all available campaigns."""
        try:
            if not os.path.exists(self.campaigns_index_file):
                return []
            
            with open(self.campaigns_index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            campaigns = []
            for campaign_data in data.get("campaigns", []):
                try:
                    # Parse datetime strings with better handling
                    if "created_date" in campaign_data:
                        date_str = campaign_data["created_date"]
                        # Handle malformed dates with both timezone and Z
                        if '+00:00Z' in date_str:
                            date_str = date_str.replace('+00:00Z', '+00:00')
                        elif 'Z' in date_str and '+' not in date_str:
                            date_str = date_str.replace('Z', '+00:00')
                        campaign_data["created_date"] = datetime.fromisoformat(date_str)
                    if "last_played" in campaign_data and campaign_data["last_played"]:
                        date_str = campaign_data["last_played"]
                        # Handle malformed dates with both timezone and Z
                        if '+00:00Z' in date_str:
                            date_str = date_str.replace('+00:00Z', '+00:00')
                        elif 'Z' in date_str and '+' not in date_str:
                            date_str = date_str.replace('Z', '+00:00')
                        campaign_data["last_played"] = datetime.fromisoformat(date_str)
                    
                    campaigns.append(CampaignMetadata(**campaign_data))
                except Exception as e:
                    logger.error(f"Error parsing campaign metadata: {e}")
                    continue
            
            return campaigns
            
        except Exception as e:
            logger.error(f"Error loading campaigns index: {e}")
            return []
    
    def get_campaign(self, campaign_id: str) -> Optional[CampaignDefinition]:
        """Load a specific campaign definition."""
        try:
            campaigns = self.get_all_campaigns()
            campaign_meta = next((c for c in campaigns if c.id == campaign_id), None)
            
            if not campaign_meta:
                logger.warning(f"Campaign {campaign_id} not found in index")
                return None
            
            campaign_file = os.path.join(self.campaigns_dir, campaign_meta.folder, "campaign.json")
            
            if not os.path.exists(campaign_file):
                logger.error(f"Campaign file not found: {campaign_file}")
                return None
            
            with open(campaign_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse datetime strings with better handling
            if "created_date" in data:
                date_str = data["created_date"]
                # Handle malformed dates with both timezone and Z
                if '+00:00Z' in date_str:
                    date_str = date_str.replace('+00:00Z', '+00:00')
                elif 'Z' in date_str and '+' not in date_str:
                    date_str = date_str.replace('Z', '+00:00')
                data["created_date"] = datetime.fromisoformat(date_str)
            if "last_played" in data and data["last_played"]:
                date_str = data["last_played"]
                # Handle malformed dates with both timezone and Z
                if '+00:00Z' in date_str:
                    date_str = date_str.replace('+00:00Z', '+00:00')
                elif 'Z' in date_str and '+' not in date_str:
                    date_str = date_str.replace('Z', '+00:00')
                data["last_played"] = datetime.fromisoformat(date_str)
            
            return CampaignDefinition(**data)
            
        except Exception as e:
            logger.error(f"Error loading campaign {campaign_id}: {e}")
            return None
    
    def save_campaign(self, campaign: CampaignDefinition) -> bool:
        """Save a campaign definition."""
        try:
            # Create campaign directory
            campaign_dir = os.path.join(self.campaigns_dir, campaign.id)
            os.makedirs(campaign_dir, exist_ok=True)
            
            # Save campaign definition
            campaign_file = os.path.join(campaign_dir, "campaign.json")
            campaign_data = campaign.model_dump()
            
            # Convert datetime objects to ISO strings (timezone-aware format)
            if "created_date" in campaign_data:
                campaign_data["created_date"] = campaign.created_date.isoformat()
            if "last_played" in campaign_data and campaign_data["last_played"]:
                campaign_data["last_played"] = campaign.last_played.isoformat()
            
            with open(campaign_file, 'w', encoding='utf-8') as f:
                json.dump(campaign_data, f, indent=2, ensure_ascii=False)
            
            # Update campaigns index
            self._update_campaigns_index(campaign)
            
            logger.info(f"Campaign {campaign.id} saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving campaign {campaign.id}: {e}")
            return False
    
    def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign and its files."""
        try:
            campaigns = self.get_all_campaigns()
            campaign_meta = next((c for c in campaigns if c.id == campaign_id), None)
            
            if not campaign_meta:
                logger.warning(f"Campaign {campaign_id} not found")
                return False
            
            # Remove campaign directory
            campaign_dir = os.path.join(self.campaigns_dir, campaign_meta.folder)
            if os.path.exists(campaign_dir):
                import shutil
                shutil.rmtree(campaign_dir)
            
            # Update campaigns index
            updated_campaigns = [c for c in campaigns if c.id != campaign_id]
            self._save_campaigns_index(updated_campaigns)
            
            logger.info(f"Campaign {campaign_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting campaign {campaign_id}: {e}")
            return False
    
    def update_last_played(self, campaign_id: str) -> None:
        """Update the last played timestamp for a campaign."""
        try:
            campaigns = self.get_all_campaigns()
            for campaign in campaigns:
                if campaign.id == campaign_id:
                    campaign.last_played = datetime.now(timezone.utc)
                    break
            
            self._save_campaigns_index(campaigns)
            
        except Exception as e:
            logger.error(f"Error updating last played for campaign {campaign_id}: {e}")
    
    def _update_campaigns_index(self, campaign: CampaignDefinition) -> None:
        """Update the campaigns index with new or updated campaign."""
        campaigns = self.get_all_campaigns()
        
        # Create metadata from campaign definition
        metadata = CampaignMetadata(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            created_date=campaign.created_date,
            last_played=campaign.last_played,
            starting_level=campaign.starting_level,
            difficulty=campaign.difficulty,
            party_size=len(campaign.party_character_ids),
            folder=campaign.id,
            thumbnail=None
        )
        
        # Replace existing or add new
        updated_campaigns = [c for c in campaigns if c.id != campaign.id]
        updated_campaigns.append(metadata)
        
        self._save_campaigns_index(updated_campaigns)
    
    def _save_campaigns_index(self, campaigns: List[CampaignMetadata]) -> None:
        """Save the campaigns index file."""
        try:
            index_data = {
                "version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "campaigns": []
            }
            
            for campaign in campaigns:
                campaign_data = campaign.model_dump()
                # Convert datetime objects to ISO strings (timezone-aware format)
                if "created_date" in campaign_data:
                    campaign_data["created_date"] = campaign.created_date.isoformat()
                if "last_played" in campaign_data and campaign_data["last_played"]:
                    campaign_data["last_played"] = campaign.last_played.isoformat()
                
                index_data["campaigns"].append(campaign_data)
            
            with open(self.campaigns_index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving campaigns index: {e}")
