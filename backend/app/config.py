from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/face_detection"
    api_key: str = "demo-key-change-me"

    class Config:
        env_file = ".env"


settings = Settings()
