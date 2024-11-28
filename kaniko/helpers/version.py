import importlib.metadata
import logging

logger = logging.getLogger(__name__)


def version_lib(package_name: str, default: str = "<UNDEFINED>"):
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return default
