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
        
    def _clean_json_string(self, json_str: str) -> str:
        """
        Clean common JSON formatting issues before parsing.
        """
        cleaned = json_str.strip()
        
        # Fix trailing commas in arrays and objects
        # This regex finds trailing commas before closing brackets/braces
        import re
        
        # Remove trailing commas before closing array brackets
        cleaned = re.sub(r',\s*]', ']', cleaned)
        
        # Remove trailing commas before closing object braces
        cleaned = re.sub(r',\s*}', '}', cleaned)
        
        # Remove trailing commas before closing brackets/braces with whitespace/newlines
        cleaned = re.sub(r',\s*\n\s*]', '\n]', cleaned)
        cleaned = re.sub(r',\s*\n\s*}', '\n}', cleaned)
        
        # Fix common escaping issues in strings
        # Handle unescaped quotes in string values (basic case)
        # This is a simple fix - more complex cases would need a proper JSON parser
        
        # Remove any trailing commas at the very end of arrays/objects
        cleaned = re.sub(r',(\s*[}\]])$', r'\1', cleaned, flags=re.MULTILINE)
        
        logger.debug(f"JSON cleaning applied: {len(json_str)} -> {len(cleaned)} chars")
        if json_str != cleaned:
            logger.debug(f"JSON changes made during cleaning")
        
        return cleaned
    
    def _extract_json_flexible(self, raw_content: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Attempts to extract a JSON object from raw text.
        Enhanced with JSON cleaning for better reliability.
        Returns the parsed JSON dictionary and any surrounding text, or (None, raw_content) on failure.
        """
        # Remove leading/trailing whitespace
        content = raw_content.strip()
        
        # Strategy 1: Try parsing the entire content as JSON (pure JSON response)
        try:
            cleaned_content = self._clean_json_string(content)
            parsed_json = json.loads(cleaned_content)
            logger.debug("Successfully parsed entire content as JSON after cleaning.")
            return parsed_json, ""
        except json.JSONDecodeError:
            # Try without cleaning as fallback
            try:
                parsed_json = json.loads(content)
                logger.debug("Successfully parsed entire content as JSON without cleaning.")
                return parsed_json, ""
            except json.JSONDecodeError:
                pass
        
        # Strategy 2: Look for JSON in markdown code blocks
        match = JSON_BLOCK_REGEX.search(content)
        if match:
            json_str = match.group(1)
            try:
                cleaned_json = self._clean_json_string(json_str)
                parsed_json = json.loads(cleaned_json)
                prefix = content[:match.start()].strip()
                suffix = content[match.end():].strip()
                surrounding_text = ""
                if prefix: surrounding_text += prefix
                if suffix:
                    if surrounding_text: surrounding_text += "\n" + suffix
                    else: surrounding_text += suffix
                logger.debug("Successfully extracted JSON from markdown code block after cleaning.")
                return parsed_json, surrounding_text.strip()
            except json.JSONDecodeError:
                # Try without cleaning as fallback
                try:
                    parsed_json = json.loads(json_str)
                    prefix = content[:match.start()].strip()
                    suffix = content[match.end():].strip()
                    surrounding_text = ""
                    if prefix: surrounding_text += prefix
                    if suffix:
                        if surrounding_text: surrounding_text += "\n" + suffix
                        else: surrounding_text += suffix
                    logger.debug("Successfully extracted JSON from markdown code block without cleaning.")
                    return parsed_json, surrounding_text.strip()
                except json.JSONDecodeError as e:
                    logger.warning(f"Found JSON block but failed to parse even after cleaning: {e}")
        
        # Strategy 3: Find the largest JSON object by looking for balanced braces
        # Start from the first '{' and find the matching '}'
        first_brace = content.find('{')
        if first_brace == -1:
            logger.warning("No opening brace found in content.")
            return None, content
        
        # Find the matching closing brace
        brace_count = 0
        end_pos = -1
        for i in range(first_brace, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i
                    break
        
        if end_pos == -1:
            logger.warning("No matching closing brace found.")
            return None, content
        
        # Extract and try to parse the JSON string
        json_str = content[first_brace:end_pos + 1]
        try:
            cleaned_json = self._clean_json_string(json_str)
            parsed_json = json.loads(cleaned_json)
            prefix = content[:first_brace].strip()
            suffix = content[end_pos + 1:].strip()
            surrounding_text = ""
            if prefix: surrounding_text += prefix
            if suffix:
                if surrounding_text: surrounding_text += "\n" + suffix
                else: surrounding_text += suffix
            logger.debug("Successfully extracted JSON using balanced brace matching after cleaning.")
            return parsed_json, surrounding_text.strip()
        except json.JSONDecodeError:
            # Try without cleaning as fallback
            try:
                parsed_json = json.loads(json_str)
                prefix = content[:first_brace].strip()
                suffix = content[end_pos + 1:].strip()
                surrounding_text = ""
                if prefix: surrounding_text += prefix
                if suffix:
                    if surrounding_text: surrounding_text += "\n" + suffix
                    else: surrounding_text += suffix
                logger.debug("Successfully extracted JSON using balanced brace matching without cleaning.")
                return parsed_json, surrounding_text.strip()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse extracted JSON string even after cleaning: {e}")
                logger.debug(f"Problematic JSON string for parsing: {json_str}")
                logger.debug(f"Cleaned JSON string: {self._clean_json_string(json_str)}")
                return None, content
    
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
        
        # Log request summary only
        logger.info(f"Sending AI request: {len(messages)} messages to {self.model_name}")

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
                            logger.debug(f"Text surrounding the parsed JSON: {len(surrounding_text)} chars")
                        logger.debug("Validated AIResponse object (Flexible Mode)")
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
