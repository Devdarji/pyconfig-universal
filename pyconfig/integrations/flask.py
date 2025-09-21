"""Flask integration for PyConfig Universal."""

from typing import Any, Dict, Optional
from ..core.config import Config


class FlaskConfig(Config):
    """Flask-specific configuration management."""
    
    def __init__(self, app=None, **kwargs):
        # Auto-detect Flask environment
        if 'environment' not in kwargs:
            flask_env = self._detect_flask_environment()
            if flask_env:
                kwargs['environment'] = flask_env
        
        super().__init__(**kwargs)
        
        if app is not None:
            self.init_app(app)
    
    def _detect_flask_environment(self) -> Optional[str]:
        """Detect Flask environment from FLASK_ENV."""
        import os
        flask_env = os.getenv('FLASK_ENV')
        if flask_env:
            return flask_env.lower()
        return None
    
    def init_app(self, app) -> None:
        """Initialize Flask app with configuration."""
        # Flask settings mapping
        flask_mappings = {
            'secret_key': 'SECRET_KEY',
            'debug': 'DEBUG',
            'testing': 'TESTING',
            'host': 'HOST',
            'port': 'PORT',
            'server_name': 'SERVER_NAME',
            'application_root': 'APPLICATION_ROOT',
            'preferred_url_scheme': 'PREFERRED_URL_SCHEME',
            'max_content_length': 'MAX_CONTENT_LENGTH',
            'send_file_max_age_default': 'SEND_FILE_MAX_AGE_DEFAULT',
            'trap_bad_request_errors': 'TRAP_BAD_REQUEST_ERRORS',
            'trap_http_exceptions': 'TRAP_HTTP_EXCEPTIONS',
            'explain_template_loading': 'EXPLAIN_TEMPLATE_LOADING',
            'preserve_context_on_exception': 'PRESERVE_CONTEXT_ON_EXCEPTION',
            'session_cookie_name': 'SESSION_COOKIE_NAME',
            'session_cookie_domain': 'SESSION_COOKIE_DOMAIN',
            'session_cookie_path': 'SESSION_COOKIE_PATH',
            'session_cookie_httponly': 'SESSION_COOKIE_HTTPONLY',
            'session_cookie_secure': 'SESSION_COOKIE_SECURE',
            'session_cookie_samesite': 'SESSION_COOKIE_SAMESITE',
            'permanent_session_lifetime': 'PERMANENT_SESSION_LIFETIME',
            'use_x_sendfile': 'USE_X_SENDFILE',
            'logger_name': 'LOGGER_NAME',
            'logger_handler_policy': 'LOGGER_HANDLER_POLICY',
            'jsonify_prettyprint_regular': 'JSONIFY_PRETTYPRINT_REGULAR',
            'json_as_ascii': 'JSON_AS_ASCII',
            'json_sort_keys': 'JSON_SORT_KEYS',
            'jsonify_mimetype': 'JSONIFY_MIMETYPE',
            'templates_auto_reload': 'TEMPLATES_AUTO_RELOAD',
        }
        
        # Update Flask app config
        for config_key, flask_key in flask_mappings.items():
            value = self.get(config_key)
            if value is not None:
                app.config[flask_key] = value
        
        # Add all configuration to app.config for easy access
        for key, value in self.to_dict().items():
            if key.upper() not in app.config:
                app.config[key.upper()] = value
        
        # Store config instance in app for later access
        app.pyconfig = self


def configure_flask(app, **config_kwargs) -> FlaskConfig:
    """Configure Flask app with PyConfig Universal."""
    config = FlaskConfig(app=app, **config_kwargs)
    return config
