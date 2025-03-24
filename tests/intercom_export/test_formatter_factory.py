"""
Tests for formatter factory.
"""

import io
import pytest
from intercom_export.formatters.factory import (
    create_formatter,
    register_formatter,
    get_available_formats,
    UnknownFormatError,
    BaseFormatter
)
from intercom_export.formatters.markdown import MarkdownFormatter
from intercom_export.formatters.json_formatter import JSONFormatter

def test_create_markdown_formatter():
    """Test creating a markdown formatter."""
    formatter = create_formatter('markdown')
    assert isinstance(formatter, MarkdownFormatter)
    
    # Test with file
    output_file = io.StringIO()
    formatter = create_formatter('markdown', output_file)
    assert isinstance(formatter, MarkdownFormatter)
    assert formatter.file == output_file

def test_create_json_formatter():
    """Test creating a JSON formatter."""
    formatter = create_formatter('json')
    assert isinstance(formatter, JSONFormatter)
    
    # Test with custom indentation
    formatter = create_formatter('json', indent=4)
    assert isinstance(formatter, JSONFormatter)
    assert formatter.indent == 4

def test_create_formatter_case_insensitive():
    """Test format name case insensitivity."""
    assert isinstance(create_formatter('MARKDOWN'), MarkdownFormatter)
    assert isinstance(create_formatter('Json'), JSONFormatter)
    assert isinstance(create_formatter('markdown'), MarkdownFormatter)
    assert isinstance(create_formatter('JSON'), JSONFormatter)

def test_create_formatter_unknown_format():
    """Test handling of unknown format."""
    with pytest.raises(UnknownFormatError) as exc_info:
        create_formatter('unknown')
    
    error_msg = str(exc_info.value)
    assert "Unknown format: unknown" in error_msg
    assert "markdown" in error_msg
    assert "json" in error_msg

def test_register_custom_formatter():
    """Test registering a custom formatter."""
    class CustomFormatter(BaseFormatter):
        def format_header(self) -> str:
            return ""
        
        def format_footer(self) -> str:
            return ""
        
        def format_conversation(self, conversation) -> str:
            return str(conversation)
    
    # Register the formatter
    register_formatter('custom', CustomFormatter)
    
    # Check it's available
    assert 'custom' in get_available_formats()
    
    # Create an instance
    formatter = create_formatter('custom')
    assert isinstance(formatter, CustomFormatter)

def test_get_available_formats():
    """Test getting list of available formats."""
    formats = get_available_formats()
    
    assert 'markdown' in formats
    assert 'json' in formats
    assert len(formats) >= 2  # At least markdown and json

def test_formatter_with_kwargs():
    """Test passing additional arguments to formatters."""
    # Test with JSON formatter
    formatter = create_formatter('json', indent=None)
    assert isinstance(formatter, JSONFormatter)
    assert formatter.indent is None
    
    # Test with file and kwargs
    output_file = io.StringIO()
    formatter = create_formatter('json', output_file, indent=4)
    assert formatter.file == output_file
    assert formatter.indent == 4

def test_register_formatter_overwrite():
    """Test overwriting an existing formatter registration."""
    class NewMarkdownFormatter(BaseFormatter):
        def format_header(self) -> str:
            return ""
        
        def format_footer(self) -> str:
            return ""
        
        def format_conversation(self, conversation) -> str:
            return str(conversation)
    
    # Register new implementation
    register_formatter('markdown', NewMarkdownFormatter)
    
    # Check new implementation is used
    formatter = create_formatter('markdown')
    assert isinstance(formatter, NewMarkdownFormatter)
    assert not isinstance(formatter, MarkdownFormatter)

def test_register_formatter_invalid():
    """Test registering invalid formatter classes."""
    # Test with non-BaseFormatter class
    class InvalidFormatter:
        pass
    
    with pytest.raises(TypeError):
        register_formatter('invalid', InvalidFormatter)
    
    # Test with abstract base class
    with pytest.raises(TypeError):
        register_formatter('invalid', BaseFormatter)
