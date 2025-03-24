"""
Tests for command-line interface.
"""

import os
from unittest.mock import patch, mock_open, MagicMock
import pytest
import yaml

from intercom_export.cli import (
    setup_argparser,
    load_conversation_ids,
    export_conversations,
    main
)
from intercom_export.models.conversation import Conversation
from intercom_export.api.client import IntercomAPIError

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return MagicMock(
        intercom=MagicMock(api_token="test-token"),
        export=MagicMock(
            output_format="markdown",
            batch_size=15
        )
    )

@pytest.fixture
def mock_conversations():
    """Create mock conversation data."""
    return [
        {
            "id": "123456",
            "created_at": 1672567200,
            "updated_at": 1672567500,
            "state": "open",
            "conversation_message": {
                "id": "msg1",
                "body": "Test message",
                "author": {
                    "id": "user1",
                    "name": "John Doe",
                    "type": "user"
                },
                "created_at": 1672567200
            }
        }
    ]

def test_argument_parser():
    """Test command-line argument parsing."""
    parser = setup_argparser()
    
    # Test with minimal arguments
    args = parser.parse_args(["123456"])
    assert args.conversation_ids == [123456]
    assert args.format == "markdown"
    assert not args.verbose
    
    # Test with all arguments
    args = parser.parse_args([
        "--config", "config.yaml",
        "--format", "json",
        "--output", "output.json",
        "--batch-size", "20",
        "-v",
        "123456", "123457"
    ])
    assert args.conversation_ids == [123456, 123457]
    assert args.config == "config.yaml"
    assert args.format == "json"
    assert args.output == "output.json"
    assert args.batch_size == 20
    assert args.verbose

def test_load_conversation_ids_from_text():
    """Test loading conversation IDs from text file."""
    content = "123456\n123457\n123458\n"
    
    with patch("builtins.open", mock_open(read_data=content)):
        ids = load_conversation_ids("conversations.txt")
        assert ids == [123456, 123457, 123458]

def test_load_conversation_ids_from_yaml():
    """Test loading conversation IDs from YAML file."""
    content = """
    conversation_ids:
      - 123456
      - 123457
      - 123458
    """
    
    with patch("builtins.open", mock_open(read_data=content)):
        ids = load_conversation_ids("config.yaml")
        assert ids == [123456, 123457, 123458]

@patch("intercom_export.cli.IntercomClient")
def test_export_conversations_markdown(mock_client_class, mock_config, mock_conversations, tmp_path):
    """Test exporting conversations to markdown."""
    # Setup mock client
    mock_client = mock_client_class.return_value
    mock_client.get_conversations.return_value = mock_conversations
    
    # Create args
    args = MagicMock(
        conversation_ids=[123456],
        format="markdown",
        output=str(tmp_path / "output.md"),
        batch_size=15,
        verbose=False
    )
    
    # Run export
    export_conversations(mock_config, args)
    
    # Check output file was created
    assert os.path.exists(args.output)
    with open(args.output) as f:
        content = f.read()
        assert "## Conversation 123456" in content
        assert "Test message" in content

@patch("intercom_export.cli.IntercomClient")
def test_export_conversations_json(mock_client_class, mock_config, mock_conversations, tmp_path):
    """Test exporting conversations to JSON."""
    # Setup mock client
    mock_client = mock_client_class.return_value
    mock_client.get_conversations.return_value = mock_conversations
    
    # Create args
    args = MagicMock(
        conversation_ids=[123456],
        format="json",
        output=str(tmp_path / "output.json"),
        batch_size=15,
        verbose=False
    )
    
    # Run export
    export_conversations(mock_config, args)
    
    # Check output file was created
    assert os.path.exists(args.output)
    with open(args.output) as f:
        data = yaml.safe_load(f)
        assert isinstance(data, list)
        assert data[0]['id'] == "123456"

@patch("intercom_export.cli.IntercomClient")
def test_export_conversations_error_handling(mock_client_class, mock_config):
    """Test error handling during export."""
    # Setup mock client to raise error
    mock_client = mock_client_class.return_value
    mock_client.get_conversations.side_effect = IntercomAPIError("API Error")
    
    args = MagicMock(
        conversation_ids=[123456],
        format="markdown",
        output="output.md",
        batch_size=15,
        verbose=True
    )
    
    with pytest.raises(SystemExit) as exc_info:
        export_conversations(mock_config, args)
    
    assert exc_info.value.code == 1

@patch("intercom_export.cli.create_config")
@patch("intercom_export.cli.export_conversations")
def test_main_function(mock_export, mock_create_config):
    """Test main function execution."""
    # Setup mocks
    mock_config = MagicMock()
    mock_create_config.return_value = mock_config
    
    # Test with command line arguments
    with patch("sys.argv", ["intercom-export", "123456"]):
        main()
        
        # Check config was created
        mock_create_config.assert_called_once()
        
        # Check export was called
        mock_export.assert_called_once()
        args = mock_export.call_args[0][1]
        assert args.conversation_ids == [123456]

@patch("intercom_export.cli.create_config")
def test_main_function_config_error(mock_create_config):
    """Test main function with configuration error."""
    # Setup mock to raise error
    mock_create_config.side_effect = Exception("Config Error")
    
    with patch("sys.argv", ["intercom-export", "123456"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
