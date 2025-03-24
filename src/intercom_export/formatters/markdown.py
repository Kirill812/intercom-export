"""
Markdown formatter for conversation exports.
"""

from typing import Dict, Any, List
from .base import BaseFormatter
from ..models.conversation import Conversation

class MarkdownFormatter(BaseFormatter):
    """Formats conversations as markdown documents."""
    
    def format_header(self) -> str:
        """Format the document header."""
        return (
            "# Intercom Support Conversations\n\n"
            "This document contains customer support conversations exported from "
            "Intercom, formatted for LLM analysis.\n\n"
        )
    
    def format_footer(self) -> str:
        """Format the document footer."""
        return ""  # No footer needed for markdown
    
    def _format_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Format metadata key-value pairs as markdown list items."""
        lines = []
        for key, value in sorted(metadata.items()):
            if value is not None:  # Skip None values
                # Handle nested dictionaries
                if isinstance(value, dict):
                    lines.append(f"- **{key}:**")
                    for sub_key, sub_value in value.items():
                        if sub_value is not None:
                            lines.append(f"  - {sub_key}: {sub_value}")
                # Handle lists
                elif isinstance(value, list):
                    if value:  # Only add if list is not empty
                        lines.append(f"- **{key}:** {', '.join(str(v) for v in value)}")
                # Handle simple values
                else:
                    lines.append(f"- **{key}:** {value}")
        return lines
    
    def format_conversation(self, conversation: Conversation) -> str:
        """
        Format a single conversation as markdown.
        
        The format includes:
        - Conversation ID and timestamp
        - Context/metadata section
        - Messages in chronological order
        """
        lines = []
        
        # Conversation header
        lines.extend([
            f"## Conversation {conversation.id}\n",
            f"**Created:** {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        ])
        
        # Context section
        context = {
            'State': conversation.state,
            'Tags': ', '.join(conversation.tags) if conversation.tags else None,
            **conversation.custom_attributes
        }
        
        if any(v is not None for v in context.values()):
            lines.append("### Context\n")
            lines.extend(self._format_metadata(context))
            lines.append("")  # Empty line after context
            # Device Information section
            device_info = {}
            if hasattr(conversation, "browser") and conversation.browser:
                device_info["Browser"] = conversation.browser
            if hasattr(conversation, "browser_version") and conversation.browser_version:
                device_info["Browser Version"] = conversation.browser_version
            if hasattr(conversation, "browser_language") and conversation.browser_language:
                device_info["Browser Language"] = conversation.browser_language
            if hasattr(conversation, "os") and conversation.os:
                device_info["Operating System"] = conversation.os
            if hasattr(conversation, "android_app_name") and conversation.android_app_name:
                device_info["Android App"] = conversation.android_app_name
            if hasattr(conversation, "android_app_version") and conversation.android_app_version:
                device_info["Android App Version"] = conversation.android_app_version
            if hasattr(conversation, "android_device") and conversation.android_device:
                device_info["Android Device"] = conversation.android_device
            if hasattr(conversation, "android_os_version") and conversation.android_os_version:
                device_info["Android OS Version"] = conversation.android_os_version
            if hasattr(conversation, "ios_app_name") and conversation.ios_app_name:
                device_info["iOS App"] = conversation.ios_app_name
            if hasattr(conversation, "ios_app_version") and conversation.ios_app_version:
                device_info["iOS App Version"] = conversation.ios_app_version
            if hasattr(conversation, "ios_device") and conversation.ios_device:
                device_info["iOS Device"] = conversation.ios_device
            if hasattr(conversation, "ios_os_version") and conversation.ios_os_version:
                device_info["iOS OS Version"] = conversation.ios_os_version
            if hasattr(conversation, "location") and conversation.location:
                loc = conversation.location
                loc_str = ", ".join(filter(None, [loc.get("city"), loc.get("region"), loc.get("country")]))
                if loc_str:
                    device_info["Location"] = loc_str
            if device_info:
                lines.append("### Device Information\n")
                lines.extend(self._format_metadata(device_info))
                lines.append("")
        
        # Messages section
        if conversation.messages:
            lines.append("### Conversation\n")
            
            for message in conversation.messages:
                # Message header with timestamp and author
                lines.append(
                    f"**{message.created_at.strftime('%Y-%m-%d %H:%M:%S')} - "
                    f"{message.author.name} ({message.author.type}):**"
                )
                
                # Message content
                if message.body:
                    # Ensure message body ends with exactly two newlines
                    lines.append(message.body.rstrip() + "\n")
        
        # Add separator
        lines.extend(["---", ""])
        
        return "\n".join(lines)
