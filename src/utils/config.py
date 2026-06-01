"""Configuration and logging helpers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML configuration and return a plain dictionary."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def resolve_path(path_value: str | Path) -> Path:
    """Resolve project-relative paths from the config file."""
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def setup_logging(level: str = "INFO") -> None:
    """Configure process-wide logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
