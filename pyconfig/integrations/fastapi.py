"""FastAPI integration for PyConfig Universal."""

from typing import Any, Dict, Optional
from ..core.config import Config


class FastAPIConfig(Config):
    """FastAPI-specific configuration management."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def get_app_settings(self) -> Dict[str, Any]:
        """Get settings suitable for FastAPI app configuration."""
        config_dict = self.to_dict()
        
        # Common FastAPI settings
        app_settings = {}
        
        # API metadata
        if 'title' in config_dict:
            app_settings['title'] = config_dict['title']
        if 'description' in config_dict:
            app_settings['description'] = config_dict['description']
        if 'version' in config_dict:
            app_settings['version'] = config_dict['version']
        
        # Server settings
        if 'debug' in config_dict:
            app_settings['debug'] = config_dict['debug']
        
        # CORS settings
        cors_settings = {}
        for key in ['cors_origins', 'cors_methods', 'cors_headers']:
            if key in config_dict:
                cors_key = key.replace('cors_', 'allow_')
                cors_settings[cors_key] = config_dict[key]
        
        if cors_settings:
            app_settings['cors'] = cors_settings
        
        return app_settings
    
    def get_uvicorn_settings(self) -> Dict[str, Any]:
        """Get settings suitable for Uvicorn server."""
        config_dict = self.to_dict()
        
        uvicorn_settings = {}
        
        # Server settings
        if 'host' in config_dict:
            uvicorn_settings['host'] = config_dict['host']
        if 'port' in config_dict:
            uvicorn_settings['port'] = config_dict['port']
        if 'debug' in config_dict:
            uvicorn_settings['debug'] = config_dict['debug']
        if 'reload' in config_dict:
            uvicorn_settings['reload'] = config_dict['reload']
        if 'workers' in config_dict:
            uvicorn_settings['workers'] = config_dict['workers']
        
        # SSL settings
        if 'ssl_keyfile' in config_dict:
            uvicorn_settings['ssl_keyfile'] = config_dict['ssl_keyfile']
        if 'ssl_certfile' in config_dict:
            uvicorn_settings['ssl_certfile'] = config_dict['ssl_certfile']
        
        return uvicorn_settings


def configure_fastapi(app, **config_kwargs) -> FastAPIConfig:
    """Configure FastAPI app with PyConfig Universal."""
    config = FastAPIConfig(**config_kwargs)
    
    # Apply configuration to FastAPI app
    app_settings = config.get_app_settings()
    
    for key, value in app_settings.items():
        if hasattr(app, key):
            setattr(app, key, value)
    
    # Store config instance in app for later access
    app.pyconfig = config
    
    return config


def create_fastapi_app(**config_kwargs):
    """Create and configure FastAPI app with PyConfig Universal."""
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError:
        raise ImportError("FastAPI is required for FastAPI integration")
    
    config = FastAPIConfig(**config_kwargs)
    app_settings = config.get_app_settings()
    
    # Extract CORS settings
    cors_settings = app_settings.pop('cors', {})
    
    # Create FastAPI app
    app = FastAPI(**app_settings)
    
    # Add CORS middleware if configured
    if cors_settings:
        app.add_middleware(CORSMiddleware, **cors_settings)
    
    # Store config instance
    app.pyconfig = config
    
    return app
