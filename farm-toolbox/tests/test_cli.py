"""Tests for the profile-management command-line interface."""

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

import pokemon_farm.cli as cli_module
from pokemon_farm.cli import main
from pokemon_farm.profiles import load_manifest


@dataclass
class _ProcessResult:
    """Minimal completed-process result returned by harmless test runners."""

    returncode: int


def _make_tool_root(tmp_path: Path) -> Path:
    """Create a harmless filesystem fixture shaped like a PokeBot checkout."""
    tool_root = tmp_path / "pokebot-gen3"
    (tool_root / ".venv" / "Scripts").mkdir(parents=True)
    (tool_root / "roms").mkdir()
    (tool_root / "profiles").mkdir()
    (tool_root / "pokebot.py").write_bytes(b"")
    (tool_root / ".venv" / "Scripts" / "python.exe").write_bytes(b"")
    return tool_root


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


def test_provision_gen3_stages_then_syncs_a_created_upstream_profile(
    created_manifest, tmp_path: Path, monkeypatch, capsys
) -> None:
    """Provision runs bare PokeBot and imports the profile it created."""
    tool_root = _make_tool_root(tmp_path)
    manifest_path = created_manifest.profile_root / "profile.json"
    observed: list[tuple[list[str], Path]] = []

    def harmless_runner(command: list[str], *, cwd: Path):
        observed.append((command, cwd))
        upstream = tool_root / "profiles" / created_manifest.profile_name
        upstream.mkdir()
        (upstream / "metadata.yml").write_text("version: 1\n", encoding="utf-8")
        (upstream / "current_state.ss1").write_bytes(b"provisioned")
        return _ProcessResult(0)

    monkeypatch.setattr(cli_module, "_run_process", harmless_runner)

    exit_code = main(
        [
            "provision-gen3",
            "--profile",
            str(manifest_path),
            "--tool-root",
            str(tool_root),
        ]
    )

    assert exit_code == 0
    assert observed == [
        (
            [
                str(tool_root / ".venv" / "Scripts" / "python.exe"),
                "pokebot.py",
            ],
            tool_root,
        )
    ]
    assert (tool_root / "roms" / "emerald-level-grind.gba").read_bytes() == b"source-rom"
    assert created_manifest.runtime_state.read_bytes() == b"provisioned"
    assert "profile synchronized" in capsys.readouterr().out


def test_sync_gen3_command_copies_the_named_upstream_profile(
    created_manifest, tmp_path: Path, capsys
) -> None:
    """Sync imports upstream state into only the selected local profile."""
    tool_root = _make_tool_root(tmp_path)
    upstream = tool_root / "profiles" / created_manifest.profile_name
    upstream.mkdir()
    (upstream / "metadata.yml").write_text("version: 1\n", encoding="utf-8")
    (upstream / "current_state.ss1").write_bytes(b"synced")

    exit_code = main(
        [
            "sync-gen3",
            "--profile",
            str(created_manifest.profile_root / "profile.json"),
            "--tool-root",
            str(tool_root),
        ]
    )

    assert exit_code == 0
    assert created_manifest.runtime_state.read_bytes() == b"synced"
    assert "profile synchronized" in capsys.readouterr().out


def test_sync_gen3_command_rejects_a_representable_gen2_manifest(
    created_manifest, tmp_path: Path, capsys
) -> None:
    """The CLI cannot sync an upstream Gen3 profile into a Gen2 manifest."""
    tool_root = _make_tool_root(tmp_path)
    upstream = tool_root / "profiles" / created_manifest.profile_name
    upstream.mkdir()
    (upstream / "current_state.ss1").write_bytes(b"gen2-unsafe")
    manifest_path = created_manifest.profile_root / "profile.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["game_family"] = "gen2"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")

    exit_code = main(
        [
            "sync-gen3",
            "--profile",
            str(manifest_path),
            "--tool-root",
            str(tool_root),
        ]
    )

    assert exit_code == 2
    assert not created_manifest.runtime_state.exists()
    assert "Gen 3" in capsys.readouterr().err


def test_launch_gen3_syncs_only_after_a_zero_exit(
    created_manifest, tmp_path: Path, monkeypatch
) -> None:
    """A clean bot exit copies its updated native state back to the profile."""
    tool_root = _make_tool_root(tmp_path)
    (created_manifest.bot_profile_dir / "metadata.yml").write_text(
        "version: 1\n", encoding="utf-8"
    )
    created_manifest.runtime_state.write_bytes(b"before")

    def harmless_runner(command: list[str], *, cwd: Path):
        assert command[-3:] == [
            "emerald-level-grind",
            "--bot-mode",
            "Level Grind",
        ]
        assert cwd == tool_root
        (tool_root / "profiles" / created_manifest.profile_name / "current_state.ss1").write_bytes(
            b"after"
        )
        return _ProcessResult(0)

    monkeypatch.setattr(cli_module, "_run_process", harmless_runner)

    exit_code = main(
        [
            "launch-gen3",
            "--profile",
            str(created_manifest.profile_root / "profile.json"),
            "--tool-root",
            str(tool_root),
            "--mode",
            "Level Grind",
        ]
    )

    assert exit_code == 0
    assert created_manifest.runtime_state.read_bytes() == b"after"
    assert created_manifest.source_path.read_bytes() == b"source-rom"


def test_launch_gen3_nonzero_exit_preserves_unsynced_upstream_state(
    created_manifest, tmp_path: Path, monkeypatch, capsys
) -> None:
    """A failed bot run reports recoverable upstream state without importing it."""
    tool_root = _make_tool_root(tmp_path)
    (created_manifest.bot_profile_dir / "metadata.yml").write_text(
        "version: 1\n", encoding="utf-8"
    )
    created_manifest.runtime_state.write_bytes(b"before")

    def failing_runner(command: list[str], *, cwd: Path):
        upstream_state = (
            tool_root
            / "profiles"
            / created_manifest.profile_name
            / "current_state.ss1"
        )
        upstream_state.write_bytes(b"recoverable")
        return _ProcessResult(7)

    monkeypatch.setattr(cli_module, "_run_process", failing_runner)

    exit_code = main(
        [
            "launch-gen3",
            "--profile",
            str(created_manifest.profile_root / "profile.json"),
            "--tool-root",
            str(tool_root),
            "--mode",
            "Level Grind",
        ]
    )

    upstream = tool_root / "profiles" / created_manifest.profile_name
    assert exit_code == 7
    assert created_manifest.runtime_state.read_bytes() == b"before"
    assert (upstream / "current_state.ss1").read_bytes() == b"recoverable"
    assert str(upstream) in capsys.readouterr().err
