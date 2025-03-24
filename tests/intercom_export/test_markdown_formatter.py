"""
Tests for markdown formatter.
"""

from datetime import datetime
import io
from intercom_export.models.conversation import Conversation, Message, Author
from intercom_export.formatters.markdown import MarkdownFormatter

def create_test_conversation() -> Conversation:
    """Create a test conversation with sample data."""
    return Conversation(
        id="123456",
        created_at=datetime(2023, 1, 1, 12, 0),
        updated_at=datetime(2023, 1, 1, 12, 30),
        title="Test Conversation",
        state="open",
        messages=[
            Message(
                id="msg1",
                body="Hello, I need help with login",
                author=Author(
                    id="user1",
                    name="John Doe",
                    type="user"
                ),
                created_at=datetime(2023, 1, 1, 12, 0),
                type="comment"
            ),
            Message(
                id="msg2",
                body="I'll help you with that",
                author=Author(
                    id="admin1",
                    name="Support Agent",
                    type="admin"
                ),
                created_at=datetime(2023, 1, 1, 12, 5),
                type="comment"
            )
        ],
        custom_attributes={
            "platform": "iOS",
            "app_version": "1.2.3"
        },
        tags=["support", "login"]
    )

def test_markdown_formatter_single_conversation():
    """Test formatting a single conversation."""
    conversation = create_test_conversation()
    formatter = MarkdownFormatter()
    
    output = formatter.format_conversation(conversation)
    
    # Check conversation header
    assert "## Conversation 123456" in output
    assert "**Created:** 2023-01-01 12:00:00" in output
    
    # Check context section
    assert "### Context" in output
    assert "- **State:** open" in output
    assert "- **platform:** iOS" in output
    assert "- **app_version:** 1.2.3" in output
    assert "- **Tags:** support, login" in output
    
    # Check messages
    assert "### Conversation" in output
    assert "**2023-01-01 12:00:00 - John Doe (user):**" in output
    assert "Hello, I need help with login" in output
    assert "**2023-01-01 12:05:00 - Support Agent (admin):**" in output
    assert "I'll help you with that" in output

def test_markdown_formatter_multiple_conversations():
    """Test formatting multiple conversations."""
    conversations = [
        create_test_conversation(),
        Conversation(
            id="123457",
            created_at=datetime(2023, 1, 2, 12, 0),
            updated_at=datetime(2023, 1, 2, 12, 30),
            state="closed",
            messages=[
                Message(
                    id="msg3",
                    body="Another test message",
                    author=Author(
                        id="user2",
                        name="Jane Smith",
                        type="user"
                    ),
                    created_at=datetime(2023, 1, 2, 12, 0),
                    type="comment"
                )
            ]
        )
    ]
    
    # Test with string output
    formatter = MarkdownFormatter()
    output = formatter.format_conversations(conversations)
    
    # Check both conversations are included
    assert "## Conversation 123456" in output
    assert "## Conversation 123457" in output
    assert "John Doe" in output
    assert "Jane Smith" in output
    
    # Test with file output
    output_file = io.StringIO()
    formatter = MarkdownFormatter(output_file)
    formatter.format_conversations(conversations)
    content = output_file.getvalue()
    
    # Check file content
    assert "## Conversation 123456" in content
    assert "## Conversation 123457" in content

def test_markdown_formatter_empty_conversation():
    """Test formatting a conversation with no messages."""
    conversation = Conversation(
        id="123458",
        created_at=datetime(2023, 1, 1, 12, 0),
        updated_at=datetime(2023, 1, 1, 12, 0),
        state="open"
    )
    
    formatter = MarkdownFormatter()
    output = formatter.format_conversation(conversation)
    
    # Should include basic information
    assert "## Conversation 123458" in output
    assert "**Created:** 2023-01-01 12:00:00" in output
    assert "### Context" in output
    assert "- **State:** open" in output
    # Should not include conversation section
    assert "### Conversation" not in output

def test_markdown_formatter_metadata_handling():
    """Test handling of various metadata types."""
    conversation = Conversation(
        id="123459",
        created_at=datetime(2023, 1, 1, 12, 0),
        updated_at=datetime(2023, 1, 1, 12, 0),
        state="open",
        custom_attributes={
            "string_value": "test",
            "number_value": 123,
            "boolean_value": True,
            "null_value": None,
            "nested_dict": {"key": "value"},
            "list_value": ["item1", "item2"]
        }
    )
    
    formatter = MarkdownFormatter()
    output = formatter.format_conversation(conversation)
    
    # Check metadata formatting
    assert "- **string_value:** test" in output
    assert "- **number_value:** 123" in output
    assert "- **boolean_value:** True" in output
    assert "null_value" not in output  # Should skip None values
    assert "- **nested_dict:**" in output
    assert "  - key: value" in output
    assert "- **list_value:** item1, item2" in output
