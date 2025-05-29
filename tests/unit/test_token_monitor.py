"""
Tests for token monitoring callback handlers.
"""

import pytest
from uuid import uuid4
from langchain_core.outputs import LLMResult, Generation

from app.utils.token_monitor import CompletionTokenMonitor


class TestCompletionTokenMonitor:
    """Test cases for CompletionTokenMonitor."""
    
    def test_initialization(self):
        """Test that monitor initializes with correct default values."""
        monitor = CompletionTokenMonitor()
        
        assert monitor.last_completion_tokens is None
        assert monitor.last_prompt_tokens is None
        assert monitor.last_total_tokens is None
        assert monitor.total_completion_tokens == 0
        assert monitor.total_prompt_tokens == 0
        assert monitor.call_count == 0
        assert monitor.rate_limit_detected is False
    
    def test_on_llm_end_with_token_usage(self):
        """Test processing LLM response with token usage information."""
        monitor = CompletionTokenMonitor()
        
        # Create mock LLM result with token usage
        response = LLMResult(
            generations=[[Generation(text="Test response")]],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 30,
                    "total_tokens": 80
                }
            }
        )
        
        monitor.on_llm_end(response, run_id=uuid4())
        
        assert monitor.last_prompt_tokens == 50
        assert monitor.last_completion_tokens == 30
        assert monitor.last_total_tokens == 80
        assert monitor.total_prompt_tokens == 50
        assert monitor.total_completion_tokens == 30
        assert monitor.call_count == 1
        assert monitor.rate_limit_detected is False
    
    def test_on_llm_end_rate_limit_detection(self):
        """Test detection of rate limiting pattern."""
        monitor = CompletionTokenMonitor()
        
        # Create response with 0 completion tokens but non-zero prompt tokens
        response = LLMResult(
            generations=[[Generation(text="")]],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 0,
                    "total_tokens": 100
                }
            }
        )
        
        monitor.on_llm_end(response, run_id=uuid4())
        
        assert monitor.last_prompt_tokens == 100
        assert monitor.last_completion_tokens == 0
        assert monitor.rate_limit_detected is True
    
    def test_on_llm_end_no_rate_limit_with_zero_prompt(self):
        """Test that 0 completion tokens with 0 prompt tokens doesn't trigger rate limit detection."""
        monitor = CompletionTokenMonitor()
        
        response = LLMResult(
            generations=[[Generation(text="")]],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        )
        
        monitor.on_llm_end(response, run_id=uuid4())
        
        assert monitor.rate_limit_detected is False
    
    def test_on_llm_end_without_token_usage(self):
        """Test handling response without token usage information."""
        monitor = CompletionTokenMonitor()
        
        # Response without llm_output
        response = LLMResult(
            generations=[[Generation(text="Test response")]]
        )
        
        monitor.on_llm_end(response, run_id=uuid4())
        
        assert monitor.last_completion_tokens is None
        assert monitor.last_prompt_tokens is None
        assert monitor.call_count == 1
    
    def test_on_llm_end_with_empty_token_usage(self):
        """Test handling response with empty token usage dict."""
        monitor = CompletionTokenMonitor()
        
        response = LLMResult(
            generations=[[Generation(text="Test response")]],
            llm_output={"token_usage": {}}
        )
        
        monitor.on_llm_end(response, run_id=uuid4())
        
        assert monitor.last_completion_tokens == 0
        assert monitor.last_prompt_tokens == 0
        assert monitor.last_total_tokens == 0
        assert monitor.call_count == 1
    
    def test_multiple_calls_accumulation(self):
        """Test that multiple calls accumulate token counts correctly."""
        monitor = CompletionTokenMonitor()
        
        # First call
        response1 = LLMResult(
            generations=[[Generation(text="Response 1")]],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 30,
                    "total_tokens": 80
                }
            }
        )
        monitor.on_llm_end(response1, run_id=uuid4())
        
        # Second call
        response2 = LLMResult(
            generations=[[Generation(text="Response 2")]],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 60,
                    "completion_tokens": 40,
                    "total_tokens": 100
                }
            }
        )
        monitor.on_llm_end(response2, run_id=uuid4())
        
        assert monitor.call_count == 2
        assert monitor.total_prompt_tokens == 110  # 50 + 60
        assert monitor.total_completion_tokens == 70  # 30 + 40
        assert monitor.last_prompt_tokens == 60  # From second call
        assert monitor.last_completion_tokens == 40  # From second call
    
    def test_on_llm_error(self):
        """Test error handling."""
        monitor = CompletionTokenMonitor()
        
        error = ValueError("Test error")
        # Should not raise, just log
        monitor.on_llm_error(error, run_id=uuid4())
        
        # State should remain unchanged
        assert monitor.call_count == 0
    
    def test_reset(self):
        """Test resetting the monitor state."""
        monitor = CompletionTokenMonitor()
        
        # Set some state
        response = LLMResult(
            generations=[[Generation(text="Test")]],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 0,
                    "total_tokens": 50
                }
            }
        )
        monitor.on_llm_end(response, run_id=uuid4())
        
        # Reset
        monitor.reset()
        
        assert monitor.last_completion_tokens is None
        assert monitor.last_prompt_tokens is None
        assert monitor.last_total_tokens is None
        assert monitor.rate_limit_detected is False
        # Note: totals and call_count are NOT reset
        assert monitor.total_prompt_tokens == 50
        assert monitor.call_count == 1
    
    def test_get_stats(self):
        """Test getting statistics."""
        monitor = CompletionTokenMonitor()
        
        # Add some data
        response = LLMResult(
            generations=[[Generation(text="Test")]],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150
                }
            }
        )
        monitor.on_llm_end(response, run_id=uuid4())
        
        stats = monitor.get_stats()
        
        assert stats["call_count"] == 1
        assert stats["total_prompt_tokens"] == 100
        assert stats["total_completion_tokens"] == 50
        assert stats["total_tokens"] == 150
        assert stats["last_prompt_tokens"] == 100
        assert stats["last_completion_tokens"] == 50
        assert stats["last_total_tokens"] == 150
        assert stats["rate_limit_detected"] is False
    
    def test_none_values_in_token_usage(self):
        """Test handling None values in token usage."""
        monitor = CompletionTokenMonitor()
        
        response = LLMResult(
            generations=[[Generation(text="Test")]],
            llm_output={
                "token_usage": {
                    "prompt_tokens": None,
                    "completion_tokens": None,
                    "total_tokens": None
                }
            }
        )
        
        monitor.on_llm_end(response, run_id=uuid4())
        
        assert monitor.last_prompt_tokens is None
        assert monitor.last_completion_tokens is None
        assert monitor.total_prompt_tokens == 0  # None treated as 0 for totals
        assert monitor.total_completion_tokens == 0