"""
Tests for Intercom API client.
"""

from datetime import datetime
import json
from unittest.mock import patch, Mock
import pytest
import requests

from intercom_export.api.client import (
    IntercomClient,
    IntercomAPIError,
    RateLimitError,
    AuthenticationError
)
from intercom_export.config import IntercomConfig

@pytest.fixture
def client():
    """Create a test API client."""
    config = IntercomConfig(
        api_token="test-token",
        base_url="https://api.intercom.io",
        api_version="2.8"
    )
    return IntercomClient(config)

@pytest.fixture
def mock_response():
    """Create a mock response with test conversation data."""
    return {
        "conversations": [
            {
                "id": "123456",
                "created_at": 1672567200,  # 2023-01-01 12:00:00
                "updated_at": 1672567500,  # 2023-01-01 12:05:00
                "title": "Test Conversation",
                "state": "open",
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
                            "body": "Response message",
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
        ]
    }

def test_get_conversations_success(client, mock_response):
    """Test successful conversation fetching."""
    with patch.object(requests.Session, 'post') as mock_post:
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = mock_response
        
        conversations = client.get_conversations([123456])
        
        assert len(conversations) == 1
        conv = conversations[0]
        assert conv['id'] == "123456"
        assert conv['state'] == "open"
        
        # Check API request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs['json']['query']['value'][0]['value'] == [123456]
        assert kwargs['json']['display_as'] == 'plaintext'
        assert 'conversation_message' in kwargs['json']['expand']

def test_get_conversations_batch_processing(client, mock_response):
    """Test processing conversations in batches."""
    with patch.object(requests.Session, 'post') as mock_post:
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = mock_response
        
        # Test with more IDs than batch size
        conversation_ids = list(range(1, 32))  # 31 IDs
        client.get_conversations(conversation_ids, batch_size=10)
        
        # Should make 4 API calls (3 full batches + 1 partial)
        assert mock_post.call_count == 4
        
        # Check batch sizes
        for i in range(3):  # First 3 batches
            args, kwargs = mock_post.call_args_list[i]
            assert len(kwargs['json']['query']['value'][0]['value']) == 10
        
        # Check last batch
        args, kwargs = mock_post.call_args_list[3]
        assert len(kwargs['json']['query']['value'][0]['value']) == 1

def test_get_conversations_authentication_error(client):
    """Test handling of authentication errors."""
    with patch.object(requests.Session, 'post') as mock_post:
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = 401
        mock_post.return_value.text = "Invalid API token"
        
        with pytest.raises(AuthenticationError) as exc_info:
            client.get_conversations([123456])
        
        assert "Invalid API token" in str(exc_info.value)

def test_get_conversations_rate_limit(client):
    """Test handling of rate limit errors."""
    with patch.object(requests.Session, 'post') as mock_post:
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = 429
        mock_post.return_value.text = "Rate limit exceeded"
        
        with pytest.raises(RateLimitError) as exc_info:
            client.get_conversations([123456])
        
        assert "Rate limit exceeded" in str(exc_info.value)

def test_get_conversations_general_error(client):
    """Test handling of general API errors."""
    with patch.object(requests.Session, 'post') as mock_post:
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Internal server error"
        
        with pytest.raises(IntercomAPIError) as exc_info:
            client.get_conversations([123456])
        
        assert "Internal server error" in str(exc_info.value)

def test_get_conversation_single(client, mock_response):
    """Test fetching a single conversation."""
    with patch.object(requests.Session, 'post') as mock_post:
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = mock_response
        
        conversation = client.get_conversation(123456)
        
        assert conversation['id'] == "123456"
        assert conversation['state'] == "open"
        assert conversation['conversation_message']['body'] == "Initial message"
        
        # Should use get_conversations internally
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs['json']['query']['value'][0]['value'] == [123456]

def test_get_conversation_not_found(client):
    """Test handling of non-existent conversation."""
    with patch.object(requests.Session, 'post') as mock_post:
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {"conversations": []}
        
        with pytest.raises(IntercomAPIError) as exc_info:
            client.get_conversation(123456)
        
        assert "Conversation 123456 not found" in str(exc_info.value)
