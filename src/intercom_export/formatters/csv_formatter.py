import csv
from io import StringIO
from typing import Optional, TextIO
from ..formatters.base import BaseFormatter
from ..models.conversation import Conversation

class CSVFormatter(BaseFormatter):
    """Format conversations as CSV."""
    
    def __init__(self, file: Optional[TextIO] = None, include_headers: bool = True, **kwargs):
        """
        Initialize CSV formatter.
        
        Args:
            file: Optional file-like object to write to.
            include_headers: Whether to include a header row in the CSV output.
            **kwargs: Additional options, such as 'flatten_messages', 'delimiter', and 'quotechar'.
        """
        super().__init__(file)
        self.include_headers = include_headers
        self.flatten_messages = kwargs.get('flatten_messages', False)
        self.delimiter = kwargs.get('delimiter', ',')
        self.quotechar = kwargs.get('quotechar', '"')
        
        if self.flatten_messages:
            self.columns = [
                'conversation_id', 'created_at', 'updated_at', 'state',
                'message_id', 'message_type', 'message_author', 'message_text', 
                'message_created_at'
            ]
        else:
            self.columns = [
                'id', 'created_at', 'updated_at', 'state', 'subject',
                'assignee_name', 'assignee_type', 'contact_name', 'contact_email',
                'message_count', 'first_message_text', 'last_message_text'
            ]
    
    def format_header(self) -> str:
        """Format the CSV header row."""
        if not self.include_headers:
            return ""
        output = StringIO()
        writer = csv.writer(output, delimiter=self.delimiter, quotechar=self.quotechar, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(self.columns)
        return output.getvalue().strip()
    
    def format_conversation(self, conversation: Conversation) -> str:
        """Format a single conversation as CSV row(s)."""
        output = StringIO()
        writer = csv.writer(output, delimiter=self.delimiter, quotechar=self.quotechar, quoting=csv.QUOTE_MINIMAL)
        if self.flatten_messages:
            # Write one row per message
            for message in conversation.messages:
                row = [
                    conversation.id,
                    conversation.created_at,
                    conversation.updated_at,
                    conversation.state,
                    message.id,
                    message.type,
                    message.author.get('name', 'Unknown'),
                    message.body.replace("\n", " "),
                    message.created_at
                ]
                writer.writerow(row)
        else:
            # Write a summary row for the conversation
            row = [
                conversation.id,
                conversation.created_at,
                conversation.updated_at,
                conversation.state,
                conversation.subject or 'No subject',
                conversation.assignee.get('name', 'Unassigned') if conversation.assignee else 'Unassigned',
                conversation.assignee.get('type', 'Unknown') if conversation.assignee else 'None',
                conversation.contact.get('name', 'Unknown') if conversation.contact else 'Unknown',
                conversation.contact.get('email', 'No email') if conversation.contact else 'No email',
                len(conversation.messages),
                conversation.messages[0].body.replace("\n", " ") if conversation.messages else "",
                conversation.messages[-1].body.replace("\n", " ") if conversation.messages else ""
            ]
            writer.writerow(row)
        return output.getvalue().strip()
    
    def format_footer(self) -> str:
        """CSV format does not require a footer; return an empty string."""
        return ""
