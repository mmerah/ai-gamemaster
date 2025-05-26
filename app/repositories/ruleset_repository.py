import json
from typing import Optional, Dict, List

class RulesetRepository:
    def __init__(self, index_file_path: str = "knowledge/rulesets.json"):
        self.index_file_path = index_file_path
        self._rulesets = self._load_index()

    def _load_index(self) -> List[Dict]:
        try:
            with open(self.index_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def get_ruleset_info(self, ruleset_id: str) -> Optional[Dict]:
        for ruleset in self._rulesets:
            if ruleset.get("id") == ruleset_id:
                return ruleset
        return None

    def get_all_rulesets_info(self) -> List[Dict]:
        return self._rulesets.copy()
