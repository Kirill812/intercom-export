"""
JSON formatter for conversation exports.
"""

import json
from typing import List, Optional, TextIO
from .base import BaseFormatter
from ..models.conversation import Conversation

class JSONFormatter(BaseFormatter):
    """Formats conversations as JSON documents."""
    
    def __init__(self, file: Optional[TextIO] = None, indent: int = 2):
        """
        Initialize the formatter.
        
        Args:
            file: Optional file-like object to write to
            indent: Number of spaces for JSON indentation
        """
        super().__init__(file)
        self.indent = indent
    
    def format_header(self) -> str:
        """Format the document header."""
        return "["  # Start JSON array
    
    def format_footer(self) -> str:
        """Format the document footer."""
        return "\n]"  # End JSON array
    
    def format_conversation(self, conversation: Conversation) -> str:
        """
        Format a single conversation as JSON.
        
        Args:
            conversation: The conversation to format
        
        Returns:
            JSON string representation of the conversation
        """
        # Convert conversation to dictionary
        data = conversation.to_dict()
        
        # Format as JSON
        json_str = json.dumps(data, indent=self.indent, ensure_ascii=False)
        
        # If this isn't the first conversation, prepend a comma
        if self.file and self.file.tell() > len(self.format_header()):
            return ",\n" + json_str
        return json_str
    
    def format_conversations(self, conversations: List[Conversation]) -> Optional[str]:
        """
        Format multiple conversations as a JSON array.
        
        Args:
            conversations: List of conversations to format
        
        Returns:
            If file is provided, writes to file and returns None.
            Otherwise, returns formatted JSON string.
        """
        if not self.file:
            # For string output, use standard JSON encoding
            return json.dumps(
                [conv.to_dict() for conv in conversations],
                indent=self.indent,
                ensure_ascii=False
            )
        
        # For file output, write incrementally
        return super().format_conversations(conversations)
