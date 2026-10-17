from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    camping_api_service_key: str = ""
    weather_api_service_key: str = ""
    allowed_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "https://camping-weather-planner.vercel.app"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
