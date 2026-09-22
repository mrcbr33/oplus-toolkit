"""
core.py - Core ADB operations for OPlus Toolkit.

This module provides:
- Single-package operations: uninstall, disable, enable, restore
- Batch processing with progress callback
- Package listing (installed, disabled)
- Dry-run mode for safe testing
- Automatic refusal of blacklisted packages
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable, Optional

from utils import (
    get_blacklist_packages,
    get_ready_devices,
    is_adb_available,
    load_bloatware_lists,
    run_adb_command,
)


# ============================================================
# TYPES
# ============================================================

class Action(str, Enum):
    """Supported operations on a package."""
    UNINSTALL = "uninstall"
    DISABLE = "disable"
    ENABLE = "enable"
    RESTORE = "restore"


@dataclass
class OperationResult:
    """Result of a single-package operation."""
    package: str
    action: Action
    success: bool
    message: str

    def __str__(self) -> str:
        status = "OK" if self.success else "FAIL"
        return f"[{status}] {self.action.value} {self.package}: {self.message}"


@dataclass
class BatchResult:
    """Result of a batch of operations."""
    results: list[OperationResult] = field(default_factory=list)
    dry_run: bool = False

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed(self) -> int:
        return self.total - self.succeeded

    @property
    def success_rate(self) -> float:
        return (self.succeeded / self.total * 100) if self.total else 0.0

    def summary(self) -> str:
        mode = "DRY RUN" if self.dry_run else "EXECUTED"
        return (
            f"[{mode}] {self.total} operations: "
            f"{self.succeeded} succeeded, {self.failed} failed "
            f"({self.success_rate:.1f}% success)"
        )


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _ensure_device_ready(serial: Optional[str], dry_run: bool = False) -> None:
    """
    Raise a RuntimeError if the ADB connection is not usable.

    In dry-run mode, the device check is skipped: only the ADB binary
    is verified. This allows simulating batches without a connected device.
    """
    if not is_adb_available():
        raise RuntimeError("ADB is not installed or not in PATH.")

    if dry_run:
        return

    devices = get_ready_devices()
    if not devices:
        raise RuntimeError(
            "No device connected. Connect a device and enable USB debugging."
        )
    if serial is None and len(devices) > 1:
        raise RuntimeError(
            f"Multiple devices connected ({len(devices)}). "
            "Please specify a device serial."
        )


def _run_shell(
    args: list[str],
    serial: Optional[str],
    dry_run: bool,
) -> tuple[bool, str]:
    """
    Run an ADB shell command and return (success, message).

    In dry-run mode, the command is not executed; a synthetic success is returned.
    """
    if dry_run:
        return True, f"[DRY RUN] adb shell {' '.join(args)}"

    try:
        result = run_adb_command(["shell", *args], serial=serial)
    except Exception as exc:
        return False, f"ADB error: {exc}"

    output = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()

    if result.returncode != 0:
        return False, stderr or output or f"exit code {result.returncode}"

    if output.lower().startswith("failure"):
        return False, output

    return True, output or "OK"


# ============================================================
# LISTING
# ============================================================

def list_installed_packages(
    serial: Optional[str] = None,
    include_system: bool = True,
) -> list[str]:
    """Return the list of installed packages (enabled only)."""
    args = ["pm", "list", "packages"]
    if not include_system:
        args.append("-3")
    result = run_adb_command(["shell", *args], serial=serial)
    return sorted(
        line[len("package:"):].strip()
        for line in result.stdout.splitlines()
        if line.startswith("package:")
    )


def list_disabled_packages(serial: Optional[str] = None) -> list[str]:
    """Return the list of disabled packages."""
    result = run_adb_command(
        ["shell", "pm", "list", "packages", "-d"], serial=serial
    )
    return sorted(
        line[len("package:"):].strip()
        for line in result.stdout.splitlines()
        if line.startswith("package:")
    )


def list_packages_status(serial: Optional[str] = None) -> dict[str, str]:
    """Return a mapping of package name -> status ('enabled' or 'disabled')."""
    status: dict[str, str] = {}
    for pkg in list_installed_packages(serial=serial):
        status[pkg] = "enabled"
    for pkg in list_disabled_packages(serial=serial):
        status[pkg] = "disabled"
    return status


# ============================================================
# SINGLE-PACKAGE OPERATIONS
# ============================================================

def uninstall_package(
    package: str,
    serial: Optional[str] = None,
    dry_run: bool = False,
) -> OperationResult:
    """Uninstall a package for the current user (user 0)."""
    ok, msg = _run_shell(
        ["pm", "uninstall", "--user", "0", package], serial, dry_run
    )
    return OperationResult(package, Action.UNINSTALL, ok, msg)


def disable_package(
    package: str,
    serial: Optional[str] = None,
    dry_run: bool = False,
) -> OperationResult:
    """Disable a package for the current user."""
    ok, msg = _run_shell(
        ["pm", "disable-user", "--user", "0", package], serial, dry_run
    )
    return OperationResult(package, Action.DISABLE, ok, msg)


def enable_package(
    package: str,
    serial: Optional[str] = None,
    dry_run: bool = False,
) -> OperationResult:
    """Re-enable a previously disabled package."""
    ok, msg = _run_shell(
        ["pm", "enable", "--user", "0", package], serial, dry_run
    )
    return OperationResult(package, Action.ENABLE, ok, msg)


def restore_package(
    package: str,
    serial: Optional[str] = None,
    dry_run: bool = False,
) -> OperationResult:
    """Restore a package that was uninstalled for the current user."""
    ok, msg = _run_shell(
        ["cmd", "package", "install-existing", "--user", "0", package],
        serial,
        dry_run,
    )
    return OperationResult(package, Action.RESTORE, ok, msg)


# ============================================================
# BATCH PROCESSING
# ============================================================

_ACTION_DISPATCH: dict[Action, Callable[..., OperationResult]] = {
    Action.UNINSTALL: uninstall_package,
    Action.DISABLE: disable_package,
    Action.ENABLE: enable_package,
    Action.RESTORE: restore_package,
}


def process_batch(
    packages: Iterable[str],
    action: Action,
    serial: Optional[str] = None,
    dry_run: bool = False,
    progress_callback: Optional[Callable[[int, int, OperationResult], None]] = None,
) -> BatchResult:
    """
    Process a batch of packages with the given action.

    Blacklisted packages are automatically refused and reported as failed
    without being touched.
    """
    _ensure_device_ready(serial, dry_run=dry_run)

    blacklist = get_blacklist_packages(load_bloatware_lists())
    func = _ACTION_DISPATCH[action]

    batch = BatchResult(dry_run=dry_run)
    package_list = list(packages)
    total = len(package_list)

    for index, package in enumerate(package_list, start=1):
        if package in blacklist:
            result = OperationResult(
                package=package,
                action=action,
                success=False,
                message="BLOCKED: package is in the blacklist.",
            )
        else:
            result = func(package, serial=serial, dry_run=dry_run)

        batch.results.append(result)

        if progress_callback is not None:
            try:
                progress_callback(index, total, result)
            except Exception:
                pass

    return batch


def restore_from_backup(
    backup_data: dict,
    serial: Optional[str] = None,
    dry_run: bool = False,
    progress_callback: Optional[Callable[[int, int, OperationResult], None]] = None,
) -> BatchResult:
    """
    Restore packages listed in a backup file.

    The action is inferred from the backup's 'action' field:
    - 'uninstall' -> restore
    - 'disable'   -> enable
    """
    packages = backup_data.get("packages", [])
    original_action = backup_data.get("action", "uninstall")

    if original_action == "disable":
        action = Action.ENABLE
    else:
        action = Action.RESTORE

    return process_batch(
        packages=packages,
        action=action,
        serial=serial,
        dry_run=dry_run,
        progress_callback=progress_callback,
    )
