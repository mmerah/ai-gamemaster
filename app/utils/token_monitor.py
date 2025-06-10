"""
LangChain callback handlers for monitoring and debugging.
"""

import logging
from typing import Any, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from app.models.models import TokenStatsModel

logger = logging.getLogger(__name__)


class CompletionTokenMonitor(BaseCallbackHandler):
    """
    Callback handler to monitor completion tokens and detect rate limiting patterns.
    """

    def __init__(self) -> None:
        """Initialize the monitor."""
        super().__init__()
        self.last_completion_tokens: Optional[int] = None
        self.last_prompt_tokens: Optional[int] = None
        self.last_total_tokens: Optional[int] = None
        self.total_completion_tokens: int = 0
        self.total_prompt_tokens: int = 0
        self.call_count: int = 0
        self.rate_limit_detected: bool = False

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """
        Called when LLM finishes generating.

        Args:
            response: The LLM result containing token usage info
            run_id: The run ID
            parent_run_id: The parent run ID if any
            **kwargs: Additional keyword arguments
        """
        # LangChain callback parameters - mark as unused
        _ = run_id
        _ = parent_run_id
        self.call_count += 1

        # Extract token usage from response
        if response.llm_output and isinstance(response.llm_output, dict):
            token_usage = response.llm_output.get("token_usage", {})

            self.last_completion_tokens = token_usage.get("completion_tokens", 0)
            self.last_prompt_tokens = token_usage.get("prompt_tokens", 0)
            self.last_total_tokens = token_usage.get("total_tokens", 0)

            # Update totals
            self.total_completion_tokens += self.last_completion_tokens or 0
            self.total_prompt_tokens += self.last_prompt_tokens or 0

            # Log token usage
            logger.info(
                f"Token usage - Prompt: {self.last_prompt_tokens}, "
                f"Completion: {self.last_completion_tokens}, "
                f"Total: {self.last_total_tokens}"
            )

            # Check for rate limiting pattern (0 completion tokens with non-zero prompt tokens)
            if (
                self.last_completion_tokens == 0
                and self.last_prompt_tokens is not None
                and self.last_prompt_tokens > 0
            ):
                self.rate_limit_detected = True
                logger.warning(
                    "Detected rate limiting: Model processed prompt but generated 0 completion tokens"
                )
        else:
            logger.debug("No token usage information in response")

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """
        Called when LLM errors.

        Args:
            error: The error that occurred
            run_id: The run ID
            parent_run_id: The parent run ID if any
            **kwargs: Additional keyword arguments
        """
        # LangChain callback parameters - mark as unused
        _ = run_id
        _ = parent_run_id
        logger.error(f"LLM error in CompletionTokenMonitor: {error}")

    def reset(self) -> None:
        """Reset the monitor state."""
        self.last_completion_tokens = None
        self.last_prompt_tokens = None
        self.last_total_tokens = None
        self.rate_limit_detected = False

    def get_stats(self) -> TokenStatsModel:
        """
        Get current statistics.

        Returns:
            TokenStatsModel with token usage statistics
        """
        total_tokens = self.total_completion_tokens + self.total_prompt_tokens
        avg_tokens = total_tokens / self.call_count if self.call_count > 0 else 0.0

        return TokenStatsModel(
            total_prompt_tokens=self.total_prompt_tokens,
            total_completion_tokens=self.total_completion_tokens,
            total_tokens=total_tokens,
            call_count=self.call_count,
            average_tokens_per_call=avg_tokens,
        )
