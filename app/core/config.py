from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:Singh%40786@localhost:5432/saas_db"

    class Config:
        env_file = ".env"


settings = Settings()