"""Type system for configuration validation."""

import re
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from urllib.parse import urlparse
from .exceptions import ValidationError


class TypeValidator:
    """Base class for type validators."""
    
    def __init__(self, **kwargs):
        self.options = kwargs
    
    def validate(self, key: str, value: Any) -> Any:
        """Validate and convert value. Returns converted value or raises ValidationError."""
        raise NotImplementedError
    
    def get_description(self) -> str:
        """Get human-readable description of this type."""
        return self.__class__.__name__.replace('Validator', '').lower()


class StringValidator(TypeValidator):
    """String type validator."""
    
    def validate(self, key: str, value: Any) -> str:
        if value is None:
            raise ValidationError(key, "cannot be None", value)
        
        # Convert to string
        str_value = str(value)
        
        # Strip whitespace if requested
        if self.options.get('strip', False):
            str_value = str_value.strip()
        
        # Check length constraints
        min_length = self.options.get('min_length')
        if min_length is not None and len(str_value) < min_length:
            raise ValidationError(key, f"must be at least {min_length} characters", str_value)
        
        max_length = self.options.get('max_length')
        if max_length is not None and len(str_value) > max_length:
            raise ValidationError(key, f"must be at most {max_length} characters", str_value)
        
        # Check regex pattern
        regex = self.options.get('regex')
        if regex and not re.match(regex, str_value):
            raise ValidationError(key, f"must match pattern {regex}", str_value)
        
        return str_value
    
    def get_description(self) -> str:
        desc = "string"
        if 'min_length' in self.options or 'max_length' in self.options:
            min_len = self.options.get('min_length', 0)
            max_len = self.options.get('max_length', '∞')
            desc += f" (length: {min_len}-{max_len})"
        return desc


class IntValidator(TypeValidator):
    """Integer type validator."""
    
    def validate(self, key: str, value: Any) -> int:
        if value is None:
            raise ValidationError(key, "cannot be None", value)
        
        # Convert to int
        try:
            if isinstance(value, str):
                value = value.strip()
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(key, "must be a valid integer", value)
        
        # Check range constraints
        range_constraint = self.options.get('range')
        if range_constraint:
            min_val, max_val = range_constraint
            if int_value < min_val or int_value > max_val:
                raise ValidationError(key, f"must be between {min_val} and {max_val}", int_value)
        
        # Check multiple constraint
        multiple_of = self.options.get('multiple_of')
        if multiple_of and int_value % multiple_of != 0:
            raise ValidationError(key, f"must be a multiple of {multiple_of}", int_value)
        
        return int_value
    
    def get_description(self) -> str:
        desc = "integer"
        if 'range' in self.options:
            min_val, max_val = self.options['range']
            desc += f" ({min_val}-{max_val})"
        return desc


class FloatValidator(TypeValidator):
    """Float type validator."""
    
    def validate(self, key: str, value: Any) -> float:
        if value is None:
            raise ValidationError(key, "cannot be None", value)
        
        # Convert to float
        try:
            if isinstance(value, str):
                value = value.strip()
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(key, "must be a valid number", value)
        
        # Check range constraints
        range_constraint = self.options.get('range')
        if range_constraint:
            min_val, max_val = range_constraint
            if float_value < min_val or float_value > max_val:
                raise ValidationError(key, f"must be between {min_val} and {max_val}", float_value)
        
        return float_value


class BoolValidator(TypeValidator):
    """Boolean type validator."""
    
    TRUE_VALUES = {'true', '1', 'yes', 'on', 'enabled'}
    FALSE_VALUES = {'false', '0', 'no', 'off', 'disabled'}
    
    def validate(self, key: str, value: Any) -> bool:
        if value is None:
            raise ValidationError(key, "cannot be None", value)
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        if isinstance(value, str):
            str_value = value.strip().lower()
            if str_value in self.TRUE_VALUES:
                return True
            elif str_value in self.FALSE_VALUES:
                return False
        
        raise ValidationError(key, "must be a valid boolean value", value)


class ListValidator(TypeValidator):
    """List type validator."""
    
    def validate(self, key: str, value: Any) -> List[Any]:
        if value is None:
            raise ValidationError(key, "cannot be None", value)
        
        # Convert to list
        if isinstance(value, str):
            # Parse comma-separated values
            list_value = [item.strip() for item in value.split(',') if item.strip()]
        elif isinstance(value, (list, tuple)):
            list_value = list(value)
        else:
            list_value = [value]
        
        # Check length constraints
        min_items = self.options.get('min_items')
        if min_items is not None and len(list_value) < min_items:
            raise ValidationError(key, f"must have at least {min_items} items", list_value)
        
        max_items = self.options.get('max_items')
        if max_items is not None and len(list_value) > max_items:
            raise ValidationError(key, f"must have at most {max_items} items", list_value)
        
        # Validate individual items
        item_validator = self.options.get('item_validator')
        if item_validator:
            validated_items = []
            for i, item in enumerate(list_value):
                try:
                    validated_item = item_validator.validate(f"{key}[{i}]", item)
                    validated_items.append(validated_item)
                except ValidationError as e:
                    raise ValidationError(key, f"item {i}: {e.message}", item)
            list_value = validated_items
        
        # Check uniqueness
        if self.options.get('unique', False):
            if len(list_value) != len(set(list_value)):
                raise ValidationError(key, "items must be unique", list_value)
        
        return list_value


