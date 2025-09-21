"""Main configuration management class."""

import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .exceptions import ConfigNotFoundError, ConfigValidationError
from .schema import Schema
from ..loaders.env_loader import EnvLoader
from ..loaders.file_loader import (
    EnvFileLoader, YamlLoader, JsonLoader, TomlLoader, IniLoader
)


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for configuration file changes."""
    
    def __init__(self, config_instance: 'Config'):
        self.config = config_instance
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self.config._trigger_reload()


class Config:
    """Universal configuration management class."""
    
    def __init__(
        self,
        schema_file: Optional[str] = None,
        schema_dict: Optional[Dict[str, Any]] = None,
        config_files: Optional[List[str]] = None,
        environment: Optional[str] = None,
        auto_reload: bool = False,
        reload_callback: Optional[Callable] = None,
        strict_mode: bool = False,
        **loader_options
    ):
        """Initialize configuration manager."""
        self._config_data = {}
        self._schema = None
        self._environment = environment or self._detect_environment()
        self._auto_reload = auto_reload
        self._reload_callback = reload_callback
        self._strict_mode = strict_mode
        self._loader_options = loader_options
        self._lock = threading.RLock()
        self._observer = None
        self._watched_files = set()
        
        # Initialize loaders
        self._loaders = self._init_loaders()
        
        # Load schema if provided
        if schema_file:
            self._schema = Schema.from_file(schema_file)
        elif schema_dict:
            self._schema = Schema(schema_dict)
        
        # Load configuration files
        self._config_files = config_files or self._discover_config_files()
        self._load_all_configs()
        
        # Start file watching if auto-reload is enabled
        if self._auto_reload:
            self._start_file_watching()
    
    def _init_loaders(self) -> List:
        """Initialize configuration loaders."""
        loaders = [
            EnvLoader(environment=self._environment, **self._loader_options),
            EnvFileLoader(environment=self._environment, **self._loader_options),
            YamlLoader(environment=self._environment, **self._loader_options),
            JsonLoader(environment=self._environment, **self._loader_options),
            TomlLoader(environment=self._environment, **self._loader_options),
            IniLoader(environment=self._environment, **self._loader_options),
        ]
        
        # Sort by priority (higher priority first)
        return sorted(loaders, key=lambda x: x.get_priority(), reverse=True)
    
    def _detect_environment(self) -> str:
        """Auto-detect current environment."""
        # Check common environment variables
        env_vars = ['ENVIRONMENT', 'ENV', 'DJANGO_SETTINGS_MODULE', 'FLASK_ENV', 'NODE_ENV']
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # Extract environment from Django settings module
                if var == 'DJANGO_SETTINGS_MODULE' and '.' in value:
                    parts = value.split('.')
                    if len(parts) > 1:
                        return parts[-1].lower()
                return value.lower()
        
        # Check for environment-specific files
        env_files = ['.env.production', '.env.staging', '.env.development']
        for env_file in env_files:
            if os.path.exists(env_file):
                return env_file.split('.')[2]
        
        # Default to development
        return 'development'
    
    def _discover_config_files(self) -> List[str]:
        """Discover configuration files in current directory."""
        config_files = []
        
        # Common configuration file names
        candidates = [
            'config.yaml', 'config.yml', 'config.json', 'config.toml',
            'settings.yaml', 'settings.yml', 'settings.json', 'settings.toml',
            '.env', 'config.ini'
        ]
        
        # Add environment-specific variants
        if self._environment:
            env_candidates = [
                f'config.{self._environment}.yaml', f'config.{self._environment}.yml',
                f'config.{self._environment}.json', f'config.{self._environment}.toml',
                f'settings.{self._environment}.yaml', f'settings.{self._environment}.yml',
                f'settings.{self._environment}.json', f'settings.{self._environment}.toml',
                f'.env.{self._environment}', f'config.{self._environment}.ini'
            ]
            candidates.extend(env_candidates)
        
        for candidate in candidates:
            if os.path.exists(candidate):
                config_files.append(candidate)
        
        return config_files
    
    def _load_all_configs(self) -> None:
        """Load configuration from all sources."""
        with self._lock:
            merged_config = {}
            
            # Load from files (lower priority first)
            for config_file in self._config_files:
                for loader in reversed(self._loaders):  # Reverse for file loading
                    if loader.can_load(config_file) and not isinstance(loader, EnvLoader):
                        try:
                            file_config = loader.load(config_file)
                            merged_config = self._deep_merge(merged_config, file_config)
                            self._watched_files.add(config_file)
                        except Exception:
                            # Skip files that can't be loaded
                            pass
                        break
            
            # Load from environment variables (highest priority)
            env_loader = next(loader for loader in self._loaders if isinstance(loader, EnvLoader))
            env_config = env_loader.load()
            merged_config = self._deep_merge(merged_config, env_config)
            
            # Validate against schema if available
            if self._schema:
                try:
                    validated_config = self._schema.validate(merged_config, self._environment, strict=self._strict_mode)
                    # Merge validated config with any additional unvalidated keys in non-strict mode
                    if not self._strict_mode:
                        for key, value in merged_config.items():
                            if key not in validated_config:
                                validated_config[key] = value
                    self._config_data = validated_config
                except ConfigValidationError:
                    if self._strict_mode:
                        raise
                    # In non-strict mode, use unvalidated config
                    self._config_data = merged_config
            else:
                self._config_data = merged_config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _start_file_watching(self) -> None:
        """Start watching configuration files for changes."""
        if self._observer:
            return
        
        self._observer = Observer()
        handler = ConfigFileHandler(self)
        
        # Watch current directory and any directories containing config files
        watched_dirs = {'.'}
        for file_path in self._watched_files:
            watched_dirs.add(str(Path(file_path).parent))
        
        for watch_dir in watched_dirs:
            self._observer.schedule(handler, watch_dir, recursive=False)
        
        self._observer.start()
    
    def _stop_file_watching(self) -> None:
        """Stop watching configuration files."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
    
    def _trigger_reload(self) -> None:
        """Trigger configuration reload."""
        old_config = self._config_data.copy()
        
        try:
            self._load_all_configs()
            
            # Find changed keys
            changed_keys = []
            all_keys = set(old_config.keys()) | set(self._config_data.keys())
            
            for key in all_keys:
                if old_config.get(key) != self._config_data.get(key):
                    changed_keys.append(key)
            
            # Call reload callback if provided
            if self._reload_callback and changed_keys:
                self._reload_callback(changed_keys, self)
        
        except Exception:
            # Rollback on error
            self._config_data = old_config
            raise
    
    def __getattr__(self, name: str) -> Any:
        """Get configuration value by attribute access."""
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        try:
            return self.get(name)
        except ConfigNotFoundError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        with self._lock:
            # Support nested key access with dots
            if '.' in key:
                return self._get_nested_value(key, default)
            
            if key in self._config_data:
                return self._config_data[key]
            
            # If no default provided and key not found, check if it's required in schema
            if default is None:
                if self._schema and key in self._schema.get_all_fields():
                    field_info = self._schema.get_field_info(key)
                    if field_info['required']:
                        raise ConfigNotFoundError(key)
                # For attribute access, we need to distinguish between None default and no default
                # This is a bit of a hack, but we check the call stack
                import inspect
                frame = inspect.currentframe()
                try:
                    caller = frame.f_back.f_code.co_name if frame.f_back else None
                    if caller == '__getattr__':
                        raise ConfigNotFoundError(key)
                finally:
                    del frame
            
            return default
    
    def _get_nested_value(self, key: str, default: Any = None) -> Any:
        """Get nested configuration value using dot notation."""
        parts = key.split('.')
        current = self._config_data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        with self._lock:
            if '.' in key:
                self._set_nested_value(key, value)
            else:
                self._config_data[key] = value
    
    def _set_nested_value(self, key: str, value: Any) -> None:
        """Set nested configuration value using dot notation."""
        parts = key.split('.')
        current = self._config_data
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def reload(self) -> None:
        """Manually reload configuration."""
        self._trigger_reload()
    
    def validate(self) -> None:
        """Validate current configuration against schema."""
        if not self._schema:
            return
        
        self._schema.validate(self._config_data, self._environment)
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        with self._lock:
            return self._config_data.copy()
    
    def keys(self) -> List[str]:
        """Get all configuration keys."""
        with self._lock:
            return list(self._config_data.keys())
    
    def items(self):
        """Get configuration items."""
        with self._lock:
            return self._config_data.items()
    
    def generate_env_template(self, output_file: str) -> None:
        """Generate .env template file."""
        if not self._schema:
            raise ValueError("Schema is required to generate template")
        
        template_content = self._schema.generate_env_template()
        
        with open(output_file, 'w') as f:
            f.write(template_content)
    
    def generate_docs(self, output_file: str, format: str = 'markdown') -> None:
        """Generate configuration documentation."""
        if not self._schema:
            raise ValueError("Schema is required to generate documentation")
        
        docs_content = self._schema.generate_docs(format)
        
        with open(output_file, 'w') as f:
            f.write(docs_content)
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        # Mask sensitive values
        masked_config = {}
        
        for key, value in self._config_data.items():
            if self._is_sensitive_key(key):
                masked_config[key] = '******'
            else:
                masked_config[key] = value
        
        return f"Config({masked_config})"
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if key contains sensitive information."""
        sensitive_patterns = [
            'password', 'secret', 'key', 'token', 'credential',
            'auth', 'private', 'pass', 'pwd'
        ]
        
        key_lower = key.lower()
        return any(pattern in key_lower for pattern in sensitive_patterns)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._stop_file_watching()
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self._stop_file_watching()
