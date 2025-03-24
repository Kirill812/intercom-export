"""
Base formatter interface for conversation exports.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TextIO
from ..models.conversation import Conversation

class BaseFormatter(ABC):
    """Base class for conversation formatters."""
    
    def __init__(self, file: Optional[TextIO] = None):
        """
        Initialize the formatter.
        
        Args:
            file: Optional file-like object to write to. If not provided,
                 output will be returned as a string.
        """
        self.file = file
    
    @abstractmethod
    def format_conversation(self, conversation: Conversation) -> str:
        """
        Format a single conversation.
        
        Args:
            conversation: The conversation to format
        
        Returns:
            Formatted conversation string
        """
        pass
    
    @abstractmethod
    def format_header(self) -> str:
        """
        Format the header section of the output.
        
        Returns:
            Formatted header string
        """
        pass
    
    @abstractmethod
    def format_footer(self) -> str:
        """
        Format the footer section of the output.
        
        Returns:
            Formatted footer string
        """
        pass
    
    def format_conversations(self, conversations: List[Conversation]) -> Optional[str]:
        """
        Format multiple conversations.
        
        Args:
            conversations: List of conversations to format
        
        Returns:
            If file is provided, writes to file and returns None.
            Otherwise, returns formatted string.
        """
        # Start with header
        output = [self.format_header()]
        
        # Add each conversation
        for conv in conversations:
            output.append(self.format_conversation(conv))
        
        # Add footer
        output.append(self.format_footer())
        
        # Join all parts
        result = '\n'.join(output)
        
        # Write to file or return string
        if self.file:
            self.file.write(result)
            return None
        return result
