"""Immutable metadata for isolated Pokemon farming profiles."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final, Literal

from pokemon_farm.hashing import sha256_file


GameId = Literal["ruby", "sapphire", "emerald", "firered", "leafgreen"]

GEN3_GAME_IDS: Final[frozenset[GameId]] = frozenset(
    {"ruby", "sapphire", "emerald", "firered", "leafgreen"}
)


class GameFamily(StrEnum):
    """Pokemon game generations supported by the toolbox."""

    GEN2 = "gen2"
    GEN3 = "gen3"


@dataclass(frozen=True)
class ProfileManifest:
    """All source and profile-owned locations for one farm profile."""

    profile_name: str
    game_id: GameId
    game_family: GameFamily
    source_path: Path
    source_sha256: str
    profile_root: Path
    working_rom: Path
    bot_profile_dir: Path
    runtime_state: Path
    backups_dir: Path
    logs_dir: Path


def new_manifest(
    profile_name: str, game_id: str, source_path: Path, profile_root: Path
) -> ProfileManifest:
    """Build the immutable manifest for a supported Gen 3 profile."""
    if game_id not in GEN3_GAME_IDS:
        raise ValueError(f"{game_id} is not supported by the Gen 3 launcher")

    typed_game_id: GameId = game_id
    source_path = Path(source_path)
    profile_root = Path(profile_root)
    bot_profile_dir = profile_root / "bot-profile"
    return ProfileManifest(
        profile_name=profile_name,
        game_id=typed_game_id,
        game_family=GameFamily.GEN3,
        source_path=source_path,
        source_sha256=sha256_file(source_path),
        profile_root=profile_root,
        working_rom=profile_root / "game" / f"{typed_game_id}{source_path.suffix}",
        bot_profile_dir=bot_profile_dir,
        runtime_state=bot_profile_dir / "current_state.ss1",
        backups_dir=profile_root / "backups",
        logs_dir=profile_root / "logs",
    )
