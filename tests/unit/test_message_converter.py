"""
Tests for the MessageConverter utility class.
"""

import pytest
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.utils.message_converter import MessageConverter


class TestMessageConverter:
    """Test cases for MessageConverter."""
    
    def test_to_single_langchain_system_message(self):
        """Test converting a system message dict to SystemMessage."""
        msg_dict = {"role": "system", "content": "You are a helpful assistant."}
        result = MessageConverter.to_single_langchain(msg_dict)
        
        assert isinstance(result, SystemMessage)
        assert result.content == "You are a helpful assistant."
    
    def test_to_single_langchain_human_message(self):
        """Test converting a user message dict to HumanMessage."""
        msg_dict = {"role": "user", "content": "Hello, how are you?"}
        result = MessageConverter.to_single_langchain(msg_dict)
        
        assert isinstance(result, HumanMessage)
        assert result.content == "Hello, how are you?"
    
    def test_to_single_langchain_ai_message(self):
        """Test converting an assistant message dict to AIMessage."""
        msg_dict = {"role": "assistant", "content": "I'm doing well, thank you!"}
        result = MessageConverter.to_single_langchain(msg_dict)
        
        assert isinstance(result, AIMessage)
        assert result.content == "I'm doing well, thank you!"
    
    def test_to_single_langchain_unknown_role(self):
        """Test that unknown role raises ValueError."""
        msg_dict = {"role": "unknown", "content": "Some content"}
        
        with pytest.raises(ValueError, match="Unknown message role: unknown"):
            MessageConverter.to_single_langchain(msg_dict)
    
    def test_to_single_langchain_empty_content(self):
        """Test converting message with empty content."""
        msg_dict = {"role": "user", "content": ""}
        result = MessageConverter.to_single_langchain(msg_dict)
        
        assert isinstance(result, HumanMessage)
        assert result.content == ""
    
    def test_from_single_langchain_system_message(self):
        """Test converting SystemMessage to dict."""
        msg = SystemMessage(content="System prompt here")
        result = MessageConverter.from_single_langchain(msg)
        
        assert result == {"role": "system", "content": "System prompt here"}
    
    def test_from_single_langchain_human_message(self):
        """Test converting HumanMessage to dict."""
        msg = HumanMessage(content="User input")
        result = MessageConverter.from_single_langchain(msg)
        
        assert result == {"role": "user", "content": "User input"}
    
    def test_from_single_langchain_ai_message(self):
        """Test converting AIMessage to dict."""
        msg = AIMessage(content="AI response")
        result = MessageConverter.from_single_langchain(msg)
        
        assert result == {"role": "assistant", "content": "AI response"}
    
    def test_to_langchain_list(self):
        """Test converting a list of message dicts to LangChain messages."""
        messages = [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        
        result = MessageConverter.to_langchain(messages)
        
        assert len(result) == 3
        assert isinstance(result[0], SystemMessage)
        assert result[0].content == "Be helpful"
        assert isinstance(result[1], HumanMessage)
        assert result[1].content == "Hi"
        assert isinstance(result[2], AIMessage)
        assert result[2].content == "Hello!"
    
    def test_from_langchain_list(self):
        """Test converting a list of LangChain messages to dicts."""
        messages = [
            SystemMessage(content="System instructions"),
            HumanMessage(content="Question"),
            AIMessage(content="Answer"),
        ]
        
        result = MessageConverter.from_langchain(messages)
        
        assert len(result) == 3
        assert result[0] == {"role": "system", "content": "System instructions"}
        assert result[1] == {"role": "user", "content": "Question"}
        assert result[2] == {"role": "assistant", "content": "Answer"}
    
    def test_round_trip_conversion(self):
        """Test that converting back and forth preserves the data."""
        original = [
            {"role": "system", "content": "You are a game master"},
            {"role": "user", "content": "I attack the goblin"},
            {"role": "assistant", "content": "Roll for attack!"},
        ]
        
        # Convert to LangChain and back
        langchain_msgs = MessageConverter.to_langchain(original)
        result = MessageConverter.from_langchain(langchain_msgs)
        
        assert result == original
    
    def test_empty_list_conversion(self):
        """Test converting empty lists."""
        assert MessageConverter.to_langchain([]) == []
        assert MessageConverter.from_langchain([]) == []
    
    def test_missing_fields(self):
        """Test handling of messages with missing fields."""
        # Missing content field defaults to empty string
        msg_dict = {"role": "user"}
        result = MessageConverter.to_single_langchain(msg_dict)
        assert isinstance(result, HumanMessage)
        assert result.content == ""
        
        # Missing role field raises error
        msg_dict = {"content": "Some content"}
        with pytest.raises(ValueError, match="Unknown message role: "):
            MessageConverter.to_single_langchain(msg_dict)