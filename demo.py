#!/usr/bin/env python3
"""
Comprehensive demo of PyConfig Universal features.
"""

import os
import tempfile
from pathlib import Path
from pyconfig import Config

def demo_basic_usage():
    """Demo basic configuration usage."""
    print("🚀 PyConfig Universal - Comprehensive Demo")
    print("=" * 50)
    
    print("\n1. Basic Usage:")
    print("-" * 20)
    
    # Set some environment variables
    os.environ['DEBUG'] = 'true'
    os.environ['PORT'] = '8000'
    os.environ['DATABASE__HOST'] = 'localhost'
    os.environ['DATABASE__PORT'] = '5432'
    
    config = Config()
    print(f"✓ Debug mode: {config.get('debug')}")
    print(f"✓ Server port: {config.get('port')}")
    print(f"✓ Database host: {config.get('database.host')}")
    print(f"✓ Database port: {config.get('database.port')}")

def demo_schema_validation():
    """Demo schema validation."""
    print("\n2. Schema Validation:")
    print("-" * 20)
    
    schema = {
        'port': {
            'type': 'int',
            'default': 8000,
            'range': [1000, 65535],
            'description': 'Server port number'
        },
        'debug': {
            'type': 'bool',
            'default': False,
            'description': 'Enable debug mode'
        },
        'features': {
            'type': 'list[str]',
            'default': ['auth', 'cache'],
            'description': 'Enabled features'
        }
    }
    
    config = Config(schema_dict=schema)
    print(f"✓ Port (typed): {config.port} ({type(config.port)})")
    print(f"✓ Debug (typed): {config.debug} ({type(config.debug)})")
    print(f"✓ Features (typed): {config.features} ({type(config.features)})")

def demo_file_loading():
    """Demo file-based configuration loading."""
    print("\n3. File-Based Configuration:")
    print("-" * 30)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create YAML config
        yaml_file = Path(tmpdir) / 'config.yaml'

        yaml_content = """
            app:
            name: "MyApp"
            version: "1.0.0"

            database:
            host: "localhost"
            port: 5432
            name: "myapp_db"

            features:
            - authentication
            - caching
            - monitoring
        """
        yaml_file.write_text(yaml_content)
        
        # Create .env file
        env_file = Path(tmpdir) / '.env'
        env_file.write_text('SECRET_KEY=my-secret-key\nDEBUG=false')
        
        config = Config(config_files=[str(yaml_file), str(env_file)])

        print("Loaded configuration:", config)

        print(f"✓ App name: {config.get('app.name')}")
        print(f"✓ App version: {config.get('app.version')}")
        print(f"✓ Database: {config.get('database.host')}:{config.get('database.port')}")
        print(f"✓ Features: {config.get('features')}")
        print(f"✓ Secret key: {config.get('secret_key', 'Not set')}")

def demo_environment_awareness():
    """Demo environment-aware configuration."""
    print("\n4. Environment-Aware Configuration:")
    print("-" * 35)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create base config
        base_file = Path(tmpdir) / 'config.yaml'
        base_file.write_text('debug: true\nport: 8000\nlog_level: DEBUG')
        
        # Create production config
        prod_file = Path(tmpdir) / 'config.production.yaml'
        prod_file.write_text('debug: false\nlog_level: INFO')
        
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Development environment
            dev_config = Config(environment='development')
            print(f"✓ Development - Debug: {dev_config.get('debug')}, Log: {dev_config.get('log_level')}")
            
            # Production environment
            prod_config = Config(environment='production')
            print(f"✓ Production - Debug: {prod_config.get('debug')}, Log: {prod_config.get('log_level')}")
        finally:
            os.chdir(old_cwd)

def demo_template_generation():
    """Demo template and documentation generation."""
    print("\n5. Template & Documentation Generation:")
    print("-" * 40)
    
    schema = {
        'port': {
            'type': 'int',
            'default': 8000,
            'description': 'Server port number',
            'examples': ['8000', '3000']
        },
        'database_url': {
            'type': 'url',
            'required': True,
            'description': 'Database connection URL',
            'examples': ['postgresql://user:pass@host/db']
        }
    }
    
    config = Config(schema_dict=schema)
    
    # Generate .env template
    config.generate_env_template('demo.env')
    print("✓ Generated .env template (demo.env)")
    
    # Generate documentation
    config.generate_docs('demo_config.md')
    print("✓ Generated documentation (demo_config.md)")

def demo_type_validation():
    """Demo comprehensive type validation."""
    print("\n6. Type Validation:")
    print("-" * 20)
    
    # Set various typed environment variables
    os.environ['API_TIMEOUT'] = '30s'
    os.environ['MAX_CONNECTIONS'] = '100'
    os.environ['ADMIN_EMAIL'] = 'admin@example.com'
    os.environ['API_URL'] = 'https://api.example.com'
    
    schema = {
        'api_timeout': {
            'type': 'duration',
            'description': 'API timeout duration'
        },
        'max_connections': {
            'type': 'int',
            'range': [1, 1000],
            'description': 'Maximum connections'
        },
        'admin_email': {
            'type': 'email',
            'description': 'Administrator email'
        },
        'api_url': {
            'type': 'url',
            'schemes': ['https'],
            'description': 'API endpoint URL'
        }
    }
    
    config = Config(schema_dict=schema)
    print(f"✓ API timeout: {config.api_timeout} seconds")
    print(f"✓ Max connections: {config.max_connections}")
    print(f"✓ Admin email: {config.admin_email}")
    print(f"✓ API URL: {config.api_url}")

def demo_security_features():
    """Demo security features."""
    print("\n7. Security Features:")
    print("-" * 20)
    
    os.environ['SECRET_KEY'] = 'super-secret-key-123'
    os.environ['API_TOKEN'] = 'secret-api-token-456'
    
    config = Config()
    print(f"✓ Configuration representation (secrets masked):")
    print(f"  {repr(config)}")

def cleanup():
    """Clean up environment variables."""
    env_vars_to_clean = [
        'DEBUG', 'PORT', 'DATABASE__HOST', 'DATABASE__PORT',
        'API_TIMEOUT', 'MAX_CONNECTIONS', 'ADMIN_EMAIL', 'API_URL',
        'SECRET_KEY', 'API_TOKEN'
    ]
    
    for var in env_vars_to_clean:
        if var in os.environ:
            del os.environ[var]

if __name__ == '__main__':
    try:
        demo_basic_usage()
        demo_schema_validation()
        demo_file_loading()
        demo_environment_awareness()
        demo_template_generation()
        demo_type_validation()
        demo_security_features()
        
        print("\n🎉 Demo completed successfully!")
        print("\nGenerated files:")
        print("- demo.env (environment template)")
        print("- demo_config.md (configuration documentation)")
        
    finally:
        cleanup()
