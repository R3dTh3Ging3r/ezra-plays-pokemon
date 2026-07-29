"""Profile-local backups for the native PokeBot runtime state."""

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from pokemon_farm.models import ProfileManifest


def _validate_label(label: str) -> None:
    """Reject labels that cannot safely form one backup filename component."""
    if (
        not label.strip()
        or label in {".", ".."}
        or "/" in label
        or "\\" in label
        or label.endswith((".", " "))
        or any(character in label for character in '<>:"|?*')
        or any(ord(character) < 32 for character in label)
    ):
        raise ValueError("backup label must be one safe filename component")


def _validate_runtime_destination(manifest: ProfileManifest) -> Path:
    """Return a profile-owned runtime path that cannot redirect a restore."""
    runtime_state = manifest.runtime_state
    if runtime_state.is_symlink():
        raise ValueError("runtime state destination cannot be a symlink")

    resolved_runtime_state = runtime_state.resolve()
    if not resolved_runtime_state.is_relative_to(manifest.profile_root.resolve()):
        raise ValueError("runtime state destination must remain within the profile")
    if runtime_state.exists() and manifest.source_path.exists() and runtime_state.samefile(
        manifest.source_path
    ):
        raise ValueError("runtime state destination cannot be the source ROM")
    return resolved_runtime_state


def backup_runtime_state(
    manifest: ProfileManifest,
    clock: Callable[[], datetime],
    label: str = "before-run",
) -> Path:
    """Copy the existing runtime state into this profile's backup directory."""
    if not manifest.runtime_state.is_file():
        raise FileNotFoundError(f"runtime state is absent: {manifest.runtime_state}")
    _validate_label(label)

    timestamp = clock().astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    backups_dir = manifest.backups_dir.resolve()
    if not backups_dir.is_relative_to(manifest.profile_root.resolve()):
        raise ValueError("backups directory must remain within the profile")
    backup = (backups_dir / f"{timestamp}-{label}.ss1").resolve()
    if not backup.is_relative_to(backups_dir):
        raise ValueError("backup destination must be inside the profile backups directory")
    backup.touch(exist_ok=False)
    shutil.copy2(manifest.runtime_state, backup)
    return backup


def restore_backup(manifest: ProfileManifest, backup: Path) -> None:
    """Restore a profile-owned runtime-state backup without touching its ROM source."""
    backups_dir = manifest.backups_dir.resolve()
    backup = Path(backup).resolve()
    if not backup.is_relative_to(backups_dir):
        raise ValueError("backup must be inside the profile backups directory")
    if not backup.is_file():
        raise FileNotFoundError(f"backup file is absent: {backup}")

    shutil.copy2(backup, _validate_runtime_destination(manifest))
