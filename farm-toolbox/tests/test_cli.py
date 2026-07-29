"""Tests for the profile-management command-line interface."""

from pathlib import Path

import pytest

from pokemon_farm.cli import main
from pokemon_farm.profiles import load_manifest


def test_create_command_makes_a_profile(tmp_path: Path, capsys) -> None:
    """Create builds an isolated profile from an explicitly supplied ROM."""
    rom = tmp_path / "emerald.gba"
    rom.write_bytes(b"source-rom")

    exit_code = main(
        [
            "create",
            "--name",
            "emerald-level-grind",
            "--game",
            "emerald",
            "--rom",
            str(rom),
            "--profiles-root",
            str(tmp_path / "profiles"),
        ]
    )

    assert exit_code == 0
    assert "profiles\\emerald-level-grind" in capsys.readouterr().out


@pytest.mark.parametrize(
    "profile_name",
    ["..", "../escaped", "nested/name", r"nested\name"],
)
def test_create_rejects_profile_names_that_can_escape_profiles_root(
    tmp_path: Path, capsys, profile_name: str
) -> None:
    """Unsafe profile names cannot create directories outside profiles-root."""
    rom = tmp_path / "fixture.gba"
    rom.write_bytes(b"source-rom")
    profiles_root = tmp_path / "profiles"

    assert main(
        [
            "create",
            "--name",
            profile_name,
            "--game",
            "emerald",
            "--rom",
            str(rom),
            "--profiles-root",
            str(profiles_root),
        ]
    ) == 2

    assert not profiles_root.exists()
    assert "safe filename component" in capsys.readouterr().err


def test_create_rejects_an_absolute_profile_name_before_creating_directories(
    tmp_path: Path, capsys
) -> None:
    """An absolute name cannot replace the explicit profiles-root argument."""
    rom = tmp_path / "fixture.gba"
    rom.write_bytes(b"source-rom")
    profiles_root = tmp_path / "profiles"
    absolute_name = str(tmp_path / "outside-profile")

    assert main(
        [
            "create",
            "--name",
            absolute_name,
            "--game",
            "emerald",
            "--rom",
            str(rom),
            "--profiles-root",
            str(profiles_root),
        ]
    ) == 2

    assert not profiles_root.exists()
    assert not (tmp_path / "outside-profile").exists()
    assert "safe filename component" in capsys.readouterr().err


def test_verify_reports_profile_facts_and_detects_source_hash_mismatch(
    tmp_path: Path, capsys
) -> None:
    """Verify reports the requested facts even when its source has changed."""
    rom = tmp_path / "emerald.gba"
    rom.write_bytes(b"source-rom")
    profiles_root = tmp_path / "profiles"
    assert main(
        [
            "create",
            "--name",
            "emerald-level-grind",
            "--game",
            "emerald",
            "--rom",
            str(rom),
            "--profiles-root",
            str(profiles_root),
        ]
    ) == 0
    capsys.readouterr()
    manifest_path = profiles_root / "emerald-level-grind" / "profile.json"

    assert main(["verify", "--profile", str(manifest_path)]) == 0
    verified = capsys.readouterr().out
    assert "source hash:" in verified
    assert "working ROM path:" in verified
    assert "native PokeBot state path:" in verified
    assert "provisioning status: unprovisioned" in verified
    assert "backup count: 0" in verified

    rom.write_bytes(b"changed-source-rom")

    assert main(["verify", "--profile", str(manifest_path)]) == 1
    assert "source hash mismatch" in capsys.readouterr().err


def test_backup_and_restore_use_explicit_profile_and_backup_paths(
    tmp_path: Path, capsys
) -> None:
    """Backup and restore route only through the chosen profile manifest."""
    rom = tmp_path / "emerald.gba"
    rom.write_bytes(b"source-rom")
    profiles_root = tmp_path / "profiles"
    assert main(
        [
            "create",
            "--name",
            "emerald-level-grind",
            "--game",
            "emerald",
            "--rom",
            str(rom),
            "--profiles-root",
            str(profiles_root),
        ]
    ) == 0
    capsys.readouterr()
    manifest_path = profiles_root / "emerald-level-grind" / "profile.json"
    manifest = load_manifest(manifest_path)
    manifest.runtime_state.write_bytes(b"before-run")

    assert main(["backup", "--profile", str(manifest_path), "--label", "manual"]) == 0
    backup_path = Path(capsys.readouterr().out.strip().removeprefix("backup created: "))
    manifest.runtime_state.write_bytes(b"after-run")

    assert main(
        [
            "restore",
            "--profile",
            str(manifest_path),
            "--backup",
            str(backup_path),
        ]
    ) == 0
    assert manifest.runtime_state.read_bytes() == b"before-run"
