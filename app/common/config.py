from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "FastAPI Backend Boilerplate"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "A highly maintainable FastAPI startup template with layered architecture."
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Database Configuration
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "my_app_db"
    
    @property
    def DB_URL(self) -> str:
        return f"postgresql+pg8000://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    DB_POOL_SIZE: int = 4
    ISOLATION_LEVEL: str = "READ COMMITTED"

    # Security Config
    JWT_SECRET_KEY: str = Field(default="change_this_to_a_secure_random_string", alias="JWT_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 15
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
