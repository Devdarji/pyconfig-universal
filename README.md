# PyConfig Universal

[![PyPI version](https://badge.fury.io/py/pyconfig-universal.svg)](https://badge.fury.io/py/pyconfig-universal)
[![Python Support](https://img.shields.io/pypi/pyversions/pyconfig-universal.svg)](https://pypi.org/project/pyconfig-universal/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/pyconfig-universal/pyconfig/workflows/Tests/badge.svg)](https://github.com/pyconfig-universal/pyconfig/actions)
[![Coverage](https://codecov.io/gh/pyconfig-universal/pyconfig/branch/main/graph/badge.svg)](https://codecov.io/gh/pyconfig-universal/pyconfig)

**Universal Python Configuration Management Library**

PyConfig Universal is a comprehensive configuration management library designed to solve all configuration-related pain points in Python applications. It provides a single, unified interface for loading, validating, and managing configuration from multiple sources with type safety and environment awareness.

## 🚀 Key Features

- **Zero Configuration Setup** - Works out of the box with intelligent defaults
- **Multi-Format Support** - ENV, YAML, JSON, TOML, INI files
- **Type-Safe Validation** - Automatic type conversion with comprehensive validation
- **Environment Awareness** - Environment-specific configuration management
- **Hot Reloading** - Automatic configuration reload without application restart
- **Schema-Based Validation** - Define and validate configuration schemas
- **Auto-Documentation** - Generate configuration templates and documentation
- **Framework Integration** - Built-in support for Django, Flask, FastAPI
- **Security Features** - Secret detection, masking, and encryption support
- **CLI Tools** - Command-line tools for validation and management

## 📦 Installation

```bash
pip install pyconfig-universal
```

### Optional Dependencies

```bash
# For YAML support
pip install pyconfig-universal[yaml]

# For all features
pip install pyconfig-universal[all]
```

## 🏃‍♂️ Quick Start

### Basic Usage

```python
from pyconfig import Config

# Zero configuration setup
config = Config()

# Access configuration values
debug_mode = config.get('debug', False)
port = config.get('port', 8000)

# Attribute-style access
database_url = config.database_url
api_key = config.api_key
```

### With Schema Validation

```python
from pyconfig import Config

# Define configuration schema
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
    'database_url': {
        'type': 'url',
        'required': True,
        'schemes': ['postgresql', 'mysql'],
        'description': 'Database connection URL'
    }
}

# Create config with schema
config = Config(schema_dict=schema)

# Automatic validation and type conversion
port = config.port  # Always an integer
debug = config.debug  # Always a boolean
```

### Environment-Aware Configuration

```python
from pyconfig import Config

config = Config(
    config_files=['config.yaml'],
    environment='production',  # or auto-detect
    auto_reload=True
)

# Environment-specific validation rules
schema = {
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
```

## 📁 Configuration Sources

PyConfig Universal loads configuration from multiple sources in priority order:

1. **Command line arguments** (highest priority)
2. **Environment variables**
3. **Environment-specific config files** (`.env.production`)
4. **General config files** (`.env`, `config.yaml`)
5. **Default values** (lowest priority)

### Supported Formats

#### Environment Variables
```bash
# Simple values
DEBUG=true
PORT=8000

# Nested structures (double underscore)
DATABASE__HOST=localhost
DATABASE__PORT=5432
API__KEYS__PRIMARY=secret123
```

#### YAML Files
```yaml
database:
  host: localhost
  port: 5432
  credentials:
    username: user
    password: pass

features:
  - authentication
  - caching
  - monitoring
```

#### JSON Files (with comments)
```json
{
  // Database configuration
  "database": {
    "host": "localhost",
    "port": 5432
  },
  /* API configuration */
  "api": {
    "timeout": 30
  }
}
```

#### .env Files
```bash
# Application settings
DEBUG=true
PORT=8000

# Database
DATABASE_URL=postgresql://user:pass@localhost/db

# Nested configuration
CACHE__BACKEND=redis
CACHE__URL=redis://localhost:6379
```

## 🔧 Type System

PyConfig Universal provides comprehensive type validation:

### Basic Types
```python
# String validation
'username': {
    'type': 'string',
    'min_length': 3,
    'max_length': 50,
    'regex': r'^[a-zA-Z][a-zA-Z0-9_]*$'
}

# Integer validation
'port': {
    'type': 'int',
    'range': [1000, 65535],
    'multiple_of': 10
}

# Boolean validation (flexible input)
'debug': {
    'type': 'bool'
    # Accepts: true, false, 1, 0, yes, no, on, off
}
```

### Complex Types
```python
# List validation
'allowed_hosts': {
    'type': 'list[str]',
    'min_items': 1,
    'unique': True
}

# Dictionary validation
'database_config': {
    'type': 'dict[str, str]',
    'required_keys': ['host', 'database']
}
```

### Special Types
```python
# URL validation
'api_endpoint': {
    'type': 'url',
    'schemes': ['http', 'https']
}

# Email validation
'admin_email': {
    'type': 'email',
    'domains': ['company.com']
}

# Duration validation
'cache_ttl': {
    'type': 'duration',
    'min': '1s',
    'max': '1d'
    # Accepts: 1s, 30m, 2h, 1d, etc.
}
```

## 🔄 Hot Reloading

```python
from pyconfig import Config

def on_config_change(changed_keys, config):
    """Callback when configuration changes"""
    if 'debug' in changed_keys:
        logger.setLevel('DEBUG' if config.debug else 'INFO')

config = Config(
    auto_reload=True,
    reload_callback=on_config_change,
    watch_files=['config.yaml', '.env']
)

# Manual reload
config.reload()
```

## 📚 Documentation Generation

### Generate .env Template
```python
config = Config(schema_file='config_schema.yaml')
config.generate_env_template('.env.example')
```

Generated `.env.example`:
```bash
# Database connection URL
# Required: Yes
# Type: URL (schemes: postgresql, mysql)
# Example: postgresql://user:pass@host:5432/db
DATABASE_URL=

# Server port number
# Required: No
# Type: Integer (1000-65535)
# Default: 8000
PORT=8000
```

### Generate Documentation
```python
# Generate Markdown documentation
config.generate_docs('CONFIG.md', format='markdown')

# Generate HTML documentation
config.generate_docs('config.html', format='html')
```

## 🖥️ CLI Tools

PyConfig Universal includes powerful CLI tools:

```bash
# Validate configuration
pyconfig validate --config config.yaml --env .env

# Generate templates
pyconfig generate-env --schema config_schema.yaml --output .env.example

# Interactive configuration wizard
pyconfig init --interactive

# Check for missing configurations
pyconfig check --environment production

# Configuration diff between environments
pyconfig diff development production
```

## 🔌 Framework Integration

### Django Integration
```python
# settings.py
from pyconfig.integrations.django import DjangoConfig

config = DjangoConfig(
    schema_file='django_schema.yaml',
    environment=os.getenv('DJANGO_ENV', 'development')
)

# Automatically sets Django settings
SECRET_KEY = config.secret_key
DEBUG = config.debug
DATABASES = config.databases
```

### Flask Integration
```python
from flask import Flask
from pyconfig.integrations.flask import configure_flask

app = Flask(__name__)
config = configure_flask(app, schema_file='flask_schema.yaml')

@app.route('/')
def index():
    return f"Debug mode: {app.config['DEBUG']}"
```

### FastAPI Integration
```python
from pyconfig.integrations.fastapi import create_fastapi_app

app = create_fastapi_app(schema_file='api_schema.yaml')

@app.get('/')
def read_root():
    return {"debug": app.pyconfig.debug}
```

## 🔒 Security Features

### Secret Detection and Masking
```python
schema = {
    'api_key': {
        'type': 'string',
        'secret': True,  # Will be masked in logs
        'min_length': 32
    }
}

config = Config(schema_dict=schema)
print(repr(config))  # Shows: api_key=******
```

### Environment-Specific Security Rules
```python
schema = {
    'debug': {
        'type': 'bool',
        'environment_rules': {
            'production': {
                'forbidden_values': [True]  # Debug forbidden in production
            }
        }
    }
}
```

## 📊 Performance

- **Configuration loading**: < 10ms for typical applications
- **Memory usage**: < 5MB overhead
- **Hot reload**: < 100ms response time
- **Supports**: 10,000+ configuration keys

## 🧪 Testing

Run the test suite:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=pyconfig --cov-report=html

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Run only integration tests
```

## 📖 Examples

Check out the [examples](examples/) directory for:

- [Basic Usage](examples/basic_usage.py)
- [Schema Definition](examples/config_schema.yaml)
- [Configuration Files](examples/config.yaml)
- [Environment Variables](examples/.env)
- Framework integrations
- Advanced use cases

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/pyconfig-universal/pyconfig.git
cd pyconfig

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

PyConfig Universal was inspired by the limitations and pain points of existing configuration libraries:

- **python-dotenv**: Limited to .env format, no type conversion
- **django-environ**: Django-specific, complex list parsing
- **dynaconf**: Heavy dependencies, incomplete schema validation
- **pydantic-settings**: Requires Pydantic knowledge, verbose setup

## 📞 Support

- **Documentation**: [https://pyconfig-universal.readthedocs.io](https://pyconfig-universal.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/pyconfig-universal/pyconfig/issues)
- **Discussions**: [GitHub Discussions](https://github.com/pyconfig-universal/pyconfig/discussions)
- **Stack Overflow**: Tag your questions with `pyconfig-universal`

## 🗺️ Roadmap

- [ ] Plugin system for custom loaders
- [ ] Remote configuration sources (Redis, Consul, AWS Parameter Store)
- [ ] Configuration encryption at rest
- [ ] Web UI for configuration management
- [ ] Integration with more frameworks (Tornado, Sanic, etc.)
- [ ] Configuration versioning and rollback
- [ ] Audit trail and access logging

---

**Made with ❤️ by the PyConfig Universal team**
