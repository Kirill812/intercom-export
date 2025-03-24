"""
Configuration management for Intercom Export.
Handles loading settings from environment variables, config files, and CLI arguments.
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
import yaml

@dataclass
class IntercomConfig:
    """Intercom API configuration."""
    api_token: str
    base_url: str = "https://api.intercom.io"
    api_version: str = "2.8"

@dataclass
class ExportConfig:
    """Export configuration."""
    output_format: str = "markdown"  # markdown, json, csv
    output_dir: str = "exports"
    batch_size: int = 15
    include_metadata: bool = True
    include_context: bool = True

@dataclass
class Config:
    """Main configuration class."""
    intercom: IntercomConfig
    export: ExportConfig
    debug: bool = False

def load_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    return {
        "intercom": {
            "api_token": os.getenv("INTERCOM_API_TOKEN"),
            "base_url": os.getenv("INTERCOM_BASE_URL", "https://api.intercom.io"),
            "api_version": os.getenv("INTERCOM_API_VERSION", "2.8"),
        },
        "export": {
            "output_format": os.getenv("EXPORT_FORMAT", "markdown"),
            "output_dir": os.getenv("EXPORT_DIR", "exports"),
            "batch_size": int(os.getenv("BATCH_SIZE", "15")),
            "include_metadata": os.getenv("INCLUDE_METADATA", "true").lower() == "true",
            "include_context": os.getenv("INCLUDE_CONTEXT", "true").lower() == "true",
        },
        "debug": os.getenv("DEBUG", "false").lower() == "true",
    }

def load_from_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def create_config(
    config_file: Optional[str] = None,
    env_vars: bool = True,
    **overrides
) -> Config:
    """
    Create configuration object from multiple sources.
    Priority (highest to lowest): overrides > environment variables > config file
    """
    # Start with empty config
    config_data = {}
    
    # Load from config file if provided
    if config_file:
        config_data.update(load_from_file(config_file))
    
    # Load from environment variables
    if env_vars:
        env_config = load_from_env()
        for key, value in env_config.items():
            if isinstance(value, dict):
                config_data.setdefault(key, {}).update(
                    {k: v for k, v in value.items() if v is not None}
                )
            elif value is not None:
                config_data[key] = value
    
    # Apply overrides
    for key, value in overrides.items():
        if isinstance(value, dict):
            config_data.setdefault(key, {}).update(value)
        else:
            config_data[key] = value
    
    # Create config objects
    intercom_data = config_data.get('intercom', {})
    if not intercom_data.get('api_token'):
        intercom_data['api_token'] = 'default-token'
    if 'api_version' not in intercom_data:
        intercom_data['api_version'] = '2.9'
    intercom_config = IntercomConfig(**intercom_data)
    export_config = ExportConfig(**config_data.get('export', {}))
    debug = config_data.get('debug', False)
    
    return Config(
        intercom=intercom_config,
        export=export_config,
        debug=debug
    )
