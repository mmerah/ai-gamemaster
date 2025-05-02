import instructor
import openai
import logging
import json
from typing import List, Dict, Optional, Tuple
from instructor import Mode
from .base import BaseAIService
from .schemas import AIResponse

logger = logging.getLogger(__name__)


class OpenAIService(BaseAIService):
    """
    AI service interacting with OpenAI-compatible APIs using the instructor library.
    """
    def __init__(self, api_key: Optional[str], base_url: Optional[str], model_name: str):
        if not base_url:
            logger.warning("OpenAIService initialized without a base_url. Using default OpenAI API.")

        self.model_name = model_name
        try:
            # Handle cases where API key might be None (e.g., local llama.cpp server)
            if api_key:
                base_client = openai.OpenAI(api_key=api_key, base_url=base_url)
            else:
                logger.info("Initializing OpenAI client without API key (for local server).")
                base_client = openai.OpenAI(api_key="nokey", base_url=base_url)

            # Apply instructor patch with MODE.TOOLS
            self.client = instructor.patch(
                client=base_client,
                mode=Mode.JSON
            )
            logger.info(f"OpenAIService Initialized. Model: {self.model_name}, Base URL: {base_url or 'Default OpenAI'}, Mode: {Mode.JSON}")

        except Exception as e:
            logger.critical(f"Failed to initialize OpenAI client for Instructor: {e}", exc_info=True)
            raise ConnectionError(f"Could not initialize OpenAI client: {e}") from e
        
    def get_response(self, messages: List[Dict[str, str]]) -> Optional[AIResponse]:
        """
        Sends messages to the AI and returns the parsed Pydantic response model.

        Args:
            messages (list): A list of message dictionaries conforming to the API standard.

        Returns:
            AIResponse | None: The parsed Pydantic model or None if an error occurred.
        """
        if not self.client:
            logger.error("OpenAIService client not initialized.")
            return None

        try:
            # Log the request payload (if DEBUG enabled)
            if logger.isEnabledFor(logging.DEBUG):
                try:
                    # Limit length for logging if necessary
                    log_payload = json.dumps(messages, indent=2)
                    if len(log_payload) > 5000: # Limit log size
                         log_payload = log_payload[:5000] + "\n... (truncated)"
                    logger.debug(f"Sending request payload to AI:\n{log_payload}")
                except Exception as log_e:
                    logger.warning(f"Could not serialize messages for logging: {log_e}")

            logger.info(f"Sending request to {self.model_name} via Instructor...")
            # Use instructor to get a validated Pydantic model back
            response: AIResponse = self.client.chat.completions.create(
                model=self.model_name,
                response_model=AIResponse,
                messages=messages,
                max_retries=1,
                temperature=0.15
            )
            logger.info("Successfully received and validated structured response.")
            logger.debug(f"Parsed AIResponse object: {response.model_dump_json(indent=2)}")

            return response

        except openai.APIConnectionError as e:
            logger.error(f"API Connection Error: {e}")
        except openai.RateLimitError as e:
            logger.error(f"API Rate Limit Error: {e}")
        except openai.APIStatusError as e:
            logger.error(f"API Status Error: Status={e.status_code}, Response={e.response}")
        except openai.APITimeoutError as e:
            logger.error(f"API Timeout Error: {e}")
        except Exception as e:
            # Includes validation errors from Instructor/Pydantic if retries fail
            logger.error(f"Instructor/OpenAI Error in get_response: {e}", exc_info=True)

        return None