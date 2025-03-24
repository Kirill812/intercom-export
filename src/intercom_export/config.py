import os
import yaml

def load_file_config():
    """
    Load configuration values from the config.yaml file.
    If the file is missing or cannot be parsed, returns an empty dictionary.
    """
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        return {}

def load_config():
    """
    Load configuration by first reading values from config.yaml and then
    overriding them with any corresponding environment variables that are set.
    This ensures that file-based values are preserved unless explicitly replaced by an environment variable.
    """
    file_config = load_file_config()
    config = {}
    for key, value in file_config.items():
        env_val = os.environ.get(key)
        config[key] = env_val if env_val is not None else value
    return config

class IntercomConfig:
    """
    Configuration class for Intercom settings.
    Can be initialized with a dictionary or using keyword arguments.
    """
    def __init__(self, *args, **kwargs):
        if args:
            self.config = args[0]
        else:
            self.config = kwargs

    def __getitem__(self, key):
        return self.config.get(key)

    def __getattr__(self, name):
        return self.config.get(name)

class ExportConfig:
    """
    Configuration class for export-related settings.
    Can be initialized with a dictionary or using keyword arguments.
    """
    def __init__(self, *args, **kwargs):
        if args:
            self.config = args[0]
        else:
            self.config = kwargs

    def __getitem__(self, key):
        return self.config.get(key)

    def __getattr__(self, name):
        return self.config.get(name)

def create_config(config_file=None, env_vars=False, **overrides):
    """
    Create and return a tuple of configuration objects:
    (IntercomConfig, ExportConfig)
    
    Parameters:
      config_file: Optional file path to load configuration from instead of "config.yaml".
      env_vars: If True, override file configuration with environment variables.
      overrides: Additional key-value overrides.
    """
    if config_file:
        try:
            with open(config_file, "r") as f:
                file_config = yaml.safe_load(f) or {}
        except Exception:
            file_config = {}
    else:
        file_config = load_file_config()
    
    config = dict(file_config)
    
    if env_vars:
        for key, value in os.environ.items():
            config[key] = value

    # Apply additional overrides
    for key, value in overrides.items():
        if isinstance(value, dict) and key in config and isinstance(config[key], dict):
            config[key].update(value)
        else:
            config[key] = value

    return IntercomConfig(config), ExportConfig(config)

# Legacy access to raw config dict if needed
CONFIG = load_config()
# Provide a Config alias for legacy purposes expected by tests
Config = CONFIG
