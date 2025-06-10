"""
Tests for the OpenAIService.
"""

from typing import Any
from unittest.mock import MagicMock, Mock, patch

from langchain_core.messages import AIMessage

from app.ai_services.openai_service import OpenAIService
from app.ai_services.schemas import AIResponse
from app.models import ServiceConfigModel


class TestOpenAIService:
    """Test cases for OpenAIService."""

    @patch("app.ai_services.openai_service.ChatOpenAI")
    def test_initialization(self, mock_chat_openai: MagicMock) -> None:
        """Test service initialization with correct parameters."""
        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test-key",
            base_url="http://localhost:8080/v1",
            model_name="test-model",
            parsing_mode="strict",
            temperature=0.5,
        )

        # Verify ChatOpenAI was initialized correctly
        mock_chat_openai.assert_called_once()
        call_kwargs = mock_chat_openai.call_args.kwargs
        assert call_kwargs["api_key"] == "test-key"
        assert call_kwargs["base_url"] == "http://localhost:8080/v1"
        assert call_kwargs["model"] == "test-model"
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_retries"] == 0

        # Verify service attributes
        assert service.model_name == "test-model"
        assert service.parsing_mode == "strict"
        assert service.temperature == 0.5

    @patch("app.ai_services.openai_service.ChatOpenAI")
    def test_initialization_with_dummy_key(self, mock_chat_openai: MagicMock) -> None:
        """Test that None api_key is converted to 'dummy'."""
        OpenAIService(
            config=ServiceConfigModel(),
            api_key=None,
            base_url="http://localhost:8080/v1",
            model_name="local-model",
            parsing_mode="flexible",
        )

        call_kwargs = mock_chat_openai.call_args.kwargs
        assert call_kwargs["api_key"] == "dummy"

    def test_get_response_empty_messages(self) -> None:
        """Test that empty messages list returns None."""
        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test",
            base_url="http://test",
            model_name="test",
        )

        result = service.get_response([])
        assert result is None

    def test_get_response_invalid_message_format(self) -> None:
        """Test handling of invalid message format."""
        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test",
            base_url="http://test",
            model_name="test",
        )

        # Message with unknown role
        messages = [{"role": "unknown", "content": "test"}]
        result = service.get_response(messages)
        assert result is None

    @patch("app.ai_services.openai_service.ChatOpenAI")
    def test_get_response_strict_mode_success(
        self, mock_chat_openai: MagicMock
    ) -> None:
        """Test successful response in strict mode."""
        # Setup mock
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Mock structured output
        mock_structured_llm = Mock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        # Create valid AIResponse
        ai_response = AIResponse(
            narrative="The goblin attacks!",
            dice_requests=[],
            game_state_updates=[],
            end_turn=False,
        )

        # Mock the response
        mock_structured_llm.invoke.return_value = {
            "parsed": ai_response,
            "raw": AIMessage(content='{"narrative": "The goblin attacks!"}'),
        }

        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test",
            base_url="http://test",
            model_name="test",
            parsing_mode="strict",
        )

        messages = [
            {"role": "system", "content": "You are a game master"},
            {"role": "user", "content": "I attack the goblin"},
        ]

        result = service.get_response(messages)

        assert result is not None
        assert isinstance(result, AIResponse)
        assert result.narrative == "The goblin attacks!"
        assert result.end_turn is False

    @patch("app.ai_services.openai_service.ChatOpenAI")
    def test_get_response_strict_mode_fallback_to_flexible(
        self, mock_chat_openai: MagicMock
    ) -> None:
        """Test fallback from strict to flexible mode."""
        # Setup mock
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Mock structured output failure
        mock_structured_llm = Mock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = {
            "parsed": None,
            "raw": AIMessage(
                content='{"narrative": "Fallback response", "dice_requests": []}'
            ),
        }

        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test",
            base_url="http://test",
            model_name="test",
            parsing_mode="strict",
        )

        messages = [{"role": "user", "content": "test"}]

        result = service.get_response(messages)

        assert result is not None
        assert result.narrative == "Fallback response"

    @patch("app.ai_services.openai_service.ChatOpenAI")
    def test_get_response_flexible_mode_success(
        self, mock_chat_openai: MagicMock
    ) -> None:
        """Test successful response in flexible mode."""
        # Setup mock
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Mock response
        mock_llm.invoke.return_value = AIMessage(
            content='```json\n{"narrative": "You see a dragon", "dice_requests": []}\n```'
        )

        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test",
            base_url="http://test",
            model_name="test",
            parsing_mode="flexible",
        )

        messages = [{"role": "user", "content": "Look around"}]

        result = service.get_response(messages)

        assert result is not None
        assert result.narrative == "You see a dragon"

    @patch("app.ai_services.openai_service.ChatOpenAI")
    def test_get_response_flexible_mode_with_trailing_commas(
        self, mock_chat_openai: MagicMock
    ) -> None:
        """Test flexible mode handles JSON with trailing commas."""
        # Setup mock
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Response with trailing comma
        mock_llm.invoke.return_value = AIMessage(
            content='{"narrative": "Test", "dice_requests": [],}'
        )

        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test",
            base_url="http://test",
            model_name="test",
            parsing_mode="flexible",
        )

        messages = [{"role": "user", "content": "test"}]

        result = service.get_response(messages)

        assert result is not None
        assert result.narrative == "Test"

    @patch("app.ai_services.openai_service.ChatOpenAI")
    def test_get_response_empty_content(self, mock_chat_openai: MagicMock) -> None:
        """Test handling of empty response content."""
        # Setup mock
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Empty response
        mock_llm.invoke.return_value = AIMessage(content="")

        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test",
            base_url="http://test",
            model_name="test",
            parsing_mode="flexible",
        )

        messages = [{"role": "user", "content": "test"}]

        result = service.get_response(messages)

        assert result is None

    @patch("app.ai_services.openai_service.ChatOpenAI")
    @patch("time.sleep")  # Mock sleep to speed up test
    def test_rate_limit_detection_and_retry(
        self, mock_sleep: MagicMock, mock_chat_openai: MagicMock
    ) -> None:
        """Test rate limit detection triggers retry with delay."""
        # Setup mock
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Track call count
        call_count = 0

        def side_effect(messages: Any) -> AIMessage:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First attempt: simulate rate limiting
                # Set token monitor values to simulate rate limiting
                service.token_monitor.last_completion_tokens = 0
                service.token_monitor.last_prompt_tokens = 100
                return AIMessage(content="")  # Empty response
            else:
                # Second attempt: success
                return AIMessage(
                    content='{"narrative": "Success after retry", "dice_requests": []}'
                )

        mock_llm.invoke.side_effect = side_effect

        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test",
            base_url="http://test",
            model_name="test",
            parsing_mode="flexible",
        )

        messages = [{"role": "user", "content": "test"}]

        result = service.get_response(messages)

        assert result is not None
        assert result.narrative == "Success after retry"
        # Verify sleep was called with 5 seconds for rate limit
        assert any(call.args == (5.0,) for call in mock_sleep.call_args_list)

    @patch("app.ai_services.openai_service.ChatOpenAI")
    @patch("time.sleep")
    def test_max_retries_exhausted(
        self, mock_sleep: MagicMock, mock_chat_openai: MagicMock
    ) -> None:
        """Test that all retries are exhausted."""
        # Setup mock
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # All attempts fail
        mock_llm.invoke.return_value = AIMessage(content="")

        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test",
            base_url="http://test",
            model_name="test",
            parsing_mode="flexible",
        )

        messages = [{"role": "user", "content": "test"}]

        result = service.get_response(messages)

        assert result is None
        # Should have made 3 attempts
        assert mock_llm.invoke.call_count == 3

    @patch("app.ai_services.openai_service.ChatOpenAI")
    def test_get_response_with_exception(self, mock_chat_openai: MagicMock) -> None:
        """Test exception handling during response generation."""
        # Setup mock
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Raise exception
        mock_llm.invoke.side_effect = Exception("API Error")

        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test",
            base_url="http://test",
            model_name="test",
            parsing_mode="flexible",
        )

        messages = [{"role": "user", "content": "test"}]

        result = service.get_response(messages)

        assert result is None

    @patch("app.ai_services.openai_service.ChatOpenAI")
    def test_structured_output_not_implemented(
        self, mock_chat_openai: MagicMock
    ) -> None:
        """Test fallback when model doesn't support structured output."""
        # Setup mock
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Structured output not implemented
        mock_llm.with_structured_output.side_effect = NotImplementedError

        # Setup fallback response
        mock_llm.invoke.return_value = AIMessage(
            content='{"narrative": "Fallback working", "dice_requests": []}'
        )

        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test",
            base_url="http://test",
            model_name="test",
            parsing_mode="strict",
        )

        messages = [{"role": "user", "content": "test"}]

        result = service.get_response(messages)

        assert result is not None
        assert result.narrative == "Fallback working"

    @patch("app.ai_services.openai_service.ChatOpenAI")
    def test_parse_flexible_validation_error(self, mock_chat_openai: MagicMock) -> None:
        """Test handling of Pydantic validation errors."""
        # Setup mock
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm

        # Invalid JSON structure (missing required field)
        mock_llm.invoke.return_value = AIMessage(
            content='{"end_turn": true}'  # Missing required 'narrative' field
        )

        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test",
            base_url="http://test",
            model_name="test",
            parsing_mode="flexible",
        )

        messages = [{"role": "user", "content": "test"}]

        result = service.get_response(messages)

        assert result is None

    @patch("app.ai_services.openai_service.ChatOpenAI")
    def test_token_monitor_integration(self, mock_chat_openai: MagicMock) -> None:
        """Test that token monitor callback is properly integrated."""
        service = OpenAIService(
            config=ServiceConfigModel(),
            api_key="test",
            base_url="http://test",
            model_name="test",
        )

        # Verify token monitor is in callbacks
        assert service.token_monitor in service.callbacks
        assert len(service.callbacks) == 1

        # Verify it's passed to ChatOpenAI
        call_kwargs = mock_chat_openai.call_args.kwargs
        assert "callbacks" in call_kwargs
        assert service.token_monitor in call_kwargs["callbacks"]
