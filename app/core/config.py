from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/facial_recognition"

    jwt_secret_key: str = "changeme-generate-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    face_model_pack: str = "buffalo_l"
    recognition_threshold: float = 0.45
    liveness_threshold: float = 0.65

    consensus_frames_required: int = 5
    # The browser polls ~1 frame/sec, so 5 frames span ~5s of wall time; the
    # window must be comfortably larger than that (with latency margin) or the
    # oldest frame expires before the 5th arrives and consensus never completes.
    consensus_window_seconds: int = 10


settings = Settings()
