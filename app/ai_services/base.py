import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .schemas import AIResponse

logger = logging.getLogger(__name__)


class BaseAIService(ABC):
    @abstractmethod
    def get_response(self, messages: List[Dict[str, str]]) -> Optional[AIResponse]:
        """
        Sends messages to the AI and returns the parsed Pydantic response model.

        Args:
            messages (list[Any]): A list of message dictionaries conforming to the API standard.

        Returns:
            AIResponse | None: The parsed Pydantic model or None if an error occurred.
        """
        pass
