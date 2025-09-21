"""File-based configuration loaders."""

import os
import json
import configparser
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import tomli
    HAS_TOML = True
except ImportError:
    try:
        import tomllib
        HAS_TOML = True
        tomli = tomllib
    except ImportError:
        HAS_TOML = False

from .base import FileLoader, EnvironmentAwareLoader
from ..core.exceptions import ConfigFileError


class EnvFileLoader(FileLoader, EnvironmentAwareLoader):
    """Load configuration from .env files."""
    
    def __init__(self, **options):
        super().__init__(**options)
        self.supported_extensions = ['.env']
    
    def load(self, source: str) -> Dict[str, Any]:
        """Load configuration from .env file."""
        config = {}
        
        # Try environment-specific files first
        sources = self.get_environment_specific_sources(source)
        
        for file_path in sources:
            if os.path.exists(file_path):
                config.update(self._load_env_file(file_path))
        
        return config
    
    def _load_env_file(self, file_path: str) -> Dict[str, Any]:
        """Load a single .env file."""
        config = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Handle nested keys
                        if '__' in key:
                            self._set_nested_value(config, key.lower(), value)
                        else:
                            config[key.lower()] = value
        
        except Exception as e:
            raise ConfigFileError(file_path, str(e))
        
        return config
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: str) -> None:
        """Set nested configuration value."""
        parts = key.split('__')
        current = config
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def can_load(self, source: str) -> bool:
        """Check if source is a .env file."""
        return source.endswith('.env') or '.env.' in source
    
    def get_priority(self) -> int:
        """Env files have medium-high priority."""
        return 80


class YamlLoader(FileLoader, EnvironmentAwareLoader):
    """Load configuration from YAML files."""
    
    def __init__(self, **options):
        super().__init__(**options)
        self.supported_extensions = ['.yaml', '.yml']
    
    def load(self, source: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not HAS_YAML:
            raise ConfigFileError(source, "PyYAML is required for YAML support")
        
        config = {}
        
        # Try environment-specific files first
        sources = self.get_environment_specific_sources(source)
        
        for file_path in sources:
            if os.path.exists(file_path):
                config.update(self._load_yaml_file(file_path))
        
        return config
    
    def _load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """Load a single YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            raise ConfigFileError(file_path, str(e))
    
    def get_priority(self) -> int:
        """YAML files have medium priority."""
        return 60


class JsonLoader(FileLoader, EnvironmentAwareLoader):
    """Load configuration from JSON files."""
    
    def __init__(self, **options):
        super().__init__(**options)
        self.supported_extensions = ['.json']
    
    def load(self, source: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        config = {}
        
        # Try environment-specific files first
        sources = self.get_environment_specific_sources(source)
        
        for file_path in sources:
            if os.path.exists(file_path):
                config.update(self._load_json_file(file_path))
        
        return config
    
    def _load_json_file(self, file_path: str) -> Dict[str, Any]:
        """Load a single JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Handle JSON with comments (strip comments)
                content = f.read()
                content = self._strip_json_comments(content)
                data = json.loads(content)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            raise ConfigFileError(file_path, str(e))
    
    def _strip_json_comments(self, content: str) -> str:
        """Strip comments from JSON content."""
        lines = []
        for line in content.split('\n'):
            # Remove single-line comments
            if '//' in line:
                line = line[:line.index('//')]
            lines.append(line)
        
        # Remove multi-line comments
        content = '\n'.join(lines)
        while '/*' in content and '*/' in content:
            start = content.index('/*')
            end = content.index('*/', start) + 2
            content = content[:start] + content[end:]
        
        return content
    
    def get_priority(self) -> int:
        """JSON files have medium priority."""
        return 50


class TomlLoader(FileLoader, EnvironmentAwareLoader):
    """Load configuration from TOML files."""
    
    def __init__(self, **options):
        super().__init__(**options)
        self.supported_extensions = ['.toml']
    
    def load(self, source: str) -> Dict[str, Any]:
        """Load configuration from TOML file."""
        if not HAS_TOML:
            raise ConfigFileError(source, "tomli is required for TOML support")
        
        config = {}
        
        # Try environment-specific files first
        sources = self.get_environment_specific_sources(source)
        
        for file_path in sources:
            if os.path.exists(file_path):
                config.update(self._load_toml_file(file_path))
        
        return config
    
    def _load_toml_file(self, file_path: str) -> Dict[str, Any]:
        """Load a single TOML file."""
        try:
            with open(file_path, 'rb') as f:
                data = tomli.load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            raise ConfigFileError(file_path, str(e))
    
    def get_priority(self) -> int:
        """TOML files have medium priority."""
        return 55


class IniLoader(FileLoader, EnvironmentAwareLoader):
    """Load configuration from INI files."""
    
    def __init__(self, **options):
        super().__init__(**options)
        self.supported_extensions = ['.ini', '.cfg']
    
    def load(self, source: str) -> Dict[str, Any]:
        """Load configuration from INI file."""
        config = {}
        
        # Try environment-specific files first
        sources = self.get_environment_specific_sources(source)
        
        for file_path in sources:
            if os.path.exists(file_path):
                config.update(self._load_ini_file(file_path))
        
        return config
    
    def _load_ini_file(self, file_path: str) -> Dict[str, Any]:
        """Load a single INI file."""
        try:
            parser = configparser.ConfigParser()
            parser.read(file_path, encoding='utf-8')
            
            config = {}
            for section_name in parser.sections():
                section_dict = dict(parser[section_name])
                if section_name == 'DEFAULT':
                    config.update(section_dict)
                else:
                    config[section_name.lower()] = section_dict
            
            return config
        except Exception as e:
            raise ConfigFileError(file_path, str(e))
    
    def get_priority(self) -> int:
        """INI files have low priority."""
        return 30
