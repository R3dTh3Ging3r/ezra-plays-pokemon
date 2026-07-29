"""Creation and persistence for isolated Pokemon farming profiles."""

import json
import os
import shutil
from pathlib import Path

from pokemon_farm.hashing import sha256_file
from pokemon_farm.models import GameFamily, ProfileManifest


_MANIFEST_FILENAME = "profile.json"
_PATH_FIELDS = (
    "source_path",
    "profile_root",
    "working_rom",
    "bot_profile_dir",
    "runtime_state",
    "backups_dir",
    "logs_dir",
)


def create_profile(manifest: ProfileManifest) -> ProfileManifest:
    """Create a profile-owned ROM copy and persist its manifest."""
    if manifest.profile_root.exists():
        raise FileExistsError(f"profile root already exists: {manifest.profile_root}")

    manifest.profile_root.mkdir(parents=True)
    for directory in (
        manifest.working_rom.parent,
        manifest.bot_profile_dir,
        manifest.profile_root / "save",
        manifest.backups_dir,
        manifest.logs_dir,
    ):
        directory.mkdir()

    shutil.copy2(manifest.source_path, manifest.working_rom)
    if sha256_file(manifest.source_path) != manifest.source_sha256:
        raise RuntimeError("source ROM changed during profile creation")

    _write_manifest(manifest)
    return manifest


def load_manifest(path: Path) -> ProfileManifest:
    """Load a profile manifest whose locations are relative to its root."""
    path = Path(path)
    profile_root = path.parent.resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    paths = {
        field: (profile_root / data[field]).resolve()
        for field in _PATH_FIELDS
    }
    return ProfileManifest(
        profile_name=data["profile_name"],
        game_id=data["game_id"],
        game_family=GameFamily(data["game_family"]),
        source_sha256=data["source_sha256"],
        **paths,
    )


def _write_manifest(manifest: ProfileManifest) -> None:
    root = manifest.profile_root.resolve()
    data = {
        "profile_name": manifest.profile_name,
        "game_id": manifest.game_id,
        "game_family": manifest.game_family.value,
        "source_sha256": manifest.source_sha256,
    }
    data.update(
        {
            field: Path(os.path.relpath(getattr(manifest, field), root)).as_posix()
            for field in _PATH_FIELDS
        }
    )
    (root / _MANIFEST_FILENAME).write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
