from importlib.metadata import version, PackageNotFoundError

from pydantic_settings import BaseSettings, SettingsConfigDict


try:
    # Single source of truth: the version baked into the installed package
    # metadata (from pyproject [project].version at build time). Works for
    # wheels and editable installs alike.
    SCRIPT_VERSION = version("kaniko-wrapper")
except PackageNotFoundError:
    # Running straight from a source checkout without an install.
    # `pip install -e .` makes the real version resolve here too.
    SCRIPT_VERSION = "0.0.0.dev"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

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


settings = Settings()
