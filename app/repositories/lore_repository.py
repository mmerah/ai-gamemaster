import json
from typing import Optional, Dict, List

class LoreRepository:
    def __init__(self, index_file_path: str = "knowledge/lores.json"):
        self.index_file_path = index_file_path
        self._lores = self._load_index()

    def _load_index(self) -> List[Dict]:
        try:
            with open(self.index_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def get_lore_info(self, lore_id: str) -> Optional[Dict]:
        for lore in self._lores:
            if lore.get("id") == lore_id:
                return lore
        return None

    def get_all_lores_info(self) -> List[Dict]:
        return self._lores.copy()
