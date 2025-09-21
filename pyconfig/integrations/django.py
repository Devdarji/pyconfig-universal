"""Django integration for PyConfig Universal."""

import os
from typing import Dict, Any, Optional
from ..core.config import Config


class DjangoConfig(Config):
    """Django-specific configuration management."""
    
    def __init__(self, **kwargs):
        # Auto-detect Django environment
        if 'environment' not in kwargs:
            django_env = self._detect_django_environment()
            if django_env:
                kwargs['environment'] = django_env
        
        super().__init__(**kwargs)
        
        # Auto-configure Django settings
        self._configure_django_settings()
    
    def _detect_django_environment(self) -> Optional[str]:
        """Detect Django environment from DJANGO_SETTINGS_MODULE."""
        settings_module = os.getenv('DJANGO_SETTINGS_MODULE')
        if settings_module and '.' in settings_module:
            parts = settings_module.split('.')
            if len(parts) > 1:
                env_part = parts[-1].lower()
                if env_part in ['development', 'staging', 'production', 'testing']:
                    return env_part
        return None
    
    def _configure_django_settings(self) -> None:
        """Configure Django settings from configuration."""
        try:
            from django.conf import settings
            
            # Common Django settings mapping
            django_mappings = {
                'secret_key': 'SECRET_KEY',
                'debug': 'DEBUG',
                'allowed_hosts': 'ALLOWED_HOSTS',
                'database_url': self._configure_database_url,
                'databases': 'DATABASES',
                'static_url': 'STATIC_URL',
                'static_root': 'STATIC_ROOT',
                'media_url': 'MEDIA_URL',
                'media_root': 'MEDIA_ROOT',
                'time_zone': 'TIME_ZONE',
                'language_code': 'LANGUAGE_CODE',
                'use_i18n': 'USE_I18N',
                'use_l10n': 'USE_L10N',
                'use_tz': 'USE_TZ',
            }
            
            for config_key, django_setting in django_mappings.items():
                value = self.get(config_key)
                if value is not None:
                    if callable(django_setting):
                        django_setting(value)
                    else:
                        setattr(settings, django_setting, value)
        
        except ImportError:
            # Django not available
            pass
    
    def _configure_database_url(self, database_url: str) -> None:
        """Configure Django database from URL."""
        try:
            from django.conf import settings
            import dj_database_url
            
            databases = dj_database_url.parse(database_url)
            settings.DATABASES = {'default': databases}
        
        except ImportError:
            # dj-database-url not available, set URL directly
            try:
                from django.conf import settings
                settings.DATABASE_URL = database_url
            except ImportError:
                pass


def configure_django(config_instance: Config) -> None:
    """Configure Django settings from Config instance."""
    django_config = DjangoConfig(
        schema_file=getattr(config_instance, '_schema_file', None),
        config_files=getattr(config_instance, '_config_files', None),
        environment=config_instance._environment
    )
