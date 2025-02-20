from pydantic_settings import BaseSettings

# Script version
SCRIPT_VERSION = "2.0.0.0"


class Settings(BaseSettings):
    log_level: str = "INFO"
    log_format: str = "%(log_color)s%(asctime)s - %(levelname)s - %(message)s"
    datefmt: str = "%Y-%m-%d %H:%M:%S"
    log_colors: dict = {
        "DEBUG": "green",
        "INFO": "blue",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }

    class Config:
        env_file = ".env"


settings = Settings()
