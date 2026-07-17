"""
전역 설정. .env 파일을 읽어 pydantic-settings로 검증한다.
서비스 어디서든 `from app.core.config import settings` 로 사용.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "development"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT (이다영 담당 모듈에서 최종 값 사용)
    JWT_SECRET_KEY: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # External APIs
    KAKAO_REST_API_KEY: str = ""
    KAKAO_JS_KEY: str = ""
    TOUR_API_KEY: str = ""
    TOUR_API_BASE_URL: str = "https://apis.data.go.kr/B551011/KorService2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()