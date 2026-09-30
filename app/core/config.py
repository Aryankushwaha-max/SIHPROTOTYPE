from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "eRTMAC-NWIS"
    database_url: str = "sqlite:///./nwis.db"
    api_prefix: str = "/api/v1"
    max_upload_bytes: int = 15_000_000
    model_config = SettingsConfigDict(env_prefix="NWIS_", env_file=".env", extra="ignore")


settings = Settings()
