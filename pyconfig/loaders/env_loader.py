"""Environment variable configuration loader."""

import os
from typing import Dict, Any
from .base import ConfigLoader


class EnvLoader(ConfigLoader):
    """Load configuration from environment variables."""
    
    def __init__(self, prefix: str = '', nested_separator: str = '__', **options):
        super().__init__(**options)
        self.prefix = prefix
        self.nested_separator = nested_separator
    
    def load(self, source: str = '') -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        
        for key, value in os.environ.items():
            # Skip if prefix is specified and key doesn't start with it
            if self.prefix and not key.startswith(self.prefix):
                continue
            
            # Skip system environment variables if no prefix is specified
            if not self.prefix and self._is_system_env_var(key):
                continue
            
            # Remove prefix if specified
            config_key = key
            if self.prefix:
                config_key = key[len(self.prefix):].lstrip('_')
            
            # Handle nested keys (e.g., DATABASE__HOST -> database.host)
            if self.nested_separator in config_key:
                self._set_nested_value(config, config_key, value)
            else:
                config[config_key.lower()] = value
        
        return config
    
    def _is_system_env_var(self, key: str) -> bool:
        """Check if environment variable is a system variable."""
        # Common application configuration patterns
        app_patterns = [
            'DEBUG', 'PORT', 'HOST', 'DATABASE_', 'DB_', 'REDIS_',
            'API_', 'SECRET_', 'KEY_', 'TOKEN_', 'AUTH_',
            'CACHE_', 'LOG_', 'MAIL_', 'EMAIL_', 'SMTP_',
            'ENVIRONMENT', 'ENV', 'CONFIG_', 'SETTINGS_'
        ]
        
        key_upper = key.upper()
        
        # If it matches common app patterns, it's NOT a system var
        if any(key_upper.startswith(pattern) for pattern in app_patterns):
            return False
        
        # System variable patterns
        system_patterns = [
            'PATH', 'HOME', 'USER', 'SHELL', 'TERM', 'PWD', 'OLDPWD',
            'LANG', 'LC_', 'TMPDIR', 'EDITOR', 'PAGER', 'LESS',
            'SSH_', 'DISPLAY', 'XDG_', 'DESKTOP_', 'GNOME_',
            'KDE_', 'QT_', 'GTK_', 'DBUS_', 'XAUTHORITY',
            'CONDA_', 'VIRTUAL_ENV', 'PYTHONPATH', 'PYTHONHOME',
            'PIP_', 'JUPYTER_', 'IPYTHON_', 'MPLBACKEND',
            'AWS_EXECUTION_ENV', 'DENO_', 'NODE_', 'NPM_',
            '_', 'SHLVL', 'PS1', 'PS2', 'IFS', 'OPTIND',
            'CFBUNDLEIDENTIFIER', 'CF_USER_TEXT_ENCODING',
            'NVM_', 'ZSH', 'LS_COLORS', 'LSCOLORS', 'TTY',
            'XPC_', 'LOGNAME', 'Q_', 'QTERM_', 'PYENV_',
            'PYTEST_', 'COVERAGE_'
        ]
        
        return any(key_upper.startswith(prefix) for prefix in system_patterns)
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: str) -> None:
        """Set nested configuration value."""
        parts = key.lower().split(self.nested_separator)
        current = config
        
        # Navigate to the nested location
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the final value
        current[parts[-1]] = value
    
    def can_load(self, source: str) -> bool:
        """Environment loader can always load."""
        return True
    
    def get_priority(self) -> int:
        """Environment variables have high priority."""
        return 100
