"""Command-line management for isolated Pokemon farming profiles."""

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from pokemon_farm.backups import backup_runtime_state, restore_backup
from pokemon_farm.hashing import sha256_file
from pokemon_farm.models import new_manifest
from pokemon_farm.profiles import create_profile, load_manifest


def _create(args: argparse.Namespace) -> int:
    """Create one profile from an explicitly supplied source ROM."""
    manifest = new_manifest(
        args.name,
        args.game,
        Path(args.rom),
        Path(args.profiles_root) / args.name,
    )
    created = create_profile(manifest)
    print(f"profile created: {created.profile_root}")
    return 0


def _verify(args: argparse.Namespace) -> int:
    """Report a manifest's source integrity and profile-owned state."""
    manifest = load_manifest(Path(args.profile))
    current_hash = sha256_file(manifest.source_path)
    source_matches = current_hash == manifest.source_sha256
    provisioning_status = (
        "provisioned" if manifest.runtime_state.is_file() else "unprovisioned"
    )
    backup_count = sum(1 for path in manifest.backups_dir.glob("*.ss1") if path.is_file())

    print(
        "source hash: "
        f"recorded={manifest.source_sha256} current={current_hash} "
        f"status={'match' if source_matches else 'mismatch'}"
    )
    print(f"working ROM path: {manifest.working_rom}")
    print(f"native PokeBot state path: {manifest.runtime_state}")
    print(f"provisioning status: {provisioning_status}")
    print(f"backup count: {backup_count}")
    if not source_matches:
        print("source hash mismatch", file=sys.stderr)
        return 1
    return 0


def _backup(args: argparse.Namespace) -> int:
    """Create a timestamped backup of the profile's native runtime state."""
    manifest = load_manifest(Path(args.profile))
    backup = backup_runtime_state(manifest, lambda: datetime.now(UTC), args.label)
    print(f"backup created: {backup}")
    return 0


def _restore(args: argparse.Namespace) -> int:
    """Restore the selected profile-local runtime-state backup."""
    manifest = load_manifest(Path(args.profile))
    backup = Path(args.backup)
    restore_backup(manifest, backup)
    print(f"backup restored: {backup}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Build the parser used by the console script and tests."""
    parser = argparse.ArgumentParser(prog="pokemon-farm")
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="create an isolated profile")
    create.add_argument("--name", required=True, help="profile name")
    create.add_argument("--game", required=True, help="Gen 3 game identifier")
    create.add_argument("--rom", required=True, help="path to the source ROM")
    create.add_argument(
        "--profiles-root", required=True, help="directory containing profile directories"
    )
    create.set_defaults(handler=_create)

    verify = commands.add_parser("verify", help="verify one profile manifest")
    verify.add_argument("--profile", required=True, help="path to profile.json")
    verify.set_defaults(handler=_verify)

    backup = commands.add_parser("backup", help="back up native runtime state")
    backup.add_argument("--profile", required=True, help="path to profile.json")
    backup.add_argument("--label", default="before-run", help="safe backup label")
    backup.set_defaults(handler=_backup)

    restore = commands.add_parser("restore", help="restore native runtime state")
    restore.add_argument("--profile", required=True, help="path to profile.json")
    restore.add_argument(
        "--backup",
        required=True,
        help="path to a backup inside this profile's backups directory",
    )
    restore.set_defaults(handler=_restore)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the profile-management CLI and return its process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (FileNotFoundError, FileExistsError, OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
