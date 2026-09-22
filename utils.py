"""
utils.py - Utility functions for OPlus Toolkit.

This module provides support functions for:
- ADB availability check and command execution
- Device detection and information retrieval
- UI type detection (ColorOS, OxygenOS, Realme UI)
- Bloatware list loading and querying
- Backup creation and restoration
- Logging setup
"""

import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
BACKUPS_DIR = PROJECT_ROOT / "backups"
LOGS_DIR = PROJECT_ROOT / "logs"
BLOATWARE_FILE = DATA_DIR / "bloatware_lists.json"


def ensure_directories() -> None:
    """Create necessary directories if they don't exist."""
    for directory in (BACKUPS_DIR, LOGS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOGGING
# ============================================================

def setup_logger(name: str = "oplus_toolkit", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger with both console and file output."""
    ensure_directories()

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    log_file = LOGS_DIR / f"oplus_toolkit_{datetime.now():%Y%m%d}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# ============================================================
# ADB AVAILABILITY AND EXECUTION
# ============================================================

def is_adb_available() -> bool:
    """Check if ADB is installed and available in PATH."""
    return shutil.which("adb") is not None


def run_adb_command(
    args: list[str],
    serial: Optional[str] = None,
    timeout: int = 30,
    check: bool = False,
) -> subprocess.CompletedProcess:
    """
    Run an ADB command and return the CompletedProcess object.

    Args:
        args: List of arguments to pass to ADB (without 'adb' itself).
        serial: Device serial number. If None, targets the only connected device.
        timeout: Timeout in seconds.
        check: If True, raises CalledProcessError on non-zero exit code.

    Returns:
        subprocess.CompletedProcess with stdout, stderr, and returncode.
    """
    if not is_adb_available():
        raise RuntimeError("ADB is not installed or not in PATH.")

    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    cmd += args

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
    )


# ============================================================
# DEVICE DETECTION
# ============================================================

def get_connected_devices() -> list[dict[str, str]]:
    """
    Return a list of connected ADB devices.

    Each entry is a dict with keys: 'serial' and 'state'.
    Only devices with state 'device' are considered ready.
    """
    result = run_adb_command(["devices"])
    devices = []
    for line in result.stdout.splitlines()[1:]:  # Skip "List of devices attached"
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            devices.append({"serial": parts[0], "state": parts[1]})
    return devices


def get_device_property(prop: str, serial: Optional[str] = None) -> str:
    """Get a single system property from the device via ADB."""
    try:
        result = run_adb_command(["shell", "getprop", prop], serial=serial)
        return result.stdout.strip()
    except Exception:
        return ""


def get_device_info(serial: Optional[str] = None) -> dict[str, str]:
    """
    Retrieve detailed device information.

    Returns a dict with:
        - serial
        - brand (e.g. OPPO, OnePlus, realme)
        - model
        - android_version
        - sdk_level
        - ui_type (ColorOS, OxygenOS, Realme UI)
        - ui_version
    """
    info = {
        "serial": serial or "",
        "brand": get_device_property("ro.product.brand", serial),
        "model": get_device_property("ro.product.model", serial),
        "android_version": get_device_property("ro.build.version.release", serial),
        "sdk_level": get_device_property("ro.build.version.sdk", serial),
    }
    info["ui_type"], info["ui_version"] = detect_ui_type(info["brand"], serial)
    return info


def detect_ui_type(brand: str, serial: Optional[str] = None) -> tuple[str, str]:
    """
    Detect which UI is running on the device.

    Returns a tuple (ui_type, ui_version).
    ui_type is one of: "ColorOS", "OxygenOS", "Realme UI", "Unknown".
    """
    brand_lower = brand.lower()

    # Read all candidate properties
    coloros_version = (
        get_device_property("ro.build.version.opporom", serial)
        or get_device_property("ro.build.version.coloros", serial)
    )
    oxygenos_version = (
        get_device_property("ro.oxygen.version", serial)
        or get_device_property("ro.build.version.oxygenos", serial)
    )
    realmeui_version = (
        get_device_property("ro.build.version.realmeui", serial)
        or get_device_property("ro.build.version.realmeui", serial)
    )

    # Determine by properties first (most reliable)
    if realmeui_version:
        return "Realme UI", realmeui_version
    if coloros_version:
        return "ColorOS", coloros_version
    if oxygenos_version:
        return "OxygenOS", oxygenos_version

    # Fall back to brand
    if "realme" in brand_lower:
        return "Realme UI", ""
    if "oneplus" in brand_lower:
        return "OxygenOS", ""
    if "oppo" in brand_lower:
        return "ColorOS", ""

    return "Unknown", ""


# ============================================================
# BLOATWARE LISTS
# ============================================================

def load_bloatware_lists(path: Path = BLOATWARE_FILE) -> dict[str, Any]:
    """Load the bloatware lists JSON file and return it as a dict."""
    if not path.exists():
        raise FileNotFoundError(f"Bloatware lists file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_packages_by_level(lists: dict[str, Any], level: str) -> list[dict[str, str]]:
    """
    Return the list of package dicts for a given safety level.

    Args:
        lists: The parsed bloatware JSON.
        level: One of 'light', 'aggressive', 'blacklist'.

    Returns:
        A list of dicts, each with keys 'package', 'name', 'reason'.
    """
    return lists.get("lists", {}).get(level, {}).get("packages", [])


def get_blacklist_packages(lists: dict[str, Any]) -> set[str]:
    """Return a set of package names that must never be removed."""
    return {pkg["package"] for pkg in get_packages_by_level(lists, "blacklist")}


def get_all_package_names(lists: dict[str, Any]) -> set[str]:
    """Return a set with all package names across all levels."""
    names: set[str] = set()
    for level in ("light", "aggressive", "blacklist"):
        names.update(pkg["package"] for pkg in get_packages_by_level(lists, level))
    return names


def is_package_installed(package: str, serial: Optional[str] = None) -> bool:
    """Check if a package is installed on the device."""
    result = run_adb_command(
        ["shell", "pm", "list", "packages", package], serial=serial
    )
    return f"package:{package}" in result.stdout


# ============================================================
# BACKUP
# ============================================================

def get_backup_filename() -> str:
    """Return a timestamped backup filename."""
    return f"backup_{datetime.now():%Y%m%d_%H%M%S}.json"


def create_backup(
    packages: list[str],
    device_info: dict[str, str],
    action: str = "uninstall",
) -> Path:
    """
    Create a backup file with the packages to be removed/disabled.

    Args:
        packages: List of package names affected.
        device_info: Dict from get_device_info().
        action: 'uninstall' or 'disable'.

    Returns:
        Path to the created backup file.
    """
    ensure_directories()
    backup_path = BACKUPS_DIR / get_backup_filename()

    backup_data = {
        "timestamp": datetime.now().isoformat(),
        "device": device_info,
        "action": action,
        "packages": packages,
    }

    with backup_path.open("w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)

    return backup_path


def load_backup(path: Path) -> dict[str, Any]:
    """Load a backup JSON file."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_backups() -> list[Path]:
    """Return a list of available backup files, sorted newest first."""
    ensure_directories()
    backups = sorted(BACKUPS_DIR.glob("backup_*.json"), reverse=True)
    return backups


# ============================================================
# MISC HELPERS
# ============================================================

def format_package_display(pkg: dict[str, str]) -> str:
    """Format a package dict as a human-readable string for the GUI."""
    return f"{pkg['name']} ({pkg['package']})"


def parse_bool(value: Any) -> bool:
    """Parse various truthy values to a bool (useful for config files)."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)
