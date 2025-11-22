"""
CCC Configuration Module
Centralized configuration for the Covenant Command Cycle project
"""

import os
from typing import List


class Config:
    """Application configuration with environment variable support"""

    # Server Configuration
    HOST: str = os.getenv('HOST', '127.0.0.1')
    PORT: int = int(os.getenv('PORT', '8000'))
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
    LOG_SENSITIVE_DATA: bool = os.getenv('LOG_SENSITIVE_DATA', 'False').lower() in ('true', '1', 'yes')

    # OpenAI API Configuration
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_API_BASE: str = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
    OPENAI_API_TIMEOUT: int = int(os.getenv('OPENAI_API_TIMEOUT', '30'))

    # CORS Configuration
    CORS_ENABLED: bool = os.getenv('CORS_ENABLED', 'True').lower() in ('true', '1', 'yes')
    CORS_ORIGINS: List[str] = os.getenv('CORS_ORIGINS', '*').split(',')

    # Memory Configuration
    CCC_DATABASE_PATH: str = os.getenv('CCC_DATABASE_PATH', 'ccc_memory.db')
    CCC_CAUSAL_DATABASE_PATH: str = os.getenv('CCC_CAUSAL_DATABASE_PATH', 'ccc_causal_memory.db')
    MEMORY_CACHE_TIMEOUT: int = int(os.getenv('MEMORY_CACHE_TIMEOUT', '300'))  # 5 minutes

    # Encryption Configuration
    CCC_ENCRYPTION_ENABLED: bool = os.getenv('CCC_ENCRYPTION_ENABLED', 'false').lower() in ('true', '1', 'yes')
    CCC_ENCRYPTION_KEY: str = os.getenv('CCC_ENCRYPTION_KEY', '')

    # Crucible Protocol Configuration
    CRUCIBLE_DEFAULT_TIMEOUT: int = int(os.getenv('CRUCIBLE_DEFAULT_TIMEOUT', '30'))
    CRUCIBLE_MAX_TIMEOUT: int = int(os.getenv('CRUCIBLE_MAX_TIMEOUT', '300'))
    CRUCIBLE_MAX_RETRIES: int = int(os.getenv('CRUCIBLE_MAX_RETRIES', '3'))

    # Context Analyzer Configuration
    CONTEXT_SIMILARITY_THRESHOLD: float = float(os.getenv('CONTEXT_SIMILARITY_THRESHOLD', '0.7'))
    CONTEXT_MAX_AGE_HOURS: int = int(os.getenv('CONTEXT_MAX_AGE_HOURS', '24'))
    CONTEXT_MAX_TURNS: int = int(os.getenv('CONTEXT_MAX_TURNS', '10'))

    # Causal Memory Configuration
    CAUSAL_SIMILARITY_THRESHOLD: float = float(os.getenv('CAUSAL_SIMILARITY_THRESHOLD', '0.5'))
    CAUSAL_MAX_POTENTIAL_CAUSES: int = int(os.getenv('CAUSAL_MAX_POTENTIAL_CAUSES', '5'))
    CAUSAL_TIME_DECAY_HOURS: int = int(os.getenv('CAUSAL_TIME_DECAY_HOURS', '24'))
    CAUSAL_LLM_MODEL: str = os.getenv('CAUSAL_LLM_MODEL', 'gpt-3.5-turbo')
    CAUSAL_LLM_TEMPERATURE: float = float(os.getenv('CAUSAL_LLM_TEMPERATURE', '0.7'))

    # Memory Service Initialization
    MEMORY_INIT_TIMEOUT: int = int(os.getenv('MEMORY_INIT_TIMEOUT', '60'))

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required but not set")
        return True

    @classmethod
    def get_cors_config(cls) -> dict:
        """Get CORS configuration for Flask-CORS"""
        if not cls.CORS_ENABLED:
            return {}

        if cls.CORS_ORIGINS == ['*']:
            # Development mode - allow all origins
            if cls.DEBUG:
                return {'origins': '*'}
            else:
                # Production mode - require explicit origins
                raise ValueError("CORS_ORIGINS must be explicitly set in production mode (not '*')")

        return {'origins': cls.CORS_ORIGINS}


# Create singleton instance
config = Config()
