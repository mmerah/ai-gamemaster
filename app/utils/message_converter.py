"""
Bridge utilities for converting between LangChain message formats and dictionary formats.
This allows gradual migration from dict-based messages to LangChain BaseMessage objects.
"""

from typing import Dict, List

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

from app.models.common import MessageDict


class MessageConverter:
    """Utility class for converting between message formats."""

    @staticmethod
    def to_single_langchain(message: MessageDict) -> BaseMessage:
        """
        Convert a single MessageDict to a LangChain BaseMessage.

        Args:
            message: MessageDict with 'role' and 'content' attributes

        Returns:
            Appropriate LangChain message object

        Raises:
            ValueError: If role is not recognized
        """
        role = message.role
        content = message.content

        if role == "system":
            return SystemMessage(content=content)
        elif role == "user":
            return HumanMessage(content=content)
        elif role == "assistant":
            return AIMessage(content=content)
        else:
            raise ValueError(f"Unknown message role: {role}")

    @staticmethod
    def from_single_langchain(message: BaseMessage) -> Dict[str, str]:
        """
        Convert a single LangChain BaseMessage to a dictionary.

        Args:
            message: LangChain message object

        Returns:
            Dictionary with 'role' and 'content' keys
        """
        if isinstance(message, SystemMessage):
            role = "system"
        elif isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        else:
            # Fallback for any other message types
            role = message.__class__.__name__.lower().replace("message", "")

        content = message.content
        # Convert list or dict content to string if needed
        if isinstance(content, (list, dict)):
            content = str(content)

        return {"role": role, "content": content}

    @staticmethod
    def to_langchain(messages: List[MessageDict]) -> List[BaseMessage]:
        """
        Convert a list of MessageDict objects to LangChain BaseMessage objects.

        Args:
            messages: List of MessageDict objects with 'role' and 'content' attributes

        Returns:
            List of LangChain message objects
        """
        return [MessageConverter.to_single_langchain(msg) for msg in messages]

    @staticmethod
    def from_langchain(messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """
        Convert a list of LangChain BaseMessage objects to dictionary format.

        Args:
            messages: List of LangChain message objects

        Returns:
            List of dictionaries with 'role' and 'content' keys
        """
        return [MessageConverter.from_single_langchain(msg) for msg in messages]
