"""
Tests for configuration management.
"""

import os
import tempfile
from pathlib import Path
import pytest
import yaml

from intercom_export.config import create_config, IntercomConfig, ExportConfig

@pytest.fixture
def config_file():
    """Create a temporary config file for testing."""
    config_data = {
        'intercom': {
            'api_token': 'test-token',
            'base_url': 'https://test.intercom.io',
            'api_version': '2.9'
        },
        'export': {
            'output_format': 'json',
            'output_dir': 'test-exports',
            'batch_size': 20
        },
        'debug': True
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    yield config_path
    os.unlink(config_path)

@pytest.fixture
def env_vars():
    """Set up environment variables for testing."""
    original_env = {}
    test_vars = {
        'INTERCOM_API_TOKEN': 'env-token',
        'INTERCOM_BASE_URL': 'https://env.intercom.io',
        'EXPORT_FORMAT': 'markdown',
        'BATCH_SIZE': '25'
    }
    
    # Save original environment
    for key in test_vars:
        if key in os.environ:
            original_env[key] = os.environ[key]
    
    # Set test environment
    for key, value in test_vars.items():
        os.environ[key] = value
    
    yield test_vars
    
    # Restore original environment
    for key in test_vars:
        if key in original_env:
            os.environ[key] = original_env[key]
        else:
            del os.environ[key]

def test_create_config_defaults():
    """Test creating config with default values."""
    config = create_config(env_vars=False)
    
    assert isinstance(config.intercom, IntercomConfig)
    assert isinstance(config.export, ExportConfig)
    assert config.debug is False
    
    # Check default values
    assert config.export.output_format == 'markdown'
    assert config.export.batch_size == 15

def test_create_config_from_file(config_file):
    """Test loading configuration from file."""
    config = create_config(config_file=config_file, env_vars=False)
    
    assert config.intercom.api_token == 'test-token'
    assert config.intercom.base_url == 'https://test.intercom.io'
    assert config.intercom.api_version == '2.9'
    
    assert config.export.output_format == 'json'
    assert config.export.output_dir == 'test-exports'
    assert config.export.batch_size == 20
    
    assert config.debug is True

def test_create_config_from_env(env_vars):
    """Test loading configuration from environment variables."""
    config = create_config(env_vars=True)
    
    assert config.intercom.api_token == 'env-token'
    assert config.intercom.base_url == 'https://env.intercom.io'
    assert config.export.output_format == 'markdown'
    assert config.export.batch_size == 25

def test_config_precedence(config_file, env_vars):
    """Test configuration precedence (overrides > env > file)."""
    overrides = {
        'intercom': {
            'api_token': 'override-token'
        },
        'export': {
            'batch_size': 30
        }
    }
    
    config = create_config(
        config_file=config_file,
        env_vars=True,
        **overrides
    )
    
    # Should use override values
    assert config.intercom.api_token == 'override-token'
    assert config.export.batch_size == 30
    
    # Should use env values for those not in overrides
    assert config.intercom.base_url == 'https://env.intercom.io'
    assert config.export.output_format == 'markdown'
    
    # Should use file values for those not in env or overrides
    assert config.intercom.api_version == '2.9'
    assert config.export.output_dir == 'test-exports'
    assert config.debug is True

def test_invalid_config_file():
    """Test handling of invalid config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
        f.write("invalid: yaml: content")
        f.flush()
        
        with pytest.raises(Exception):
            create_config(config_file=f.name)

def test_missing_config_file():
    """Test handling of missing config file."""
    config = create_config(config_file='nonexistent.yaml')
    
    # Should use defaults
    assert isinstance(config.intercom, IntercomConfig)
    assert isinstance(config.export, ExportConfig)
    assert config.debug is False
