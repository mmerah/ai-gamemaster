import re
import instructor
import openai
import logging
import json
from typing import List, Dict, Optional, Tuple
from instructor import Mode
from pydantic import ValidationError
from .base import BaseAIService
from .schemas import AIResponse

logger = logging.getLogger(__name__)

# Regex to find JSON block, possibly within markdown code fences
# Handles optional 'json' language tag and potential whitespace
JSON_BLOCK_REGEX = re.compile(r'```(?:json)?\s*(\{.*?\})\s*```', re.DOTALL)

class OpenAIService(BaseAIService):
    """
    AI service interacting with OpenAI-compatible APIs using the instructor library.
    Supports 'strict' (instructor JSON mode) and 'flexible' (extract JSON from text) parsing.
    """
    def __init__(self, api_key: Optional[str], base_url: Optional[str], model_name: str, parsing_mode: str = 'strict'):
        if not base_url:
            logger.warning("OpenAIService initialized without a base_url. Using default OpenAI API.")

        self.model_name = model_name
        self.parsing_mode = parsing_mode
        self.api_key = api_key
        self.base_url = base_url
        try:
            # Handle cases where API key might be None (e.g., local llama.cpp server)
            if api_key:
                self.base_client = openai.OpenAI(api_key=api_key, base_url=base_url)
            else:
                logger.info("Initializing OpenAI client without API key (for local server).")
                self.base_client = openai.OpenAI(api_key="nokey", base_url=base_url)

            # Initialize instructor-patched client ONLY if needed for strict mode
            self.instructor_client = None
            if self.parsing_mode == 'strict':
                self.instructor_client = instructor.patch(
                    client=self.base_client,
                    mode=Mode.JSON # Use JSON mode for strict enforcement
                )
                logger.info(f"OpenAIService Initialized (Strict Mode). Model: {self.model_name}, Base URL: {base_url or 'Default OpenAI'}, Mode: {Mode.JSON}")
            else:
                logger.info(f"OpenAIService Initialized (Flexible Mode). Model: {self.model_name}, Base URL: {base_url or 'Default OpenAI'}")

        except Exception as e:
            logger.critical(f"Failed to initialize OpenAI client for Instructor: {e}", exc_info=True)
            raise ConnectionError(f"Could not initialize OpenAI client: {e}") from e
        
    def _extract_json_flexible(self, raw_content: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Attempts to extract a JSON object from raw text, possibly within markdown fences.
        Returns the parsed JSON dictionary and any surrounding text, or (None, raw_content) on failure.
        """
        json_str = None
        prefix = ""
        suffix = ""

        # 1. Try finding JSON within ```json ... ``` or ``` ... ```
        match = JSON_BLOCK_REGEX.search(raw_content)
        if match:
            json_str = match.group(1)
            prefix = raw_content[:match.start()].strip()
            suffix = raw_content[match.end():].strip()
            logger.debug("Extracted JSON from markdown code block.")
        else:
            # 2. If no code block, find the first '{' and last '}'
            first_brace = raw_content.find('{')
            last_brace = raw_content.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = raw_content[first_brace : last_brace + 1]
                prefix = raw_content[:first_brace].strip()
                suffix = raw_content[last_brace + 1:].strip()
                logger.debug("Extracted JSON by finding first '{' and last '}'.")
            else:
                # No JSON structure found
                logger.warning("Could not find JSON structure ('{}' or ```json```) in flexible mode response.")
                return None, raw_content # Return original content as suffix

        if json_str:
            try:
                parsed_json = json.loads(json_str)
                surrounding_text = f"{prefix}\n{suffix}".strip()
                return parsed_json, surrounding_text
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse extracted JSON string in flexible mode: {e}")
                logger.debug(f"Problematic JSON string: {json_str}")
                # Return None for JSON, include original content as surrounding text
                return None, raw_content
        else:
            # Should have been caught above, but safety check
            return None, raw_content
    
    def get_response(self, messages: List[Dict[str, str]]) -> Optional[AIResponse]:
        """
        Sends messages to the AI and returns the parsed Pydantic response model.
        Handles both 'strict' and 'flexible' parsing modes.

        Args:
            messages (list): A list of message dictionaries conforming to the API standard.

        Returns:
            AIResponse | None: The parsed Pydantic model or None if an error occurred.
        """
        if not self.base_client:
            logger.error("OpenAIService base client not initialized.")
            return None
        
        # Log the request payload (if DEBUG enabled)
        if logger.isEnabledFor(logging.DEBUG):
            try:
                log_payload = json.dumps(messages, indent=2)
                if len(log_payload) > 5000: # Limit log size
                    log_payload = log_payload[:5000] + "\n... (truncated)"
                logger.debug(f"Sending request payload to AI ({self.model_name}):\n{log_payload}")
            except Exception as log_e:
                logger.warning(f"Could not serialize messages for logging: {log_e}")

        try:
            if self.parsing_mode == 'strict':
                # Strict Mode (Using Instructor JSON Mode)
                if not self.instructor_client:
                    logger.error("Instructor client not available for strict mode.")
                    return None
                logger.info(f"Sending request to {self.model_name} via Instructor (Strict Mode)...")
                response: AIResponse = self.instructor_client.chat.completions.create(
                    model=self.model_name,
                    response_model=AIResponse,
                    messages=messages,
                    max_retries=1,
                    temperature=0.6,
                    max_completion_tokens=4096
                )
                logger.info("Successfully received and validated structured response (Strict Mode).")
                logger.debug(f"Parsed AIResponse object: {response.model_dump_json(indent=2)}")
                return response
            
            else:
                # Flexible Mode (Manual Extraction + Validation)
                logger.info(f"Sending request to {self.model_name} (Flexible Mode)...")
                completion = self.base_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.6,
                    max_completion_tokens=4096
                )
                raw_content = completion.choices[0].message.content
                logger.debug(f"Received raw response content (Flexible Mode):\n{raw_content}")

                # Extract JSON and surrounding text
                parsed_json, surrounding_text = self._extract_json_flexible(raw_content)
                if parsed_json:
                    try:
                        # Validate the extracted JSON using Pydantic directly
                        validated_response = AIResponse.model_validate(parsed_json)
                        logger.info("Successfully extracted and validated JSON structure (Flexible Mode).")
                        if surrounding_text:
                            # Better not add this to the reasoning field, this can blow up token usage.
                            logger.debug(f"Text surrounding the parsed JSON:\n{surrounding_text}")
                        logger.debug(f"Validated AIResponse object (Flexible Mode): {validated_response.model_dump_json(indent=2)}")
                        return validated_response
                    except ValidationError as e:
                        logger.error(f"Pydantic validation failed for extracted JSON (Flexible Mode): {e}")
                        logger.debug(f"Invalid JSON data: {parsed_json}")
                        # Fallthrough
                    except Exception as e_val:
                        logger.error(f"Unexpected error during Pydantic validation (Flexible Mode): {e_val}", exc_info=True)
                        # Fallthrough
                else:
                    # Extraction failed, logged in _extract_json_flexible
                    logger.error("Failed to extract valid JSON from the response (Flexible Mode).")

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
            # Or general errors in Flexible Mode API call
            logger.error(f"Instructor/OpenAI Error in get_response: {e}", exc_info=True)

        return None