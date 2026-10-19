"""
Configuration module for LedgerLens using Pydantic Settings.
All parameters can be overridden via environment variables or .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    # Ollama vision configuration
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    GEMMA_VISION_MODEL: str = Field(default="gemma3:4b")
    OLLAMA_MOCK_FALLBACK: bool = Field(default=True)
    
    # TabPFN configuration
    TABPFN_MODE: str = Field(default="LOCAL")  # LOCAL or CLIENT
    ENABLE_TABPFN_API: bool = Field(default=False)
    TABPFN_TOKEN: str = Field(default="")
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./ledgerlens.db")
    
    # Server ports and hosts
    BACKEND_HOST: str = Field(default="0.0.0.0")
    BACKEND_PORT: int = Field(default=8000)
    FRONTEND_PORT: int = Field(default=3000)
    
    # Observability
    OBSERVABILITY_LOG_FILE: str = Field(default="observability.json")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()
