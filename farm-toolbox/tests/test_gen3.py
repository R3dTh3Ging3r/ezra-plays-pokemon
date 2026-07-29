"""Tests for safe PokeBot Gen3 staging and synchronization."""

import os
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from pokemon_farm.gen3 import (
    build_gen3_command,
    preflight_gen3,
    stage_gen3_profile,
    stage_gen3_rom,
    sync_gen3_profile,
)
from pokemon_farm.models import GameFamily


def _make_tool_root(tmp_path: Path) -> Path:
    """Create a harmless filesystem fixture shaped like a PokeBot checkout."""
    tool_root = tmp_path / "pokebot-gen3"
    (tool_root / ".venv" / "Scripts").mkdir(parents=True)
    (tool_root / "roms").mkdir()
    (tool_root / "profiles").mkdir()
    (tool_root / "pokebot.py").write_bytes(b"")
    (tool_root / ".venv" / "Scripts" / "python.exe").write_bytes(b"")
    return tool_root


def _provision_local_profile(created_manifest) -> None:
    """Add the two native PokeBot files required for a launch."""
    (created_manifest.bot_profile_dir / "metadata.yml").write_text(
        "version: 1\nrom: {}\n", encoding="utf-8"
    )
    created_manifest.runtime_state.write_bytes(b"state")


