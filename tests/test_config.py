"""Tests for the main Config class."""

import os
import tempfile
import pytest
from pathlib import Path

from pyconfig import Config
from pyconfig.core.exceptions import ConfigValidationError, ConfigNotFoundError


class TestConfig:
    """Test cases for Config class."""
    
    def test_empty_config(self):
        """Test creating empty configuration."""
        config = Config()
        assert config.to_dict() == {}
    
    def test_environment_detection(self):
        """Test automatic environment detection."""
        # Test with ENVIRONMENT variable
        os.environ['ENVIRONMENT'] = 'testing'
        config = Config()
        assert config._environment == 'testing'
        del os.environ['ENVIRONMENT']
    
    def test_env_variable_loading(self):
        """Test loading from environment variables."""
        os.environ['TEST_KEY'] = 'test_value'
        os.environ['NESTED__KEY'] = 'nested_value'
        
        config = Config()
        
        assert config.get('test_key') == 'test_value'
        assert config.get('nested.key') == 'nested_value'
        
        # Cleanup
        del os.environ['TEST_KEY']
        del os.environ['NESTED__KEY']
    
    def test_file_loading(self):
        """Test loading from configuration files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test .env file
            env_file = Path(tmpdir) / '.env'
            env_file.write_text('TEST_KEY=file_value\nDEBUG=true')
            
            config = Config(config_files=[str(env_file)])
            
            assert config.get('test_key') == 'file_value'
            assert config.get('debug') == 'true'
    
    def test_yaml_loading(self):
        """Test loading from YAML files."""
        pytest.importorskip("yaml")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / 'config.yaml'
            yaml_content = """
database:
  host: localhost
  port: 5432
debug: true
features:
  - auth
  - cache
"""
            yaml_file.write_text(yaml_content)
            
            config = Config(config_files=[str(yaml_file)])
            
            assert config.get('database.host') == 'localhost'
            assert config.get('database.port') == 5432
            assert config.get('debug') is True
            assert config.get('features') == ['auth', 'cache']
    
    def test_json_loading(self):
        """Test loading from JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / 'config.json'
            json_content = '''
{
  // This is a comment
  "database": {
    "host": "localhost",
    "port": 5432
  },
  "debug": true,
  /* Multi-line comment */
  "features": ["auth", "cache"]
}
'''
            json_file.write_text(json_content)
            
            config = Config(config_files=[str(json_file)])
            
            assert config.get('database.host') == 'localhost'
            assert config.get('database.port') == 5432
            assert config.get('debug') is True
            assert config.get('features') == ['auth', 'cache']
    
    def test_priority_order(self):
        """Test configuration priority order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config file
            config_file = Path(tmpdir) / '.env'
            config_file.write_text('TEST_KEY=file_value')
            
            # Set environment variable (higher priority)
            os.environ['TEST_KEY'] = 'env_value'
            
            config = Config(config_files=[str(config_file)])
            
            # Environment variable should override file
            assert config.get('test_key') == 'env_value'
            
            # Cleanup
            del os.environ['TEST_KEY']
    
    def test_schema_validation(self):
        """Test schema validation."""
        schema_dict = {
            'port': {
                'type': 'int',
                'required': True,
                'range': [1000, 65535]
            },
            'debug': {
                'type': 'bool',
                'default': False
            }
        }
        
        # Valid configuration
        os.environ['PORT'] = '8000'
        config = Config(schema_dict=schema_dict)
        assert config.get('port') == 8000
        assert config.get('debug') is False
        
        # Invalid configuration
        os.environ['PORT'] = '99'  # Below minimum
        with pytest.raises(ConfigValidationError):
            Config(schema_dict=schema_dict, strict_mode=True)
        
        # Cleanup
        del os.environ['PORT']
    
    def test_nested_access(self):
        """Test nested configuration access."""
        config_data = {
            'database': {
                'host': 'localhost',
                'credentials': {
                    'username': 'user',
                    'password': 'pass'
                }
            }
        }
        
        # Mock the config data
        config = Config()
        config._config_data = config_data
        
        assert config.get('database.host') == 'localhost'
        assert config.get('database.credentials.username') == 'user'
        assert config.get('nonexistent.key', 'default') == 'default'
    
    def test_attribute_access(self):
        """Test attribute-style access."""
        config = Config()
        config._config_data = {'debug': True, 'port': 8000}
        
        assert config.debug is True
        assert config.port == 8000
        
        with pytest.raises(AttributeError):
            _ = config.nonexistent_key
    
    def test_set_configuration(self):
        """Test setting configuration values."""
        config = Config()
        
        config.set('debug', True)
        config.set('database.host', 'localhost')
        
        assert config.get('debug') is True
        assert config.get('database.host') == 'localhost'
    
    def test_configuration_reload(self):
        """Test configuration reloading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / '.env'
            config_file.write_text('TEST_KEY=initial_value')
            
            config = Config(config_files=[str(config_file)])
            assert config.get('test_key') == 'initial_value'
            
            # Update file
            config_file.write_text('TEST_KEY=updated_value')
            config.reload()
            
            assert config.get('test_key') == 'updated_value'
    
    def test_environment_specific_files(self):
        """Test environment-specific configuration files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Base config
            base_file = Path(tmpdir) / 'config.yaml'
            base_file.write_text('debug: false\nport: 8000')
            
            # Development config
            dev_file = Path(tmpdir) / 'config.development.yaml'
            dev_file.write_text('debug: true')
            
            config = Config(
                config_files=[str(base_file)],
                environment='development'
            )
            
            # Development should override base
            assert config.get('debug') is True
            assert config.get('port') == 8000
    
    def test_sensitive_key_masking(self):
        """Test masking of sensitive configuration keys."""
        config = Config()
        config._config_data = {
            'api_key': 'secret123',
            'password': 'mypass',
            'debug': True
        }
        
        repr_str = repr(config)
        assert 'secret123' not in repr_str
        assert 'mypass' not in repr_str
        assert '******' in repr_str
        assert 'debug' in repr_str
    
    def test_context_manager(self):
        """Test using Config as context manager."""
        with Config() as config:
            assert isinstance(config, Config)
        # Should not raise any exceptions
    
    def test_required_field_error(self):
        """Test error for missing required fields."""
        schema_dict = {
            'required_field': {
                'type': 'string',
                'required': True
            }
        }
        
        config = Config(schema_dict=schema_dict)
        
        with pytest.raises(ConfigNotFoundError):
            config.get('required_field')
    
    def test_generate_env_template(self):
        """Test generating .env template."""
        schema_dict = {
            'port': {
                'type': 'int',
                'default': 8000,
                'description': 'Server port'
            },
            'debug': {
                'type': 'bool',
                'default': False,
                'description': 'Debug mode'
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            template_file = Path(tmpdir) / '.env.example'
            
            config = Config(schema_dict=schema_dict)
            config.generate_env_template(str(template_file))
            
            content = template_file.read_text()
            assert 'Server port' in content
            assert 'PORT=8000' in content
            assert 'DEBUG=False' in content
