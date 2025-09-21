"""Tests for CLI interface."""

import tempfile
import pytest
from pathlib import Path
from click.testing import CliRunner

from pyconfig.cli import main


class TestCLI:
    """Test cases for CLI interface."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'PyConfig Universal' in result.output
    
    def test_validate_command_success(self):
        """Test successful configuration validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test configuration
            config_file = Path(tmpdir) / '.env'
            config_file.write_text('PORT=8000\nDEBUG=true')
            
            # Create schema
            schema_file = Path(tmpdir) / 'schema.yaml'
            schema_content = """
port:
  type: int
  default: 8000
debug:
  type: bool
  default: false
"""
            schema_file.write_text(schema_content)
            
            result = self.runner.invoke(main, [
                'validate',
                '--config', str(config_file),
                '--schema', str(schema_file)
            ])
            
            assert result.exit_code == 0
            assert '✓ Configuration validation passed' in result.output
    
    def test_validate_command_failure(self):
        """Test failed configuration validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid configuration
            config_file = Path(tmpdir) / '.env'
            config_file.write_text('PORT=invalid_port')
            
            # Create schema
            schema_file = Path(tmpdir) / 'schema.yaml'
            schema_content = """
port:
  type: int
  required: true
"""
            schema_file.write_text(schema_content)
            
            result = self.runner.invoke(main, [
                'validate',
                '--config', str(config_file),
                '--schema', str(schema_file),
                '--strict'
            ])
            
            assert result.exit_code == 1
            assert '✗ Configuration validation failed' in result.output
    
    def test_generate_env_command(self):
        """Test generate-env command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create schema
            schema_file = Path(tmpdir) / 'schema.yaml'
            schema_content = """
port:
  type: int
  default: 8000
  description: Server port number
debug:
  type: bool
  default: false
  description: Enable debug mode
"""
            schema_file.write_text(schema_content)
            
            output_file = Path(tmpdir) / '.env.example'
            
            result = self.runner.invoke(main, [
                'generate-env',
                '--schema', str(schema_file),
                '--output', str(output_file)
            ])
            
            assert result.exit_code == 0
            assert '✓ Generated .env template' in result.output
            
            # Check generated content
            content = output_file.read_text()
            assert 'Server port number' in content
            assert 'PORT=8000' in content
            assert 'DEBUG=False' in content
    
    def test_generate_docs_markdown(self):
        """Test generate-docs command with Markdown format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create schema
            schema_file = Path(tmpdir) / 'schema.yaml'
            schema_content = """
port:
  type: int
  default: 8000
  description: Server port number
"""
            schema_file.write_text(schema_content)
            
            output_file = Path(tmpdir) / 'CONFIG.md'
            
            result = self.runner.invoke(main, [
                'generate-docs',
                '--schema', str(schema_file),
                '--output', str(output_file),
                '--format', 'markdown'
            ])
            
            assert result.exit_code == 0
            assert '✓ Generated documentation' in result.output
            
            # Check generated content
            content = output_file.read_text()
            assert '# Configuration Reference' in content
            assert '## port' in content
            assert 'Server port number' in content
    
    def test_generate_docs_html(self):
        """Test generate-docs command with HTML format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create schema
            schema_file = Path(tmpdir) / 'schema.yaml'
            schema_content = """
port:
  type: int
  default: 8000
  description: Server port number
"""
            schema_file.write_text(schema_content)
            
            output_file = Path(tmpdir) / 'config.html'
            
            result = self.runner.invoke(main, [
                'generate-docs',
                '--schema', str(schema_file),
                '--output', str(output_file),
                '--format', 'html'
            ])
            
            assert result.exit_code == 0
            assert '✓ Generated documentation' in result.output
            
            # Check generated content
            content = output_file.read_text()
            assert '<!DOCTYPE html>' in content
            assert '<h2>port</h2>' in content
    
    def test_init_command_quick(self):
        """Test init command (quick mode)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory
            import os
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                result = self.runner.invoke(main, ['init'])
                
                assert result.exit_code == 0
                assert '✓ Created .env file' in result.output
                
                # Check created file
                env_file = Path('.env')
                assert env_file.exists()
                content = env_file.read_text()
                assert 'ENVIRONMENT=development' in content
            finally:
                os.chdir(old_cwd)
    
    def test_init_command_interactive(self):
        """Test init command (interactive mode)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                # Simulate interactive input
                result = self.runner.invoke(main, ['init', '--interactive'], input='\n\n\n\ny\n')
                
                assert result.exit_code == 0
                assert '🚀 PyConfig Universal - Interactive Setup' in result.output
                
                # Check created files
                assert Path('config.yaml').exists()
                assert Path('config_schema.yaml').exists()
            finally:
                os.chdir(old_cwd)
    
    def test_check_command(self):
        """Test check command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create configuration
            config_file = Path(tmpdir) / '.env'
            config_file.write_text('PORT=8000\nDEBUG=true\nAPI_KEY=secret123')
            
            import os
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                result = self.runner.invoke(main, ['check'])
                
                assert result.exit_code == 0
                assert '✓ Configuration check passed' in result.output
                assert 'port: 8000' in result.output
                assert 'debug: true' in result.output
                assert 'api_key: ******' in result.output  # Sensitive value masked
            finally:
                os.chdir(old_cwd)
    
    def test_diff_command(self):
        """Test diff command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create development config
            dev_file = Path(tmpdir) / '.env.development'
            dev_file.write_text('DEBUG=true\nPORT=8000')
            
            # Create production config
            prod_file = Path(tmpdir) / '.env.production'
            prod_file.write_text('DEBUG=false\nPORT=80')
            
            import os
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                result = self.runner.invoke(main, ['diff', 'development', 'production'])
                
                assert result.exit_code == 0
                assert 'Configuration differences' in result.output
                assert 'debug:' in result.output
                assert 'port:' in result.output
            finally:
                os.chdir(old_cwd)
    
    def test_diff_command_no_differences(self):
        """Test diff command with no differences."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create identical configs
            config_content = 'DEBUG=true\nPORT=8000'
            
            dev_file = Path(tmpdir) / '.env.development'
            dev_file.write_text(config_content)
            
            staging_file = Path(tmpdir) / '.env.staging'
            staging_file.write_text(config_content)
            
            import os
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                result = self.runner.invoke(main, ['diff', 'development', 'staging'])
                
                assert result.exit_code == 0
                assert '✓ No differences' in result.output
            finally:
                os.chdir(old_cwd)
