"""Tests for supported-game profile manifests."""

from pathlib import Path

import pytest

from pokemon_farm.hashing import sha256_file
from pokemon_farm.models import GameFamily, new_manifest


def test_manifest_maps_emerald_to_gen3(tmp_path: Path) -> None:
    """Emerald profiles carry the Gen 3 classification and source digest."""
    rom = tmp_path / "emerald.gba"
    rom.write_bytes(b"ROM")

    manifest = new_manifest("emerald-level-grind", "emerald", rom, tmp_path / "profile")

    assert manifest.game_family is GameFamily.GEN3
    assert manifest.source_sha256 == sha256_file(rom)


def test_manifest_rejects_a_gen2_game_id(tmp_path: Path) -> None:
    """The Gen 3 launcher refuses unsupported Gen 2 game identifiers."""
    rom = tmp_path / "crystal.gbc"
    rom.write_bytes(b"ROM")

    with pytest.raises(ValueError, match="not supported by the Gen 3 launcher"):
        new_manifest("crystal-fishing", "crystal", rom, tmp_path / "profile")
