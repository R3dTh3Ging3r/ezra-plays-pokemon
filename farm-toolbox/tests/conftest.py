"""Shared pytest configuration for the farm toolbox test suite."""

from pathlib import Path

import pytest

from pokemon_farm.models import new_manifest
from pokemon_farm.profiles import create_profile


@pytest.fixture
def created_manifest(tmp_path: Path):
    """Provide a newly created isolated Emerald profile."""
    source_rom = tmp_path / "emerald.gba"
    source_rom.write_bytes(b"source-rom")
    manifest = new_manifest(
        "emerald-level-grind",
        "emerald",
        source_rom,
        tmp_path / "profiles" / "emerald-level-grind",
    )
    return create_profile(manifest)
