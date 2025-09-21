"""Base configuration loader interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class ConfigLoader(ABC):
    """Base class for configuration loaders."""
    
    def __init__(self, **options):
        self.options = options
    
    @abstractmethod
    def load(self, source: str) -> Dict[str, Any]:
        """Load configuration from source."""
        pass
    
    @abstractmethod
    def can_load(self, source: str) -> bool:
        """Check if this loader can handle the given source."""
        pass
    
    def get_priority(self) -> int:
        """Get loader priority (higher = more priority)."""
        return 0


class FileLoader(ConfigLoader):
    """Base class for file-based loaders."""
    
    def __init__(self, **options):
        super().__init__(**options)
        self.supported_extensions = []
    
    def can_load(self, source: str) -> bool:
        """Check if file extension is supported."""
        return any(source.endswith(ext) for ext in self.supported_extensions)


class EnvironmentAwareLoader(ConfigLoader):
    """Base class for environment-aware loaders."""
    
    def __init__(self, environment: Optional[str] = None, **options):
        super().__init__(**options)
        self.environment = environment
    
    def get_environment_specific_sources(self, base_source: str) -> List[str]:
        """Get environment-specific source variations."""
        if not self.environment:
            return [base_source]
        
        sources = [base_source]
        
        # Add environment-specific variations
        if '.' in base_source:
            name, ext = base_source.rsplit('.', 1)
            env_source = f"{name}.{self.environment}.{ext}"
            sources.append(env_source)
        else:
            env_source = f"{base_source}.{self.environment}"
            sources.append(env_source)
        
        return sources