def test_stage_gen3_profile_uses_a_profile_copy(
    created_manifest, tmp_path: Path
) -> None:
    _provision_local_profile(created_manifest)
    tool_root = _make_tool_root(tmp_path)

    staged_rom = stage_gen3_profile(created_manifest, tool_root)

    assert staged_rom.parent == tool_root / "roms"
    assert staged_rom.read_bytes() == b"source-rom"
    assert (
        tool_root
        / "profiles"
        / "emerald-level-grind"
        / "current_state.ss1"
    ).read_bytes() == b"state"
    assert created_manifest.source_path.read_bytes() == b"source-rom"
    backups = list(created_manifest.backups_dir.glob("*-before-gen3-stage.ss1"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == b"state"


def test_stage_gen3_rom_requires_the_validated_upstream_layout(
    created_manifest, tmp_path: Path
) -> None:
    tool_root = _make_tool_root(tmp_path)
    (tool_root / ".venv" / "Scripts" / "python.exe").unlink()

    with pytest.raises(FileNotFoundError, match="python.exe"):
        stage_gen3_rom(created_manifest, tool_root)

    assert not (tool_root / "roms" / "emerald-level-grind.gba").exists()


def test_stage_gen3_rom_rejects_a_redirected_venv_ancestor(
    created_manifest, tmp_path: Path
) -> None:
    """A redirected .venv cannot select an interpreter outside the tool root."""
    tool_root = _make_tool_root(tmp_path)
    shutil.rmtree(tool_root / ".venv")
    outside_venv = tmp_path / "outside-venv"
    (outside_venv / "Scripts").mkdir(parents=True)
    (outside_venv / "Scripts" / "python.exe").write_bytes(b"")
    redirected_venv = tool_root / ".venv"
    try:
        redirected_venv.symlink_to(outside_venv, target_is_directory=True)
    except OSError as symlink_error:
        if os.name != "nt":
            pytest.skip(f"directory redirects are unavailable: {symlink_error}")
        junction = subprocess.run(
            [
                "cmd.exe",
                "/c",
                "mklink",
                "/J",
                str(redirected_venv),
                str(outside_venv),
            ],
            capture_output=True,
            text=True,
        )
        if junction.returncode != 0:
            pytest.skip(
                "directory redirects are unavailable: "
                f"{symlink_error}; {junction.stderr.strip()}"
            )

    with pytest.raises(ValueError, match="python.exe.*tool root"):
        stage_gen3_rom(created_manifest, tool_root)

    assert not (tool_root / "roms" / "emerald-level-grind.gba").exists()


def test_stage_gen3_rom_rejects_a_non_gen3_manifest(
    created_manifest, tmp_path: Path
) -> None:
    tool_root = _make_tool_root(tmp_path)
    gen2_manifest = replace(created_manifest, game_family=GameFamily.GEN2)

    with pytest.raises(ValueError, match="Gen 3"):
        stage_gen3_rom(gen2_manifest, tool_root)

    assert not (tool_root / "roms" / "emerald-level-grind.gba").exists()


def test_stage_gen3_rom_rejects_a_changed_source(
    created_manifest, tmp_path: Path
) -> None:
    tool_root = _make_tool_root(tmp_path)
    created_manifest.source_path.write_bytes(b"changed")

    with pytest.raises(RuntimeError, match="source ROM hash mismatch"):
        stage_gen3_rom(created_manifest, tool_root)

    assert not (tool_root / "roms" / "emerald-level-grind.gba").exists()


def test_stage_gen3_rom_rejects_a_profile_name_that_escapes_roms(
    created_manifest, tmp_path: Path
) -> None:
    tool_root = _make_tool_root(tmp_path)
    escaped_manifest = replace(created_manifest, profile_name="../escaped")

    with pytest.raises(ValueError, match="profile name"):
        stage_gen3_rom(escaped_manifest, tool_root)

    assert not (tool_root / "escaped.gba").exists()


def test_preflight_requires_provisioned_profile_files(
    created_manifest, tmp_path: Path
) -> None:
    tool_root = _make_tool_root(tmp_path)

    with pytest.raises(FileNotFoundError, match="metadata.yml"):
        preflight_gen3(created_manifest, tool_root)

    (created_manifest.bot_profile_dir / "metadata.yml").write_text(
        "version: 1\n", encoding="utf-8"
    )
    with pytest.raises(FileNotFoundError, match="current_state.ss1"):
        preflight_gen3(created_manifest, tool_root)


def test_preflight_rejects_a_runtime_state_outside_the_profile(
    created_manifest, tmp_path: Path
) -> None:
    tool_root = _make_tool_root(tmp_path)
    (created_manifest.bot_profile_dir / "metadata.yml").write_text(
        "version: 1\n", encoding="utf-8"
    )
    outside_state = tmp_path / "outside.ss1"
    outside_state.write_bytes(b"outside")
    redirected_manifest = replace(created_manifest, runtime_state=outside_state)

    with pytest.raises(ValueError, match="runtime state"):
        preflight_gen3(redirected_manifest, tool_root)


def test_preflight_rejects_a_changed_source_before_launch(
    created_manifest, tmp_path: Path
) -> None:
    tool_root = _make_tool_root(tmp_path)
    _provision_local_profile(created_manifest)
    created_manifest.source_path.write_bytes(b"changed")

    with pytest.raises(RuntimeError, match="source ROM hash mismatch"):
        preflight_gen3(created_manifest, tool_root)


def test_sync_gen3_profile_copies_back_without_deleting_local_files(
    created_manifest, tmp_path: Path
) -> None:
    tool_root = _make_tool_root(tmp_path)
    upstream_profile = tool_root / "profiles" / created_manifest.profile_name
    upstream_profile.mkdir()
    (upstream_profile / "metadata.yml").write_text("version: 2\n", encoding="utf-8")
    (upstream_profile / "current_state.ss1").write_bytes(b"new-state")
    local_only = created_manifest.bot_profile_dir / "local-notes.txt"
    local_only.write_text("keep", encoding="utf-8")

    sync_gen3_profile(created_manifest, tool_root)

    assert created_manifest.runtime_state.read_bytes() == b"new-state"
    assert local_only.read_text(encoding="utf-8") == "keep"


def test_sync_gen3_profile_rejects_a_non_gen3_manifest(
    created_manifest, tmp_path: Path
) -> None:
    """Direct synchronization cannot import into a manifest for another generation."""
    tool_root = _make_tool_root(tmp_path)
    upstream_profile = tool_root / "profiles" / created_manifest.profile_name
    upstream_profile.mkdir()
    (upstream_profile / "current_state.ss1").write_bytes(b"gen2-unsafe")
    gen2_manifest = replace(created_manifest, game_family=GameFamily.GEN2)

    with pytest.raises(ValueError, match="Gen 3"):
        sync_gen3_profile(gen2_manifest, tool_root)

    assert not created_manifest.runtime_state.exists()


def test_sync_gen3_profile_rejects_a_symlinked_local_destination(
    created_manifest, tmp_path: Path
) -> None:
    tool_root = _make_tool_root(tmp_path)
    upstream_profile = tool_root / "profiles" / created_manifest.profile_name
    upstream_profile.mkdir()
    (upstream_profile / "metadata.yml").write_text("version: 2\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    created_manifest.bot_profile_dir.rmdir()
    try:
        created_manifest.bot_profile_dir.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlinks are unavailable: {error}")

    with pytest.raises(ValueError, match="bot profile"):
        sync_gen3_profile(created_manifest, tool_root)

    assert list(outside.iterdir()) == []


def test_build_gen3_command_selects_profile_and_mode(tmp_path: Path) -> None:
    assert build_gen3_command(tmp_path, "emerald-level-grind", "Level Grind") == [
        str(tmp_path / ".venv" / "Scripts" / "python.exe"),
        "pokebot.py",
        "emerald-level-grind",
        "--bot-mode",
        "Level Grind",
    ]


def test_build_gen3_command_builds_the_bare_provisioning_command(
    tmp_path: Path,
) -> None:
    assert build_gen3_command(tmp_path, None, None) == [
        str(tmp_path / ".venv" / "Scripts" / "python.exe"),
        "pokebot.py",
    ]


@pytest.mark.parametrize(
    ("profile_name", "mode"),
    [
        (None, "Level Grind"),
        ("emerald-level-grind", None),
        ("", "Level Grind"),
        ("emerald-level-grind", "  "),
    ],
)
def test_build_gen3_command_rejects_incomplete_launch_selection(
    tmp_path: Path, profile_name: str | None, mode: str | None
) -> None:
    with pytest.raises(ValueError, match="profile and mode"):
        build_gen3_command(tmp_path, profile_name, mode)
