"""Configuration schema definition and validation."""

import os
from typing import Any, Dict, List, Optional, Union
from .exceptions import ValidationError, ConfigValidationError, ConfigSchemaError
from .types import get_validator, TypeValidator


class Schema:
    """Configuration schema for validation and documentation."""
    
    def __init__(self, schema_dict: Dict[str, Any]):
        """Initialize schema from dictionary definition."""
        self.schema_dict = schema_dict
        self._validators = {}
        self._build_validators()
    
    def _build_validators(self) -> None:
        """Build type validators from schema definition."""
        for key, field_def in self.schema_dict.items():
            if isinstance(field_def, dict):
                validator = self._build_field_validator(key, field_def)
                if validator is not None:
                    self._validators[key] = validator
    
    def _build_field_validator(self, key: str, field_def: Dict[str, Any]) -> TypeValidator:
        """Build validator for a single field."""
        field_type = field_def.get('type', 'string')
        
        # Handle group types (nested configuration)
        if field_type == 'group':
            # For groups, we don't need a validator as they're handled differently
            return None
        
        # Handle nested list types (e.g., 'list[str]')
        if '[' in field_type and field_type.endswith(']'):
            base_type, item_type = field_type.split('[', 1)
            item_type = item_type.rstrip(']')
            
            if base_type == 'list':
                item_validator = get_validator(item_type)
                return get_validator('list', item_validator=item_validator, **field_def)
        
        # Handle nested dict types (e.g., 'dict[str, int]')
        if field_type.startswith('dict[') and field_type.endswith(']'):
            return get_validator('dict', **field_def)
        
        # Regular type validation
        validator_options = {k: v for k, v in field_def.items() if k != 'type'}
        return get_validator(field_type, **validator_options)
    
    def validate(self, config_data: Dict[str, Any], environment: Optional[str] = None, strict: bool = True) -> Dict[str, Any]:
        """Validate configuration data against schema."""
        errors = []
        validated_config = {}
        
        # First, add all schema fields with defaults
        for key, field_def in self.schema_dict.items():
            try:
                value = self._validate_field(key, field_def, config_data, environment)
                validated_config[key] = value
            except ValidationError as e:
                errors.append(e)
        
        # Check for unknown fields only in strict mode
        if strict:
            schema_keys = set(self.schema_dict.keys())
            config_keys = set(config_data.keys())
            unknown_keys = config_keys - schema_keys
            
            for unknown_key in unknown_keys:
                errors.append(ValidationError(
                    unknown_key, 
                    "unknown configuration key (not defined in schema)"
                ))
        
        if errors:
            raise ConfigValidationError(errors)
        
        return validated_config
    
    def _validate_field(self, key: str, field_def: Dict[str, Any], 
                       config_data: Dict[str, Any], environment: Optional[str]) -> Any:
        """Validate a single field."""
        # Check environment-specific rules
        env_rules = field_def.get('environment_rules', {})
        if environment and environment in env_rules:
            # Merge environment-specific rules
            field_def = {**field_def, **env_rules[environment]}
        
        # Get value from config data
        value = config_data.get(key)
        
        # Handle required fields
        required = field_def.get('required', False)
        if required and value is None:
            raise ValidationError(key, "is required but not provided")
        
        # Handle default values
        if value is None:
            default = field_def.get('default')
            if default is not None:
                value = default
            elif not required:
                return default  # Return default even if None for optional fields
        
        # If still None and not required, return None
        if value is None and not required:
            return None
        
        # Check forbidden values (for environment-specific restrictions)
        forbidden_values = field_def.get('forbidden_values', [])
        if value in forbidden_values:
            raise ValidationError(key, f"value {value!r} is not allowed in {environment} environment")
        
        # Validate using type validator
        if key in self._validators:
            validator = self._validators[key]
            return validator.validate(key, value)
        
        return value
    
    def get_field_info(self, key: str) -> Dict[str, Any]:
        """Get information about a schema field."""
        if key not in self.schema_dict:
            raise ConfigSchemaError(f"Field '{key}' not found in schema")
        
        field_def = self.schema_dict[key]
        validator = self._validators.get(key)
        
        info = {
            'type': field_def.get('type', 'string'),
            'required': field_def.get('required', False),
            'default': field_def.get('default'),
            'description': field_def.get('description', ''),
            'examples': field_def.get('examples', []),
        }
        
        if validator:
            info['type_description'] = validator.get_description()
        
        return info
    
    def get_all_fields(self) -> List[str]:
        """Get list of all field names in schema."""
        return list(self.schema_dict.keys())
    
    def generate_env_template(self) -> str:
        """Generate .env template from schema."""
        lines = []
        
        def add_field_template(key: str, field_def: Dict[str, Any], prefix: str = ''):
            """Add template for a single field."""
            field_type = field_def.get('type', 'string')
            
            if field_type == 'group':
                # Handle group fields
                group_fields = field_def.get('fields', {})
                lines.append(f"# {field_def.get('description', f'{key} configuration')}")
                lines.append("")
                
                for sub_key, sub_field_def in group_fields.items():
                    full_key = f"{prefix}{key}__{sub_key}" if prefix else f"{key}__{sub_key}"
                    add_field_template(sub_key, sub_field_def, f"{prefix}{key}__")
                return
            
            # Add description as comment
            description = field_def.get('description', '')
            if description:
                lines.append(f"# {description}")
            
            # Add field info
            field_info = self.get_field_info(key) if key in self.schema_dict else {
                'type': field_type,
                'required': field_def.get('required', False),
                'default': field_def.get('default'),
                'examples': field_def.get('examples', [])
            }
            
            lines.append(f"# Required: {'Yes' if field_info['required'] else 'No'}")
            lines.append(f"# Type: {field_info.get('type_description', field_info['type'])}")
            
            if field_info['default'] is not None:
                lines.append(f"# Default: {field_info['default']}")
            
            examples = field_info.get('examples', [])
            if examples:
                lines.append(f"# Example: {examples[0]}")
            
            # Add environment variable
            env_key = f"{prefix}{key}".upper().replace('.', '_').replace('-', '_')
            default_value = field_info['default'] if field_info['default'] is not None else ''
            lines.append(f"{env_key}={default_value}")
            lines.append("")  # Empty line for readability
        
        for key, field_def in self.schema_dict.items():
            add_field_template(key, field_def)
        
        return "\n".join(lines)
    
    def generate_docs(self, format: str = 'markdown') -> str:
        """Generate documentation from schema."""
        if format == 'markdown':
            return self._generate_markdown_docs()
        elif format == 'html':
            return self._generate_html_docs()
        else:
            raise ValueError(f"Unsupported documentation format: {format}")
    
    def _generate_markdown_docs(self) -> str:
        """Generate Markdown documentation."""
        lines = [
            "# Configuration Reference",
            "",
            "This document describes all available configuration options.",
            "",
        ]
        
        for key, field_def in self.schema_dict.items():
            field_info = self.get_field_info(key)
            
            lines.append(f"## {key}")
            lines.append("")
            
            if field_info['description']:
                lines.append(field_info['description'])
                lines.append("")
            
            lines.append("**Details:**")
            lines.append(f"- **Type:** {field_info.get('type_description', field_info['type'])}")
            lines.append(f"- **Required:** {'Yes' if field_info['required'] else 'No'}")
            
            if field_info['default'] is not None:
                lines.append(f"- **Default:** `{field_info['default']}`")
            
            examples = field_info.get('examples', [])
            if examples:
                lines.append("- **Examples:**")
                for example in examples:
                    lines.append(f"  - `{example}`")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_html_docs(self) -> str:
        """Generate HTML documentation."""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Configuration Reference</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "h1 { color: #333; }",
            "h2 { color: #666; border-bottom: 1px solid #eee; }",
            ".field { margin-bottom: 30px; }",
            ".details { background: #f5f5f5; padding: 15px; border-radius: 5px; }",
            "code { background: #e8e8e8; padding: 2px 4px; border-radius: 3px; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Configuration Reference</h1>",
            "<p>This document describes all available configuration options.</p>",
        ]
        
        for key, field_def in self.schema_dict.items():
            field_info = self.get_field_info(key)
            
            html_parts.extend([
                f'<div class="field">',
                f'<h2>{key}</h2>',
            ])
            
            if field_info['description']:
                html_parts.append(f'<p>{field_info["description"]}</p>')
            
            html_parts.extend([
                '<div class="details">',
                f'<strong>Type:</strong> {field_info.get("type_description", field_info["type"])}<br>',
                f'<strong>Required:</strong> {"Yes" if field_info["required"] else "No"}<br>',
            ])
            
            if field_info['default'] is not None:
                html_parts.append(f'<strong>Default:</strong> <code>{field_info["default"]}</code><br>')
            
            examples = field_info.get('examples', [])
            if examples:
                html_parts.append('<strong>Examples:</strong><br>')
                for example in examples:
                    html_parts.append(f'&nbsp;&nbsp;• <code>{example}</code><br>')
            
            html_parts.extend([
                '</div>',
                '</div>',
            ])
        
        html_parts.extend([
            "</body>",
            "</html>",
        ])
        
        return "\n".join(html_parts)
    
    @classmethod
    def from_file(cls, file_path: str) -> 'Schema':
        """Load schema from file."""
        import yaml
        
        with open(file_path, 'r') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                schema_dict = yaml.safe_load(f)
            elif file_path.endswith('.json'):
                import json
                schema_dict = json.load(f)
            else:
                raise ConfigSchemaError(f"Unsupported schema file format: {file_path}")
        
        return cls(schema_dict)
