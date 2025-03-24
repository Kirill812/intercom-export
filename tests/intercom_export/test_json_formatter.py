"""
Tests for JSON formatter.
"""

import io
import json
from datetime import datetime
from intercom_export.models.conversation import Conversation, Message, Author
from intercom_export.formatters.json_formatter import JSONFormatter

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
                body="Hello, I need help",
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
                body="I'll help you",
                author=Author(
                    id="admin1",
                    name="Support Agent",
                    type="admin"
                ),
                created_at=datetime(2023, 1, 1, 12, 5),
                type="comment"
            )
        ],
        custom_attributes={"platform": "iOS"},
        tags=["support"]
    )

def test_json_formatter_single_conversation():
    """Test formatting a single conversation."""
    conversation = create_test_conversation()
    formatter = JSONFormatter()
    
    output = formatter.format_conversation(conversation)
    data = json.loads(output)
    
    # Check basic fields
    assert data['id'] == "123456"
    assert data['created_at'] == "2023-01-01T12:00:00"
    assert data['title'] == "Test Conversation"
    assert data['state'] == "open"
    
    # Check messages
    assert len(data['messages']) == 2
    assert data['messages'][0]['body'] == "Hello, I need help"
    assert data['messages'][1]['body'] == "I'll help you"
    
    # Check metadata
    assert data['custom_attributes'] == {"platform": "iOS"}
    assert data['tags'] == ["support"]

def test_json_formatter_multiple_conversations_string():
    """Test formatting multiple conversations as string."""
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
                    body="Another message",
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
    
    formatter = JSONFormatter()
    output = formatter.format_conversations(conversations)
    data = json.loads(output)
    
    assert len(data) == 2
    assert data[0]['id'] == "123456"
    assert data[1]['id'] == "123457"
    assert len(data[0]['messages']) == 2
    assert len(data[1]['messages']) == 1

def test_json_formatter_multiple_conversations_file():
    """Test formatting multiple conversations to file."""
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
                    body="Another message",
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
    
    output_file = io.StringIO()
    formatter = JSONFormatter(output_file)
    formatter.format_conversations(conversations)
    
    # Parse the output
    content = output_file.getvalue()
    data = json.loads(content)
    
    assert len(data) == 2
    assert data[0]['id'] == "123456"
    assert data[1]['id'] == "123457"
    assert isinstance(data, list)

def test_json_formatter_empty_conversation():
    """Test formatting a conversation with no messages."""
    conversation = Conversation(
        id="123458",
        created_at=datetime(2023, 1, 1, 12, 0),
        updated_at=datetime(2023, 1, 1, 12, 0),
        state="open"
    )
    
    formatter = JSONFormatter()
    output = formatter.format_conversation(conversation)
    data = json.loads(output)
    
    assert data['id'] == "123458"
    assert data['state'] == "open"
    assert data['messages'] == []
    assert data['custom_attributes'] == {}
    assert data['tags'] == []

def test_json_formatter_indentation():
    """Test JSON formatting with different indentation."""
    conversation = create_test_conversation()
    
    # Test with no indentation
    formatter = JSONFormatter(indent=None)
    output = formatter.format_conversation(conversation)
    assert "\n" not in output
    
    # Test with custom indentation
    formatter = JSONFormatter(indent=4)
    output = formatter.format_conversation(conversation)
    lines = output.split("\n")
    assert lines[1].startswith("    ")  # Check indentation level

def test_json_formatter_unicode():
    """Test handling of Unicode characters."""
    conversation = Conversation(
        id="123459",
        created_at=datetime(2023, 1, 1, 12, 0),
        updated_at=datetime(2023, 1, 1, 12, 0),
        state="open",
        messages=[
            Message(
                id="msg1",
                body="Hello, 你好, Привет",
                author=Author(
                    id="user1",
                    name="José García",
                    type="user"
                ),
                created_at=datetime(2023, 1, 1, 12, 0),
                type="comment"
            )
        ]
    )
    
    formatter = JSONFormatter()
    output = formatter.format_conversation(conversation)
    data = json.loads(output)
    
    assert data['messages'][0]['body'] == "Hello, 你好, Привет"
    assert data['messages'][0]['author']['name'] == "José García"
