"""
PyConfig Universal - Universal Python Configuration Management Library

A comprehensive configuration management library that solves all configuration-related
pain points in Python applications.
"""

from .core.config import Config
from .core.schema import Schema
from .core.exceptions import (
    ConfigError,
    ConfigValidationError,
    ConfigNotFoundError,
    ConfigTypeError,
)

__version__ = "1.0.0"
__author__ = "PyConfig Universal Team"
__email__ = "team@pyconfig.dev"

__all__ = [
    "Config",
    "Schema", 
    "ConfigError",
    "ConfigValidationError",
    "ConfigNotFoundError",
    "ConfigTypeError",
]
