import toml
from pathlib import Path
from pydantic_settings import BaseSettings


script_dir = Path(__file__).parent.parent
pyproject_path = script_dir / "pyproject.toml"

try:
    with open(pyproject_path, "r") as f:
        pyproject_data = toml.load(f)
        SCRIPT_VERSION = pyproject_data["project"]["version"]
except FileNotFoundError:
    SCRIPT_VERSION = "1.1.1.1"
except KeyError:
    SCRIPT_VERSION = "1.1.1.1"


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
