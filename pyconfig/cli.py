"""Command-line interface for PyConfig Universal."""

import os
import sys
import click
from pathlib import Path
from typing import Optional

from .core.config import Config
from .core.schema import Schema
from .core.exceptions import ConfigError


@click.group()
@click.version_option(version='1.0.0')
def main():
    """PyConfig Universal - Universal Python Configuration Management Library."""
    pass


@main.command()
@click.option('--config', '-c', multiple=True, help='Configuration files to validate')
@click.option('--schema', '-s', help='Schema file for validation')
@click.option('--environment', '-e', help='Environment to validate for')
@click.option('--strict', is_flag=True, help='Enable strict validation mode')
def validate(config, schema, environment, strict):
    """Validate configuration files against schema."""
    try:
        # Load configuration
        config_files = list(config) if config else None
        
        config_obj = Config(
            schema_file=schema,
            config_files=config_files,
            environment=environment,
            strict_mode=strict
        )
        
        # Validate
        config_obj.validate()
        
        click.echo(click.style("✓ Configuration validation passed", fg='green'))
        
        # Show loaded configuration summary
        config_dict = config_obj.to_dict()
        click.echo(f"\nLoaded {len(config_dict)} configuration keys:")
        for key in sorted(config_dict.keys()):
            click.echo(f"  - {key}")
    
    except ConfigError as e:
        click.echo(click.style(f"✗ Configuration validation failed:", fg='red'))
        click.echo(str(e))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"✗ Unexpected error: {e}", fg='red'))
        sys.exit(1)


@main.command('generate-env')
@click.option('--schema', '-s', required=True, help='Schema file to generate from')
@click.option('--output', '-o', default='.env.example', help='Output file path')
def generate_env(schema, output):
    """Generate .env template from schema."""
    try:
        schema_obj = Schema.from_file(schema)
        template_content = schema_obj.generate_env_template()
        
        with open(output, 'w') as f:
            f.write(template_content)
        
        click.echo(click.style(f"✓ Generated .env template: {output}", fg='green'))
    
    except Exception as e:
        click.echo(click.style(f"✗ Failed to generate template: {e}", fg='red'))
        sys.exit(1)


@main.command('generate-docs')
@click.option('--schema', '-s', required=True, help='Schema file to generate from')
@click.option('--output', '-o', default='CONFIG.md', help='Output file path')
@click.option('--format', '-f', type=click.Choice(['markdown', 'html']), 
              default='markdown', help='Documentation format')
def generate_docs(schema, output, format):
    """Generate configuration documentation from schema."""
    try:
        schema_obj = Schema.from_file(schema)
        docs_content = schema_obj.generate_docs(format)
        
        with open(output, 'w') as f:
            f.write(docs_content)
        
        click.echo(click.style(f"✓ Generated documentation: {output}", fg='green'))
    
    except Exception as e:
        click.echo(click.style(f"✗ Failed to generate documentation: {e}", fg='red'))
        sys.exit(1)


@main.command()
@click.option('--interactive', '-i', is_flag=True, help='Interactive configuration wizard')
@click.option('--schema', '-s', help='Schema file to use as template')
def init(interactive, schema):
    """Initialize configuration files for a new project."""
    if interactive:
        _interactive_init(schema)
    else:
        _quick_init(schema)


def _interactive_init(schema_file: Optional[str]):
    """Interactive configuration initialization."""
    click.echo("🚀 PyConfig Universal - Interactive Setup")
    click.echo("=" * 40)
    
    # Ask for project details
    project_name = click.prompt("Project name", default="my-project")
    environment = click.prompt("Default environment", default="development")
    
    # Choose configuration format
    config_format = click.prompt(
        "Configuration format",
        type=click.Choice(['yaml', 'json', 'toml', 'env']),
        default='yaml'
    )
    
    # Create basic configuration files
    if config_format == 'yaml':
        config_content = f"""# {project_name} Configuration
environment: {environment}
debug: true

database:
  host: localhost
  port: 5432
  name: {project_name.replace('-', '_')}

api:
  host: 0.0.0.0
  port: 8000
  timeout: 30
"""
        with open('config.yaml', 'w') as f:
            f.write(config_content)
        click.echo("✓ Created config.yaml")
    
    elif config_format == 'env':
        env_content = f"""# {project_name} Environment Configuration
ENVIRONMENT={environment}
DEBUG=true

# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME={project_name.replace('-', '_')}

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_TIMEOUT=30
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        click.echo("✓ Created .env")
    
    # Create basic schema if requested
    if click.confirm("Create configuration schema?", default=True):
        schema_content = """environment:
  type: string
  default: development
  allowed_values: [development, staging, production]
  description: Application environment

