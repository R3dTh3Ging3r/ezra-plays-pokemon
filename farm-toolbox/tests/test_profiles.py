"""Tests for creation of isolated farming profiles."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from pokemon_farm.hashing import sha256_file
from pokemon_farm.models import new_manifest
from pokemon_farm.profiles import create_profile, load_manifest


def test_create_profile_copies_rom_and_keeps_source_hash(tmp_path: Path) -> None:
    """Profile creation copies the ROM without modifying its source file."""
    source_rom = tmp_path / "emerald.gba"
    source_rom.write_bytes(b"source-rom")
    original_hash = sha256_file(source_rom)
    manifest = new_manifest(
        "emerald-level-grind",
        "emerald",
        source_rom,
        tmp_path / "profiles" / "emerald-level-grind",
    )

    created = create_profile(manifest)

    assert created.working_rom.read_bytes() == b"source-rom"
    assert sha256_file(source_rom) == original_hash
    assert (created.profile_root / "profile.json").is_file()


def test_create_profile_creates_only_profile_owned_directories(tmp_path: Path) -> None:
    """A new Gen 3 profile reserves its directories without inventing a save."""
    source_rom = tmp_path / "emerald.gba"
    source_rom.write_bytes(b"source-rom")
    manifest = new_manifest("emerald", "emerald", source_rom, tmp_path / "profile")

    created = create_profile(manifest)

    assert {path.name for path in created.profile_root.iterdir() if path.is_dir()} == {
        "backups",
        "bot-profile",
        "game",
        "logs",
        "save",
    }
    assert not created.runtime_state.exists()
    assert not any(created.profile_root.joinpath("save").iterdir())


def test_create_profile_writes_relative_forward_slash_manifest(tmp_path: Path) -> None:
    """The persisted manifest is portable within its profile root."""
    source_rom = tmp_path / "source files" / "emerald.gba"
    source_rom.parent.mkdir()
    source_rom.write_bytes(b"source-rom")
    manifest = new_manifest("emerald", "emerald", source_rom, tmp_path / "profiles" / "emerald")

    created = create_profile(manifest)

    data = json.loads((created.profile_root / "profile.json").read_text(encoding="utf-8"))
    assert data["profile_root"] == "."
    assert all("\\" not in value for value in data.values() if isinstance(value, str))
    assert all(not Path(value).is_absolute() for value in data.values() if isinstance(value, str))
    assert load_manifest(created.profile_root / "profile.json") == created


def test_load_manifest_round_trips_relative_input_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Relative source and root inputs produce a manifest that reloads identically."""
    monkeypatch.chdir(tmp_path)
    source_rom = Path("roms/emerald.gba")
    source_rom.parent.mkdir()
    source_rom.write_bytes(b"source-rom")
    manifest = new_manifest("emerald", "emerald", source_rom, Path("profiles/emerald"))

    created = create_profile(manifest)

    assert load_manifest(created.profile_root / "profile.json") == created


def test_load_manifest_rejects_a_serialized_profile_root_other_than_its_parent(
    created_manifest,
) -> None:
    """A manifest cannot replace the trusted directory containing profile.json."""
    manifest_path = created_manifest.profile_root / "profile.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["profile_root"] = "../outside"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="profile_root"):
        load_manifest(manifest_path)


@pytest.mark.parametrize(
    "field",
    ["working_rom", "bot_profile_dir", "runtime_state", "backups_dir", "logs_dir"],
)
def test_load_manifest_rejects_profile_owned_paths_outside_its_parent(
    created_manifest, field: str
) -> None:
    """Serialized profile-owned paths cannot redirect later writes externally."""
    manifest_path = created_manifest.profile_root / "profile.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data[field] = f"../../outside/{field}"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match=field):
        load_manifest(manifest_path)


def test_create_profile_rejects_an_existing_profile_root(tmp_path: Path) -> None:
    """An existing root cannot be silently overwritten by a second creation."""
    source_rom = tmp_path / "emerald.gba"
    source_rom.write_bytes(b"source-rom")
    manifest = new_manifest("emerald", "emerald", source_rom, tmp_path / "profile")
    create_profile(manifest)

    with pytest.raises(FileExistsError, match="profile root already exists"):
        create_profile(manifest)


def test_create_profile_rejects_a_source_digest_that_changes(tmp_path: Path) -> None:
    """Creation stops when its post-copy source digest differs from the manifest."""
    source_rom = tmp_path / "emerald.gba"
    source_rom.write_bytes(b"source-rom")
    manifest = new_manifest("emerald", "emerald", source_rom, tmp_path / "profile")

    with pytest.raises(RuntimeError, match="source ROM changed during profile creation"):
        create_profile(replace(manifest, source_sha256="not-the-source-digest"))
