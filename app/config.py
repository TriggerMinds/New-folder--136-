from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field("development", alias="APP_ENV")
    app_host: str = Field("127.0.0.1", alias="APP_HOST")
    app_port: int = Field(8000, alias="APP_PORT")
    database_url: str = Field(
        "postgresql+psycopg://eu_leak:change_me@localhost:5432/eu_leak",
        alias="DATABASE_URL",
    )
    deepseek_api_key: str = Field("", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field("https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_flash_model: str = Field("", alias="DEEPSEEK_FLASH_MODEL")
    deepseek_pro_model: str = Field("", alias="DEEPSEEK_PRO_MODEL")
    deepseek_timeout_seconds: int = Field(60, alias="DEEPSEEK_TIMEOUT_SECONDS")
    deepseek_max_retries: int = Field(3, alias="DEEPSEEK_MAX_RETRIES")
    scheduler_enabled: bool = Field(True, alias="SCHEDULER_ENABLED")
    default_poll_interval_minutes: int = Field(30, alias="DEFAULT_POLL_INTERVAL_MINUTES")
    max_concurrent_http_requests: int = Field(4, alias="MAX_CONCURRENT_HTTP_REQUESTS")
    max_concurrent_playwright_pages: int = Field(1, alias="MAX_CONCURRENT_PLAYWRIGHT_PAGES")
    snapshot_storage_enabled: bool = Field(False, alias="SNAPSHOT_STORAGE_ENABLED")
    data_directory: str = Field("./data", alias="DATA_DIRECTORY")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    http_user_agent: str = Field("EU-Leak-Discovery/0.1.0", alias="HTTP_USER_AGENT")
    http_timeout_seconds: int = Field(30, alias="HTTP_TIMEOUT_SECONDS")
    http_max_response_bytes: int = Field(10000000, alias="HTTP_MAX_RESPONSE_BYTES")
    max_items_per_source: int = Field(100, alias="MAX_ITEMS_PER_SOURCE")
    country_pack_directory: str = Field("app/country_packs", alias="COUNTRY_PACK_DIRECTORY")
    connector_concurrency: int = Field(4, alias="CONNECTOR_CONCURRENCY")
    scheduler_timezone: str = Field("UTC", alias="SCHEDULER_TIMEZONE")
    download_artifacts: bool = Field(False, alias="DOWNLOAD_ARTIFACTS")
    github_token: str = Field("", alias="GITHUB_TOKEN")


settings = Settings()
