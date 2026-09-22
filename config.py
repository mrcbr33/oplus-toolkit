"""
config.py - Persistent configuration for OPlus Toolkit.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONFIG_FILE: Path = Path(__file__).resolve().parent / "config.json"

DEFAULTS: dict[str, Any] = {
    "language": "en",
    "theme": "dark",
    "last_level": "light",
    "last_action": "uninstall",
    "dry_run": True,
    "force_mode": False,
    "window_geometry": "1200x780",
}


def load_config() -> dict[str, Any]:
    """Load config from disk, filling missing keys with defaults."""
    if not CONFIG_FILE.exists():
        return dict(DEFAULTS)
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        return dict(DEFAULTS)

    if not isinstance(data, dict):
        return dict(DEFAULTS)

    for key, value in DEFAULTS.items():
        data.setdefault(key, value)
    return data


def save_config(config: dict[str, Any]) -> None:
    """Persist config to disk. Failures are silent (non-critical)."""
    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2, ensure_ascii=False)
    except Exception:
        pass
