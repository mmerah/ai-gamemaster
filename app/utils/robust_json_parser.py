"""
Robust JSON output parser that combines LangChain's parser with fallback strategies.
This parser handles various edge cases found in real-world LLM outputs.
"""
# mypy: disable-error-code="name-defined"

import json
import logging
import re
from typing import Any, Dict, Optional, Tuple, Type

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Regex for JSON in markdown code blocks
JSON_BLOCK_REGEX = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)


class RobustJsonOutputParser(JsonOutputParser):
    """
    Enhanced JSON parser that combines LangChain's parser with additional fallback strategies.
    """

    def __init__(self, pydantic_object: Optional[Type[BaseModel]] = None):
        """
        Initialize the parser with an optional Pydantic model for validation.

        Args:
            pydantic_object: Optional Pydantic model class for validation
        """
        super().__init__(pydantic_object=pydantic_object)

    def parse_with_fallbacks(self, text: str) -> Dict[str, Any]:
        """
        Parse JSON with multiple fallback strategies.

        Args:
            text: Raw text potentially containing JSON

        Returns:
            Parsed JSON dictionary

        Raises:
            OutputParserException: If all parsing strategies fail
        """
        # Try standard LangChain parser first
        try:
            result = self.parse(text)
            # Convert Pydantic model to dict if needed
            if isinstance(result, BaseModel):
                return result.model_dump()
            return result  # type: ignore[no-any-return]
        except OutputParserException:
            logger.debug("Standard JSON parser failed, trying fallback strategies")
        except Exception as e:
            logger.debug(f"Unexpected error in standard parser: {e}")

        # Try our enhanced extraction strategies
        parsed_json, surrounding_text = self._extract_json_flexible(text)

        if parsed_json is not None:
            if surrounding_text:
                logger.debug(
                    f"Extracted JSON with surrounding text: {len(surrounding_text)} chars"
                )
            return parsed_json

        # All strategies failed
        raise OutputParserException(
            f"Failed to parse JSON from text. Tried multiple strategies. Text: {text[:200]}..."
        )

    def _clean_json_string(self, json_str: str) -> str:
        """
        Clean common JSON formatting issues before parsing.
        Ported from the existing implementation.
        """
        cleaned = json_str.strip()

        # Fix trailing commas in arrays and objects
        # Remove trailing commas before closing array brackets
        cleaned = re.sub(r",\s*]", "]", cleaned)

        # Remove trailing commas before closing object braces
        cleaned = re.sub(r",\s*}", "}", cleaned)

        # Remove trailing commas before closing brackets/braces with whitespace/newlines
        cleaned = re.sub(r",\s*\n\s*]", "\n]", cleaned)
        cleaned = re.sub(r",\s*\n\s*}", "\n}", cleaned)

        # Remove any trailing commas at the very end of arrays/objects
        cleaned = re.sub(r",(\s*[}\]])$", r"\1", cleaned, flags=re.MULTILINE)

        if json_str != cleaned:
            logger.debug("JSON cleaning applied")

        return cleaned

    def _extract_json_flexible(
        self, raw_content: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Attempts to extract a JSON object from raw text with multiple strategies.
        Ported and enhanced from the existing implementation.

        Returns:
            Tuple of (parsed_json, surrounding_text) or (None, raw_content) on failure
        """
        content = raw_content.strip()

        # Strategy 1: Try parsing the entire content as JSON (pure JSON response)
        try:
            cleaned_content = self._clean_json_string(content)
            parsed_json = json.loads(cleaned_content)
            logger.debug("Successfully parsed entire content as JSON after cleaning")
            return parsed_json, ""
        except json.JSONDecodeError:
            # Try without cleaning as fallback
            try:
                parsed_json = json.loads(content)
                logger.debug(
                    "Successfully parsed entire content as JSON without cleaning"
                )
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
                prefix = content[: match.start()].strip()
                suffix = content[match.end() :].strip()
                surrounding_text = self._combine_surrounding_text(prefix, suffix)
                logger.debug("Successfully extracted JSON from markdown code block")
                return parsed_json, surrounding_text
            except json.JSONDecodeError:
                # Try without cleaning as fallback
                try:
                    parsed_json = json.loads(json_str)
                    prefix = content[: match.start()].strip()
                    suffix = content[match.end() :].strip()
                    surrounding_text = self._combine_surrounding_text(prefix, suffix)
                    logger.debug(
                        "Successfully extracted JSON from markdown code block without cleaning"
                    )
                    return parsed_json, surrounding_text
                except json.JSONDecodeError as e:
                    logger.warning(f"Found JSON block but failed to parse: {e}")

        # Strategy 3: Find the largest JSON object by looking for balanced braces
        first_brace = content.find("{")
        if first_brace == -1:
            logger.warning("No opening brace found in content")
            return None, content

        # Find the matching closing brace
        brace_count = 0
        end_pos = -1
        in_string = False
        escape_next = False

        for i in range(first_brace, len(content)):
            char = content[i]

            # Handle string literals to avoid counting braces inside strings
            if char == '"' and not escape_next:
                in_string = not in_string
            elif char == "\\":
                escape_next = not escape_next
                continue
            else:
                escape_next = False

            # Only count braces outside of strings
            if not in_string:
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i
                        break

        if end_pos == -1:
            logger.warning("No matching closing brace found")
            return None, content

        # Extract and try to parse the JSON string
        json_str = content[first_brace : end_pos + 1]
        try:
            cleaned_json = self._clean_json_string(json_str)
            parsed_json = json.loads(cleaned_json)
            prefix = content[:first_brace].strip()
            suffix = content[end_pos + 1 :].strip()
            surrounding_text = self._combine_surrounding_text(prefix, suffix)
            logger.debug("Successfully extracted JSON using balanced brace matching")
            return parsed_json, surrounding_text
        except json.JSONDecodeError:
            # Try without cleaning as fallback
            try:
                parsed_json = json.loads(json_str)
                prefix = content[:first_brace].strip()
                suffix = content[end_pos + 1 :].strip()
                surrounding_text = self._combine_surrounding_text(prefix, suffix)
                logger.debug(
                    "Successfully extracted JSON using balanced brace matching without cleaning"
                )
                return parsed_json, surrounding_text
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse extracted JSON string: {e}")
                logger.debug(f"Problematic JSON string: {json_str[:200]}...")
                return None, content

    def _combine_surrounding_text(self, prefix: str, suffix: str) -> str:
        """Helper to combine prefix and suffix text."""
        surrounding_text = ""
        if prefix:
            surrounding_text += prefix
        if suffix:
            if surrounding_text:
                surrounding_text += "\n" + suffix
            else:
                surrounding_text += suffix
        return surrounding_text.strip()
