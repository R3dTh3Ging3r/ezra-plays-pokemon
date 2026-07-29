"""Tests for safe profile-local runtime-state recovery."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from pokemon_farm.backups import backup_runtime_state, restore_backup


def test_backup_and_restore_touch_only_runtime_state(created_manifest) -> None:
    """Recovery restores the saved runtime state without touching the source ROM."""
    created_manifest.runtime_state.write_bytes(b"before-run")

    backup = backup_runtime_state(
        created_manifest, lambda: datetime(2026, 7, 28, 20, 0, tzinfo=UTC)
    )
    created_manifest.runtime_state.write_bytes(b"after-run")

    restore_backup(created_manifest, backup)

    assert backup.name == "20260728T200000Z-before-run.ss1"
    assert created_manifest.runtime_state.read_bytes() == b"before-run"
    assert created_manifest.source_path.read_bytes() == b"source-rom"


def test_backup_requires_an_existing_runtime_state(created_manifest) -> None:
    """A launch cannot start recovery without PokeBot's native state file."""
    with pytest.raises(FileNotFoundError, match="runtime state"):
        backup_runtime_state(
            created_manifest, lambda: datetime(2026, 7, 28, 20, 0, tzinfo=UTC)
        )


def test_restore_rejects_a_backup_outside_the_profile(created_manifest, tmp_path: Path) -> None:
    """A profile may restore only files from its own backup directory."""
    outside_backup = tmp_path / "outside.ss1"
    outside_backup.write_bytes(b"outside")

    with pytest.raises(ValueError, match="profile backups directory"):
        restore_backup(created_manifest, outside_backup)
