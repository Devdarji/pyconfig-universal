"""Configuration exceptions and error handling."""

from typing import List, Dict, Any, Optional


class ConfigError(Exception):
    """Base configuration error."""
    pass


class ValidationError(Exception):
    """Represents a single validation error."""
    
    def __init__(self, key: str, message: str, value: Any = None):
        self.key = key
        self.message = message
        self.value = value
        super().__init__(str(self))
    
    def __str__(self) -> str:
        if self.value is not None:
            return f"{self.key}: {self.message} (got: {self.value!r})"
        return f"{self.key}: {self.message}"


class ConfigValidationError(ConfigError):
    """Configuration validation failed."""
    
    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        super().__init__(self.format_errors())
    
    def format_errors(self) -> str:
        """Format validation errors into a readable message."""
        if not self.errors:
            return "Configuration validation failed"
        
        error_lines = ["Configuration validation failed:"]
        for error in self.errors:
            error_lines.append(f"  - {error}")
        
        return "\n".join(error_lines)


class ConfigNotFoundError(ConfigError):
    """Required configuration not found."""
    
    def __init__(self, key: str, searched_locations: Optional[List[str]] = None):
        self.key = key
        self.searched_locations = searched_locations or []
        
        message = f"Required configuration '{key}' not found"
        if self.searched_locations:
            message += f" (searched: {', '.join(self.searched_locations)})"
        
        super().__init__(message)


class ConfigTypeError(ConfigError):
    """Configuration type conversion failed."""
    
    def __init__(self, key: str, expected_type: str, actual_value: Any):
        self.key = key
        self.expected_type = expected_type
        self.actual_value = actual_value
        
        message = (
            f"Configuration '{key}' type conversion failed: "
            f"expected {expected_type}, got {type(actual_value).__name__} "
            f"({actual_value!r})"
        )
        
        super().__init__(message)


class ConfigFileError(ConfigError):
    """Configuration file loading error."""
    
    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        
        message = f"Failed to load configuration file '{file_path}': {reason}"
        super().__init__(message)


class ConfigSchemaError(ConfigError):
    """Configuration schema definition error."""
    pass
