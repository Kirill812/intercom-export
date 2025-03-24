"""
Tests for data models.
"""

from datetime import datetime
import pytest

from intercom_export.models.conversation import (
    Author,
    Message,
    Conversation
)

def test_author_creation():
    """Test creating an Author instance."""
    author = Author(
        id="user1",
        name="John Doe",
        type="user",
        email="john@example.com"
    )
    
    assert author.id == "user1"
    assert author.name == "John Doe"
    assert author.type == "user"
    assert author.email == "john@example.com"

def test_message_creation():
    """Test creating a Message instance."""
    author = Author(id="user1", name="John Doe", type="user")
    created_at = datetime(2023, 1, 1, 12, 0)
    
    message = Message(
        id="msg1",
        body="Test message",
        author=author,
        created_at=created_at,
        type="comment",
        metadata={"source": "web"}
    )
    
    assert message.id == "msg1"
    assert message.body == "Test message"
    assert message.author == author
    assert message.created_at == created_at
    assert message.type == "comment"
    assert message.metadata == {"source": "web"}

def test_message_from_api_data():
    """Test creating a Message from API response data."""
    api_data = {
        "id": "msg1",
        "body": "Test message",
        "author": {
            "id": "user1",
            "name": "John Doe",
            "type": "user",
            "email": "john@example.com"
        },
        "created_at": 1672567200,  # 2023-01-01 12:00:00
        "part_type": "comment",
        "source": "web"
    }
    
    message = Message.from_api_data(api_data)
    
    assert message.id == "msg1"
    assert message.body == "Test message"
    assert message.author.id == "user1"
    assert message.author.name == "John Doe"
    assert message.created_at == datetime(2023, 1, 1, 12, 0)
    assert message.type == "comment"
    assert message.metadata == {"source": "web"}

def test_conversation_creation():
    """Test creating a Conversation instance."""
    created_at = datetime(2023, 1, 1, 12, 0)
    updated_at = datetime(2023, 1, 1, 12, 30)
    
    conversation = Conversation(
        id="conv1",
        created_at=created_at,
        updated_at=updated_at,
        title="Test Conversation",
        state="open",
        custom_attributes={"platform": "iOS"},
        tags=["support"]
    )
    
    assert conversation.id == "conv1"
    assert conversation.created_at == created_at
    assert conversation.updated_at == updated_at
    assert conversation.title == "Test Conversation"
    assert conversation.state == "open"
    assert conversation.custom_attributes == {"platform": "iOS"}
    assert conversation.tags == ["support"]
    assert len(conversation.messages) == 0

def test_conversation_from_api_data():
    """Test creating a Conversation from API response data."""
    api_data = {
        "id": "conv1",
        "created_at": 1672567200,  # 2023-01-01 12:00:00
        "updated_at": 1672567500,  # 2023-01-01 12:05:00
        "title": "Test Conversation",
        "state": "open",
        "custom_attributes": {"platform": "iOS"},
        "tags": [{"name": "support"}],
        "conversation_message": {
            "id": "msg1",
            "body": "Initial message",
            "author": {
                "id": "user1",
                "name": "John Doe",
                "type": "user"
            },
            "created_at": 1672567200
        },
        "conversation_parts": {
            "conversation_parts": [
                {
                    "id": "msg2",
                    "body": "Response",
                    "author": {
                        "id": "admin1",
                        "name": "Support Agent",
                        "type": "admin"
                    },
                    "created_at": 1672567500,
                    "part_type": "comment"
                }
            ]
        }
    }
    
    conversation = Conversation.from_api_data(api_data)
    
    assert conversation.id == "conv1"
    assert conversation.created_at == datetime(2023, 1, 1, 12, 0)
    assert conversation.updated_at == datetime(2023, 1, 1, 12, 5)
    assert conversation.title == "Test Conversation"
    assert conversation.state == "open"
    assert conversation.custom_attributes == {"platform": "iOS"}
    assert conversation.tags == ["support"]
    
    # Check messages
    assert len(conversation.messages) == 2
    
    # Check initial message
    initial_msg = conversation.messages[0]
    assert initial_msg.id == "msg1"
    assert initial_msg.body == "Initial message"
    assert initial_msg.author.name == "John Doe"
    
    # Check response message
    response_msg = conversation.messages[1]
    assert response_msg.id == "msg2"
    assert response_msg.body == "Response"
    assert response_msg.author.name == "Support Agent"

def test_conversation_to_dict():
    """Test converting a Conversation to dictionary format."""
    conversation = Conversation(
        id="conv1",
        created_at=datetime(2023, 1, 1, 12, 0),
        updated_at=datetime(2023, 1, 1, 12, 5),
        title="Test Conversation",
        state="open",
        messages=[
            Message(
                id="msg1",
                body="Test message",
                author=Author(id="user1", name="John Doe", type="user"),
                created_at=datetime(2023, 1, 1, 12, 0),
                type="comment"
            )
        ],
        custom_attributes={"platform": "iOS"},
        tags=["support"]
    )
    
    data = conversation.to_dict()
    
    assert data['id'] == "conv1"
    assert data['created_at'] == "2023-01-01T12:00:00"
    assert data['title'] == "Test Conversation"
    assert data['state'] == "open"
    assert data['custom_attributes'] == {"platform": "iOS"}
    assert data['tags'] == ["support"]
    
    # Check message serialization
    assert len(data['messages']) == 1
    msg_data = data['messages'][0]
    assert msg_data['id'] == "msg1"
    assert msg_data['body'] == "Test message"
    assert msg_data['author']['name'] == "John Doe"
    assert msg_data['created_at'] == "2023-01-01T12:00:00"

def test_conversation_empty_fields():
    """Test handling of empty or missing fields."""
    conversation = Conversation(
        id="conv1",
        created_at=datetime(2023, 1, 1),
        updated_at=datetime(2023, 1, 1)
    )
    
    assert conversation.title is None
    assert conversation.state == "open"  # Default value
    assert conversation.messages == []
    assert conversation.custom_attributes == {}
    assert conversation.tags == []
    assert conversation.metadata == {}
