"""Tests for schema validation system."""

import tempfile
import pytest
from pathlib import Path

from pyconfig.core.schema import Schema
from pyconfig.core.exceptions import ConfigValidationError, ValidationError


class TestSchema:
    """Test cases for Schema class."""
    
    def test_basic_schema_validation(self):
        """Test basic schema validation."""
        schema_dict = {
            'port': {
                'type': 'int',
                'required': True,
                'range': [1000, 65535]
            },
            'debug': {
                'type': 'bool',
                'default': False
            },
            'name': {
                'type': 'string',
                'required': True,
                'min_length': 3
            }
        }
        
        schema = Schema(schema_dict)
        
        # Valid configuration
        config_data = {
            'port': 8000,
            'debug': True,
            'name': 'myapp'
        }
        
        validated = schema.validate(config_data)
        assert validated['port'] == 8000
        assert validated['debug'] is True
        assert validated['name'] == 'myapp'
    
    def test_schema_with_defaults(self):
        """Test schema validation with default values."""
        schema_dict = {
            'port': {
                'type': 'int',
                'default': 8000
            },
            'debug': {
                'type': 'bool',
                'default': False
            }
        }
        
        schema = Schema(schema_dict)
        
        # Empty configuration should use defaults
        validated = schema.validate({})
        assert validated['port'] == 8000
        assert validated['debug'] is False
    
    def test_schema_required_fields(self):
        """Test schema validation with required fields."""
        schema_dict = {
            'api_key': {
                'type': 'string',
                'required': True
            }
        }
        
        schema = Schema(schema_dict)
        
        # Missing required field should raise error
        with pytest.raises(ConfigValidationError) as exc_info:
            schema.validate({})
        
        assert 'api_key' in str(exc_info.value)
        assert 'required' in str(exc_info.value)
    
    def test_schema_type_conversion(self):
        """Test schema type conversion."""
        schema_dict = {
            'port': {'type': 'int'},
            'debug': {'type': 'bool'},
            'timeout': {'type': 'float'},
            'features': {'type': 'list'}
        }
        
        schema = Schema(schema_dict)
        
        config_data = {
            'port': '8000',  # String to int
            'debug': 'true',  # String to bool
            'timeout': '30.5',  # String to float
            'features': 'auth,cache,logging'  # String to list
        }
        
        validated = schema.validate(config_data)
        assert validated['port'] == 8000
        assert validated['debug'] is True
        assert validated['timeout'] == 30.5
        assert validated['features'] == ['auth', 'cache', 'logging']
    
    def test_schema_nested_types(self):
        """Test schema with nested list types."""
        schema_dict = {
            'allowed_hosts': {
                'type': 'list[str]',
                'min_items': 1
            }
        }
        
        schema = Schema(schema_dict)
        
        config_data = {
            'allowed_hosts': ['localhost', '127.0.0.1']
        }
        
        validated = schema.validate(config_data)
        assert validated['allowed_hosts'] == ['localhost', '127.0.0.1']
    
    def test_schema_environment_rules(self):
        """Test environment-specific validation rules."""
        schema_dict = {
            'debug': {
                'type': 'bool',
                'default': True,
                'environment_rules': {
                    'production': {
                        'default': False,
                        'forbidden_values': [True]
                    }
                }
            }
        }
        
        schema = Schema(schema_dict)
        
        # Development environment allows debug=True
        validated = schema.validate({'debug': True}, environment='development')
        assert validated['debug'] is True
        
        # Production environment forbids debug=True
        with pytest.raises(ConfigValidationError):
            schema.validate({'debug': True}, environment='production')
        
        # Production environment uses different default
        validated = schema.validate({}, environment='production')
        assert validated['debug'] is False
    
    def test_schema_validation_errors(self):
        """Test schema validation error handling."""
        schema_dict = {
            'port': {
                'type': 'int',
                'range': [1000, 65535]
            },
            'email': {
                'type': 'email'
            }
        }
        
        schema = Schema(schema_dict)
        
        config_data = {
            'port': 99,  # Invalid range
            'email': 'invalid_email'  # Invalid email
        }
        
        with pytest.raises(ConfigValidationError) as exc_info:
            schema.validate(config_data)
        
        error_message = str(exc_info.value)
        assert 'port' in error_message
        assert 'email' in error_message
    
    def test_get_field_info(self):
        """Test getting field information."""
        schema_dict = {
            'port': {
                'type': 'int',
                'default': 8000,
                'required': True,
                'description': 'Server port number',
                'examples': ['8000', '3000']
            }
        }
        
        schema = Schema(schema_dict)
        field_info = schema.get_field_info('port')
        
        assert field_info['type'] == 'int'
        assert field_info['default'] == 8000
        assert field_info['required'] is True
        assert field_info['description'] == 'Server port number'
        assert field_info['examples'] == ['8000', '3000']
    
    def test_generate_env_template(self):
        """Test generating .env template."""
        schema_dict = {
            'port': {
                'type': 'int',
                'default': 8000,
                'description': 'Server port number'
            },
            'api_key': {
                'type': 'string',
                'required': True,
                'description': 'API authentication key'
            }
        }
        
        schema = Schema(schema_dict)
        template = schema.generate_env_template()
        
        assert 'Server port number' in template
        assert 'PORT=8000' in template
        assert 'API authentication key' in template
        assert 'API_KEY=' in template
        assert 'Required: Yes' in template
        assert 'Required: No' in template
    
    def test_generate_markdown_docs(self):
        """Test generating Markdown documentation."""
        schema_dict = {
            'port': {
                'type': 'int',
                'default': 8000,
                'description': 'Server port number',
                'examples': ['8000', '3000']
            }
        }
        
        schema = Schema(schema_dict)
        docs = schema.generate_docs('markdown')
        
        assert '# Configuration Reference' in docs
        assert '## port' in docs
        assert 'Server port number' in docs
        assert '**Type:** integer' in docs
        assert '**Default:** `8000`' in docs
        assert '`8000`' in docs
        assert '`3000`' in docs
    
    def test_generate_html_docs(self):
        """Test generating HTML documentation."""
        schema_dict = {
            'port': {
                'type': 'int',
                'default': 8000,
                'description': 'Server port number'
            }
        }
        
        schema = Schema(schema_dict)
        docs = schema.generate_docs('html')
        
        assert '<!DOCTYPE html>' in docs
        assert '<title>Configuration Reference</title>' in docs
        assert '<h2>port</h2>' in docs
        assert 'Server port number' in docs
        assert '<strong>Type:</strong> integer' in docs
        assert '<code>8000</code>' in docs
    
    def test_schema_from_yaml_file(self):
        """Test loading schema from YAML file."""
        pytest.importorskip("yaml")
        
        schema_content = """
port:
  type: int
  default: 8000
  description: Server port

debug:
  type: bool
  default: false
  description: Debug mode
"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / 'schema.yaml'
            schema_file.write_text(schema_content)
            
            schema = Schema.from_file(str(schema_file))
            
            assert 'port' in schema.schema_dict
            assert 'debug' in schema.schema_dict
            assert schema.schema_dict['port']['type'] == 'int'
            assert schema.schema_dict['port']['default'] == 8000
    
    def test_schema_from_json_file(self):
        """Test loading schema from JSON file."""
        schema_content = '''
{
  "port": {
    "type": "int",
    "default": 8000,
    "description": "Server port"
  },
  "debug": {
    "type": "bool",
    "default": false,
    "description": "Debug mode"
  }
}
'''
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / 'schema.json'
            schema_file.write_text(schema_content)
            
            schema = Schema.from_file(str(schema_file))
            
            assert 'port' in schema.schema_dict
            assert 'debug' in schema.schema_dict
            assert schema.schema_dict['port']['type'] == 'int'
            assert schema.schema_dict['port']['default'] == 8000
    
    def test_unknown_fields_validation(self):
        """Test validation of unknown fields."""
        schema_dict = {
            'port': {'type': 'int'}
        }
        
        schema = Schema(schema_dict)
        
        config_data = {
            'port': 8000,
            'unknown_field': 'value'  # Not in schema
        }
        
        with pytest.raises(ConfigValidationError) as exc_info:
            schema.validate(config_data)
        
        assert 'unknown_field' in str(exc_info.value)
        assert 'unknown configuration key' in str(exc_info.value)
