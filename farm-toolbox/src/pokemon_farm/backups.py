"""Profile-local backups for the native PokeBot runtime state."""

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from pokemon_farm.models import ProfileManifest


def backup_runtime_state(
    manifest: ProfileManifest,
    clock: Callable[[], datetime],
    label: str = "before-run",
) -> Path:
    """Copy the existing runtime state into this profile's backup directory."""
    if not manifest.runtime_state.is_file():
        raise FileNotFoundError(f"runtime state is absent: {manifest.runtime_state}")

    timestamp = clock().astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup = manifest.backups_dir / f"{timestamp}-{label}.ss1"
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

    shutil.copy2(backup, manifest.runtime_state)