debug:
  type: bool
  default: true
  description: Enable debug mode

database:
  type: group
  fields:
    host:
      type: string
      default: localhost
      description: Database host
    port:
      type: int
      default: 5432
      range: [1000, 65535]
      description: Database port
    name:
      type: string
      required: true
      description: Database name

api:
  type: group
  fields:
    host:
      type: string
      default: 0.0.0.0
      description: API host
    port:
      type: int
      default: 8000
      range: [1000, 65535]
      description: API port
    timeout:
      type: int
      default: 30
      range: [1, 300]
      description: API timeout in seconds
"""
        with open('config_schema.yaml', 'w') as f:
            f.write(schema_content)
        click.echo("✓ Created config_schema.yaml")
    
    click.echo("\n🎉 Configuration setup complete!")
    click.echo("\nNext steps:")
    click.echo("1. Edit your configuration files")
    click.echo("2. Run 'pyconfig validate' to check your config")
    click.echo("3. Use Config() in your Python code")


def _quick_init(schema_file: Optional[str]):
    """Quick configuration initialization."""
    # Create basic .env file
    env_content = """# Environment Configuration
ENVIRONMENT=development
DEBUG=true

# Add your configuration variables here
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    click.echo("✓ Created .env file")
    click.echo("Edit .env to add your configuration variables")


@main.command()
@click.option('--environment', '-e', help='Environment to check')
@click.option('--schema', '-s', help='Schema file for validation')
def check(environment, schema):
    """Check for missing or invalid configuration."""
    try:
        config_obj = Config(
            schema_file=schema,
            environment=environment
        )
        
        config_dict = config_obj.to_dict()
        
        if not config_dict:
            click.echo(click.style("⚠ No configuration found", fg='yellow'))
            return
        
        click.echo(click.style("✓ Configuration check passed", fg='green'))
        click.echo(f"\nFound {len(config_dict)} configuration keys:")
        
        for key, value in sorted(config_dict.items()):
            # Mask sensitive values
            if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                display_value = '******'
            else:
                display_value = str(value)[:50] + ('...' if len(str(value)) > 50 else '')
            
            click.echo(f"  {key}: {display_value}")
    
    except ConfigError as e:
        click.echo(click.style("✗ Configuration check failed:", fg='red'))
        click.echo(str(e))
        sys.exit(1)


@main.command()
@click.argument('env1')
@click.argument('env2')
@click.option('--schema', '-s', help='Schema file for validation')
def diff(env1, env2, schema):
    """Compare configuration between two environments."""
    try:
        # Load configuration for both environments
        config1 = Config(schema_file=schema, environment=env1)
        config2 = Config(schema_file=schema, environment=env2)
        
        dict1 = config1.to_dict()
        dict2 = config2.to_dict()
        
        # Find differences
        all_keys = set(dict1.keys()) | set(dict2.keys())
        differences = []
        
        for key in sorted(all_keys):
            val1 = dict1.get(key, '<missing>')
            val2 = dict2.get(key, '<missing>')
            
            if val1 != val2:
                differences.append((key, val1, val2))
        
        if not differences:
            click.echo(click.style(f"✓ No differences between {env1} and {env2}", fg='green'))
            return
        
        click.echo(f"Configuration differences between {env1} and {env2}:")
        click.echo("=" * 50)
        
        for key, val1, val2 in differences:
            click.echo(f"\n{key}:")
            click.echo(f"  {env1}: {val1}")
            click.echo(f"  {env2}: {val2}")
    
    except ConfigError as e:
        click.echo(click.style(f"✗ Configuration diff failed: {e}", fg='red'))
        sys.exit(1)


if __name__ == '__main__':
    main()
