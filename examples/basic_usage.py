"""Basic usage example for PyConfig Universal."""

from pyconfig import Config

# Basic usage - zero configuration
config = Config()

# Access configuration values
debug_mode = config.get('debug', False)
port = config.get('port', 8000)

print(f"Debug mode: {debug_mode}")
print(f"Server port: {port}")

# Attribute-style access
if hasattr(config, 'database_url'):
    print(f"Database URL: {config.database_url}")

# With schema validation
schema_dict = {
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
    'database_url': {
        'type': 'url',
        'required': True,
        'schemes': ['postgresql', 'mysql'],
        'description': 'Database connection URL'
    }
}

# Create config with schema
config_with_schema = Config(schema_dict=schema_dict)

# Validate configuration
try:
    config_with_schema.validate()
    print("✓ Configuration is valid")
except Exception as e:
    print(f"✗ Configuration error: {e}")

# Generate .env template
config_with_schema.generate_env_template('.env.example')
print("Generated .env.example file")

# Generate documentation
config_with_schema.generate_docs('CONFIG.md')
print("Generated CONFIG.md documentation")


# load .env file
config = Config(config_files=['.env'], schema_file='config_schema.yaml')
print(config, type(config), config.get("debug"), type(config.get("debug")))