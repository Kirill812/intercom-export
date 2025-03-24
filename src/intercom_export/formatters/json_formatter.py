import json
from .base import BaseFormatter

class JSONFormatter(BaseFormatter):
    def __init__(self, file=None, **kwargs):
        self.file = file
        # Use provided indentation or default to 2
        self.indent = kwargs.get("indent", 2)

    def format_conversation(self, conversation):
        """Format a single conversation object as a JSON string."""
        return json.dumps(conversation.to_dict(), indent=self.indent)

    def format_header(self):
        """Return header for JSON output (none for JSON)."""
        return ""

    def format_footer(self):
        """Return footer for JSON output (none for JSON)."""
        return ""

    def format_conversations(self, conversations):
        """
        Format a list of conversation objects (each with a to_dict() method)
        as a JSON array string with specified indentation.
        """
        output = json.dumps([conv.to_dict() for conv in conversations], indent=self.indent)
        if self.file:
            self.file.write(output)
        else:
            return output
