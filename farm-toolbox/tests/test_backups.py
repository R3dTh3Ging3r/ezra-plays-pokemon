"""Tests for safe profile-local runtime-state recovery."""

from datetime import UTC, datetime
from dataclasses import replace
import os
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


@pytest.mark.parametrize("label", ["", "   ", "..", "../escape", "nested/name", r"nested\name"])
def test_backup_rejects_unsafe_labels(created_manifest, label: str) -> None:
    """Labels cannot escape or create nested paths below the backup directory."""
    created_manifest.runtime_state.write_bytes(b"state")

    with pytest.raises(ValueError, match="label"):
        backup_runtime_state(
            created_manifest,
            lambda: datetime(2026, 7, 28, 20, 0, tzinfo=UTC),
            label,
        )


def test_backup_rejects_same_second_collision_without_overwriting(created_manifest) -> None:
    """A repeated timestamp retains the first state rather than replacing it."""
    clock = lambda: datetime(2026, 7, 28, 20, 0, tzinfo=UTC)
    created_manifest.runtime_state.write_bytes(b"first")
    backup = backup_runtime_state(created_manifest, clock)
    created_manifest.runtime_state.write_bytes(b"second")

    with pytest.raises(FileExistsError):
        backup_runtime_state(created_manifest, clock)

    assert backup.read_bytes() == b"first"


def test_restore_rejects_a_runtime_state_symlink_to_source_without_mutating_source(
    created_manifest,
) -> None:
    """A symlinked restore destination cannot redirect writes to the source ROM."""
    backup = created_manifest.backups_dir / "known-good.ss1"
    backup.write_bytes(b"restored-state")
    try:
        created_manifest.runtime_state.symlink_to(created_manifest.source_path)
    except OSError as error:
        pytest.skip(f"symlinks are unavailable: {error}")

    with pytest.raises(ValueError, match="runtime state"):
        restore_backup(created_manifest, backup)

    assert created_manifest.source_path.read_bytes() == b"source-rom"


def test_restore_rejects_a_runtime_state_hardlink_to_source_without_mutating_source(
    created_manifest,
) -> None:
    """A hardlinked restore destination cannot overwrite the source ROM."""
    backup = created_manifest.backups_dir / "known-good.ss1"
    backup.write_bytes(b"restored-state")
    try:
        os.link(created_manifest.source_path, created_manifest.runtime_state)
    except OSError as error:
        pytest.skip(f"hardlinks are unavailable: {error}")

    with pytest.raises(ValueError, match="runtime state"):
        restore_backup(created_manifest, backup)

    assert created_manifest.source_path.read_bytes() == b"source-rom"


def test_restore_rejects_a_runtime_destination_outside_the_profile(
    created_manifest, tmp_path: Path
) -> None:
    """Restore never writes through a manifest path that resolves outside its profile."""
    backup = created_manifest.backups_dir / "known-good.ss1"
    backup.write_bytes(b"restored-state")
    outside_runtime_state = tmp_path / "outside.ss1"
    unsafe_manifest = replace(created_manifest, runtime_state=outside_runtime_state)

    with pytest.raises(ValueError, match="runtime state"):
        restore_backup(unsafe_manifest, backup)

    assert not outside_runtime_state.exists()
