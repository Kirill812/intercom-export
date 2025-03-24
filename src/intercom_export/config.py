import os
import yaml

def load_file_config():
    """
    Load configuration values from the config.yaml file.
    If the file is missing, returns an empty dictionary.
    """
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    # Let YAML parsing errors propagate

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
        # Return None if the attribute is not present
        return self.config.get(name)

    def __repr__(self):
        return f"IntercomConfig({self.config})"

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

    def __repr__(self):
        return f"ExportConfig({self.config})"

class CombinedConfig:
    """
    Combined configuration that holds separate configurations for Intercom and Export,
    along with top-level settings like debug.
    """
    def __init__(self, intercom, export, debug=False):
        self.intercom = IntercomConfig(intercom)
        self.export = ExportConfig(export)
        self.debug = debug

    def __repr__(self):
        return f"CombinedConfig(intercom={self.intercom}, export={self.export}, debug={self.debug})"

def create_config(config_file=None, env_vars=False, **overrides):
    """
    Create and return a configuration object (CombinedConfig) with attributes:
    - Intercom configuration accessible via config.api_token, config.base_url, etc.
    - Export configuration accessible via config.export.batch_size, etc.
    
    Parameters:
      config_file: Optional file path to load configuration from instead of "config.yaml".
      env_vars: If True, override file configuration with environment variables.
      overrides: Additional key-value overrides.
    """
    if config_file:
        try:
            with open(config_file, "r") as f:
                file_config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            file_config = {}
    else:
        file_config = load_file_config()

    config = dict(file_config)

    if env_vars:
        # Map specific environment variables to the proper config sections.
        for key, value in os.environ.items():
            if key in {"INTERCOM_API_TOKEN", "INTERCOM_BASE_URL", "INTERCOM_API_VERSION"}:
                intercom = config.get("intercom") or {}
                mapping = {
                    "INTERCOM_API_TOKEN": "api_token",
                    "INTERCOM_BASE_URL": "base_url",
                    "INTERCOM_API_VERSION": "api_version"
                }
                intercom[mapping[key]] = value
                config["intercom"] = intercom
            elif key in {"BATCH_SIZE", "EXPORT_FORMAT", "EXPORT_OUTPUT_DIR", "EXPORT_INCLUDE_METADATA", "EXPORT_INCLUDE_CONTEXT"}:
                export = config.get("export") or {}
                mapping = {
                    "BATCH_SIZE": "batch_size",
                    "EXPORT_FORMAT": "output_format",
                    "EXPORT_OUTPUT_DIR": "output_dir",
                    "EXPORT_INCLUDE_METADATA": "include_metadata",
                    "EXPORT_INCLUDE_CONTEXT": "include_context"
                }
                if key == "BATCH_SIZE":
                    try:
                        export[mapping[key]] = int(value)
                    except ValueError:
                        export[mapping[key]] = value
                elif key in {"EXPORT_INCLUDE_METADATA", "EXPORT_INCLUDE_CONTEXT"}:
                    export[mapping[key]] = value.lower() in ("true", "1", "yes")
                else:
                    export[mapping[key]] = value
                config["export"] = export
            elif key == "DEBUG":
                config["debug"] = value.lower() in ("true", "1", "yes")
            else:
                config[key] = value

    # Apply additional overrides
    for key, value in overrides.items():
        if isinstance(value, dict) and key in config and isinstance(config[key], dict):
            config[key].update(value)
        else:
            config[key] = value

    # Set default values if not provided by file, env, or overrides.
    default_intercom = {
        "base_url": "https://api.intercom.io",
        "api_version": "2.9",
        "api_token": ""
    }
    default_export = {
        "output_format": "markdown",
        "output_dir": "exports",
        "batch_size": 15,
        "include_metadata": True,
        "include_context": True
    }

    intercom_overrides = config.get("intercom")
    if not (isinstance(intercom_overrides, dict) and intercom_overrides is not None):
        intercom_overrides = {}
    export_overrides = config.get("export")
    if not (isinstance(export_overrides, dict) and export_overrides is not None):
        export_overrides = {}

    intercom_config = default_intercom.copy()
    intercom_config.update(intercom_overrides)
    export_config = default_export.copy()
    export_config.update(export_overrides)

    debug_value = config.get("debug", False)
    return CombinedConfig(intercom_config, export_config, debug=debug_value)

# Legacy access to raw config dict if needed
CONFIG = load_config()
# Provide a Config alias for legacy purposes expected by tests
Config = CONFIG
