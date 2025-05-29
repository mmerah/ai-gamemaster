"""
OpenAI-compatible AI service implementation using LangChain.
"""

import logging
import time
from typing import List, Dict, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

from app.ai_services.base import BaseAIService
from app.ai_services.schemas import AIResponse
from app.utils.message_converter import MessageConverter
from app.utils.robust_json_parser import RobustJsonOutputParser
from app.utils.token_monitor import CompletionTokenMonitor

logger = logging.getLogger(__name__)

# Suppress verbose DEBUG logging from the openai library's http client
logging.getLogger("openai._base_client").setLevel(logging.WARNING)

class OpenAIService(BaseAIService):
    """
    OpenAI-compatible AI service implementation using LangChain's ChatOpenAI client.
    Supports both strict (structured output) and flexible (JSON parsing) modes.
    """
    
    def __init__(
        self,
        api_key: Optional[str],
        base_url: Optional[str],
        model_name: str,
        parsing_mode: str = 'strict',
        temperature: float = 0.7
    ):
        """
        Initialize the AI service.
        
        Args:
            api_key: API key for the service (use "dummy" for local servers)
            base_url: Base URL for API calls (e.g., for local Llama.cpp)
            model_name: Name of the model to use
            parsing_mode: 'strict' for structured output, 'flexible' for JSON parsing
            temperature: Temperature for generation
        """
        self.model_name = model_name
        self.base_url = base_url
        self.parsing_mode = parsing_mode
        self.temperature = temperature
        
        # Initialize token monitor callback
        self.token_monitor = CompletionTokenMonitor()
        self.callbacks = [self.token_monitor]
        
        # Initialize ChatOpenAI client
        self.llm = ChatOpenAI(
            api_key=api_key or "dummy",  # Some providers need non-None
            base_url=base_url,
            model=model_name,
            temperature=temperature,
            callbacks=self.callbacks,
            max_retries=0,  # We handle retries ourselves
            request_timeout=60.0
        )
        
        # Initialize parser for flexible mode
        self.robust_parser = RobustJsonOutputParser(pydantic_object=AIResponse)
        
        logger.info(
            f"Initialized OpenAIService - Model: {model_name}, "
            f"Mode: {self.parsing_mode}, Temperature: {temperature}"
        )
    
    
    def get_response(self, messages: List[Dict[str, str]]) -> Optional[AIResponse]:
        """
        Send messages to the AI and return the parsed response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            Parsed AIResponse or None if all attempts fail
        """
        if not messages:
            logger.error("No messages provided to get_response")
            return None
        
        # Convert to LangChain format
        try:
            lc_messages = MessageConverter.to_langchain(messages)
        except ValueError as e:
            logger.error(f"Failed to convert messages to LangChain format: {e}")
            return None
        
        # Log request summary
        approx_tokens = sum(len(str(msg.get('content', '')).split()) * 1.3 for msg in messages)
        logger.info(
            f"Sending AI request: {len(messages)} messages (~{int(approx_tokens)} tokens) "
            f"to {self.model_name}"
        )
        
        # Retry logic with rate limit detection
        max_retries = 3
        retry_delay = 5.0
        
        for attempt in range(max_retries):
            try:
                # Reset token monitor for this attempt
                self.token_monitor.reset()
                
                response = self._get_response_attempt(lc_messages)
                if response:
                    return response
                
                # Check for rate limiting
                if self.token_monitor.last_completion_tokens == 0:
                    logger.warning(
                        f"Attempt {attempt + 1} detected rate limiting. "
                        f"Waiting {retry_delay} seconds before retry..."
                    )
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay = 10.0  # Increase delay for subsequent retries
                else:
                    logger.warning(f"Attempt {attempt + 1} returned empty response")
                    if attempt < max_retries - 1:
                        time.sleep(2.0)  # Short delay for non-rate-limit failures
                        
            except Exception as e:
                logger.error(f"Error in get_response attempt {attempt + 1}: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        logger.error(f"All {max_retries} attempts failed to get a valid response")
        return None
    
    def _get_response_attempt(self, messages: List[BaseMessage]) -> Optional[AIResponse]:
        """
        Single attempt to get response from the AI.
        
        Args:
            messages: List of LangChain message objects
            
        Returns:
            Parsed AIResponse or None if this attempt fails
        """
        try:
            if self.parsing_mode == 'strict':
                # Try structured output first
                return self._get_structured_response(messages)
            else:
                # Use flexible parsing mode
                return self._get_flexible_response(messages)
                
        except Exception as e:
            logger.error(f"Error in _get_response_attempt: {e}", exc_info=True)
            return None
    
    def _get_structured_response(self, messages: List[BaseMessage]) -> Optional[AIResponse]:
        """
        Get response using structured output (function calling).
        Falls back to flexible parsing if structured output fails.
        
        Args:
            messages: List of LangChain message objects
            
        Returns:
            Parsed AIResponse or None
        """
        try:
            logger.info(f"Sending request to {self.model_name} (Strict/Structured Mode)...")
            
            # Note: Removed OpenAI beta.parse optimization for simplicity
            
            # Try structured output with function calling
            try:
                structured_llm = self.llm.with_structured_output(
                    AIResponse,
                    method="function_calling",
                    include_raw=True
                )
                
                result = structured_llm.invoke(messages)
            except Exception as e:
                # Some models/providers don't support function calling (e.g., Gemini via OpenRouter)
                logger.warning(f"Function calling failed, trying JSON mode: {str(e)[:100]}")
                # Try with json_mode instead
                try:
                    structured_llm = self.llm.with_structured_output(
                        AIResponse,
                        method="json_mode",
                        include_raw=True
                    )
                    result = structured_llm.invoke(messages)
                except Exception as e2:
                    logger.warning(f"JSON mode also failed: {str(e2)[:100]}")
                    # Fall back to flexible parsing
                    return self._get_flexible_response(messages)
            
            # Check if we got a parsed result
            if isinstance(result, dict) and result.get("parsed"):
                logger.info("Successfully received structured response")
                return result["parsed"]
            
            # If no parsed result but we have raw, try flexible parsing
            if isinstance(result, dict) and result.get("raw"):
                logger.warning("Structured output failed, falling back to flexible parsing")
                raw = result["raw"]
                # Extract content from raw response
                if hasattr(raw, 'content'):
                    content = raw.content
                else:
                    content = str(raw)
                return self._parse_flexible(content)
            
            # If result is directly an AIResponse (some implementations might do this)
            if isinstance(result, AIResponse):
                logger.info("Successfully received structured response (direct)")
                return result
            
            logger.error(f"Unexpected result format from structured output: {type(result)}")
            
            # Last resort: try calling without structured output
            logger.warning("Falling back to flexible mode due to structured output issues")
            return self._get_flexible_response(messages)
            
        except NotImplementedError:
            # Some models don't support function calling
            logger.warning(
                f"Model {self.model_name} doesn't support structured output, "
                "falling back to flexible mode"
            )
            return self._get_flexible_response(messages)
        except Exception as e:
            logger.error(f"Structured output failed: {e}")
            # Fall back to flexible mode
            return self._get_flexible_response(messages)
    
    def _get_flexible_response(self, messages: List[BaseMessage]) -> Optional[AIResponse]:
        """
        Get response using flexible JSON parsing.
        
        Args:
            messages: List of LangChain message objects
            
        Returns:
            Parsed AIResponse or None
        """
        try:
            logger.info(f"Sending request to {self.model_name} (Flexible Mode)...")
            
            # Get raw response
            response = self.llm.invoke(messages)
            
            # Extract content
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            logger.debug(f"Received raw response content (Flexible Mode):\n{content}")
            
            # Check for empty response
            if not content or content.strip() == "":
                logger.warning("AI returned empty response content")
                return None
            
            # Parse using our robust parser
            return self._parse_flexible(content)
            
        except Exception as e:
            logger.error(f"Flexible mode error: {e}", exc_info=True)
            return None
    
    def _parse_flexible(self, content: str) -> Optional[AIResponse]:
        """
        Parse raw text content into AIResponse using robust JSON parser.
        
        Args:
            content: Raw text content from the AI
            
        Returns:
            Parsed AIResponse or None
        """
        try:
            # Use our robust parser with all fallback strategies
            parsed_dict = self.robust_parser.parse_with_fallbacks(content)
            
            # Validate with Pydantic
            validated_response = AIResponse.model_validate(parsed_dict)
            
            logger.info("Successfully extracted and validated JSON structure")
            logger.debug(f"Validated AIResponse: {validated_response.model_dump_json(indent=2)}")
            
            return validated_response
            
        except OutputParserException as e:
            logger.error(f"Failed to extract JSON from response: {e}")
            logger.debug(f"Raw content that failed to parse: {content[:500]}...")
            return None
        except ValidationError as e:
            logger.error(f"Pydantic validation failed: {e}")
            logger.debug(f"Invalid data: {parsed_dict if 'parsed_dict' in locals() else 'N/A'}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during parsing: {e}", exc_info=True)
            return None
    
