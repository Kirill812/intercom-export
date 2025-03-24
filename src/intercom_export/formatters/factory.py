"""
Factory for creating formatters based on output format.
"""

from typing import Optional, TextIO, Type
from .base import BaseFormatter
from .markdown import MarkdownFormatter
from .json_formatter import JSONFormatter

# Registry of available formatters
FORMATTERS = {
    'markdown': MarkdownFormatter,
    'json': JSONFormatter
}

class UnknownFormatError(Exception):
    """Raised when an unknown format is requested."""
    pass

def create_formatter(
    format_name: str,
    file: Optional[TextIO] = None,
    **kwargs
) -> BaseFormatter:
    """
    Create a formatter for the specified format.
    
    Args:
        format_name: Name of the format (e.g., 'markdown', 'json')
        file: Optional file-like object to write to
        **kwargs: Additional arguments to pass to the formatter
    
    Returns:
        Formatter instance
    
    Raises:
        UnknownFormatError: If the format is not supported
    """
    formatter_class = FORMATTERS.get(format_name.lower())
    if not formatter_class:
        raise UnknownFormatError(
            f"Unknown format: {format_name}. "
            f"Available formats: {', '.join(FORMATTERS.keys())}"
        )
    
    if format_name.lower() == "markdown":
        kwargs.pop("indent", None)
    return formatter_class(file, **kwargs)

def register_formatter(
    format_name: str,
    formatter_class: Type[BaseFormatter]
) -> None:
    """
    Register a new formatter.
    
    Args:
        format_name: Name of the format
        formatter_class: Formatter class to register
    """
    if not issubclass(formatter_class, BaseFormatter):
        raise TypeError("Formatter must be a subclass of BaseFormatter")
    FORMATTERS[format_name.lower()] = formatter_class

def get_available_formats() -> list[str]:
    """
    Get list of available formats.
    
    Returns:
        List of format names
    """
    return list(FORMATTERS.keys())