class DictValidator(TypeValidator):
    """Dictionary type validator."""
    
    def validate(self, key: str, value: Any) -> Dict[str, Any]:
        if value is None:
            raise ValidationError(key, "cannot be None", value)
        
        if not isinstance(value, dict):
            raise ValidationError(key, "must be a dictionary", value)
        
        dict_value = dict(value)
        
        # Check required keys
        required_keys = self.options.get('required_keys', [])
        for req_key in required_keys:
            if req_key not in dict_value:
                raise ValidationError(key, f"missing required key '{req_key}'", dict_value)
        
        # Check allowed keys
        allowed_keys = self.options.get('allowed_keys')
        if allowed_keys:
            for dict_key in dict_value.keys():
                if dict_key not in allowed_keys:
                    raise ValidationError(key, f"unexpected key '{dict_key}'", dict_value)
        
        return dict_value


class UrlValidator(TypeValidator):
    """URL type validator."""
    
    def validate(self, key: str, value: Any) -> str:
        if value is None:
            raise ValidationError(key, "cannot be None", value)
        
        url_str = str(value).strip()
        
        try:
            parsed = urlparse(url_str)
        except Exception:
            raise ValidationError(key, "must be a valid URL", url_str)
        
        if not parsed.scheme:
            raise ValidationError(key, "URL must have a scheme (http, https, etc.)", url_str)
        
        # Check allowed schemes
        schemes = self.options.get('schemes')
        if schemes and parsed.scheme not in schemes:
            raise ValidationError(key, f"URL scheme must be one of: {', '.join(schemes)}", url_str)
        
        # Check for localhost in production
        if self.options.get('no_localhost', False):
            if parsed.hostname in ('localhost', '127.0.0.1', '::1'):
                raise ValidationError(key, "localhost URLs not allowed", url_str)
        
        return url_str


class EmailValidator(TypeValidator):
    """Email type validator."""
    
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def validate(self, key: str, value: Any) -> str:
        if value is None:
            raise ValidationError(key, "cannot be None", value)
        
        email_str = str(value).strip()
        
        if not self.EMAIL_REGEX.match(email_str):
            raise ValidationError(key, "must be a valid email address", email_str)
        
        # Check allowed domains
        domains = self.options.get('domains')
        if domains:
            email_domain = email_str.split('@')[1]
            if email_domain not in domains:
                raise ValidationError(key, f"email domain must be one of: {', '.join(domains)}", email_str)
        
        return email_str


class PathValidator(TypeValidator):
    """File path type validator."""
    
    def validate(self, key: str, value: Any) -> str:
        if value is None:
            raise ValidationError(key, "cannot be None", value)
        
        path_str = str(value).strip()
        path = Path(path_str)
        
        # Check if file/directory exists
        if self.options.get('exists', False) and not path.exists():
            raise ValidationError(key, "path does not exist", path_str)
        
        # Check if parent directory exists
        if self.options.get('parent_exists', False) and not path.parent.exists():
            raise ValidationError(key, "parent directory does not exist", path_str)
        
        # Check if path is writable
        if self.options.get('writable', False):
            if path.exists() and not os.access(path, os.W_OK):
                raise ValidationError(key, "path is not writable", path_str)
            elif not path.exists() and not os.access(path.parent, os.W_OK):
                raise ValidationError(key, "parent directory is not writable", path_str)
        
        return path_str


class DurationValidator(TypeValidator):
    """Duration type validator (e.g., '30s', '5m', '2h', '1d')."""
    
    UNITS = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
    }
    
    def validate(self, key: str, value: Any) -> int:
        if value is None:
            raise ValidationError(key, "cannot be None", value)
        
        if isinstance(value, (int, float)):
            return int(value)
        
        duration_str = str(value).strip().lower()
        
        # Parse duration string
        match = re.match(r'^(\d+)([smhd])$', duration_str)
        if not match:
            raise ValidationError(key, "must be a valid duration (e.g., '30s', '5m', '2h', '1d')", duration_str)
        
        amount, unit = match.groups()
        seconds = int(amount) * self.UNITS[unit]
        
        # Check range constraints
        min_duration = self.options.get('min')
        if min_duration:
            min_seconds = self._parse_duration(min_duration)
            if seconds < min_seconds:
                raise ValidationError(key, f"must be at least {min_duration}", duration_str)
        
        max_duration = self.options.get('max')
        if max_duration:
            max_seconds = self._parse_duration(max_duration)
            if seconds > max_seconds:
                raise ValidationError(key, f"must be at most {max_duration}", duration_str)
        
        return seconds
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string to seconds."""
        match = re.match(r'^(\d+)([smhd])$', duration_str.lower())
        if not match:
            return 0
        amount, unit = match.groups()
        return int(amount) * self.UNITS[unit]


# Type registry
TYPE_VALIDATORS = {
    'string': StringValidator,
    'str': StringValidator,
    'int': IntValidator,
    'integer': IntValidator,
    'float': FloatValidator,
    'number': FloatValidator,
    'bool': BoolValidator,
    'boolean': BoolValidator,
    'list': ListValidator,
    'array': ListValidator,
    'dict': DictValidator,
    'dictionary': DictValidator,
    'url': UrlValidator,
    'email': EmailValidator,
    'path': PathValidator,
    'duration': DurationValidator,
}


def get_validator(type_name: str, **options) -> TypeValidator:
    """Get validator instance for given type name."""
    if type_name not in TYPE_VALIDATORS:
        raise ValueError(f"Unknown type: {type_name}")
    
    validator_class = TYPE_VALIDATORS[type_name]
    return validator_class(**options)
