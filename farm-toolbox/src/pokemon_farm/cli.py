"""Command-line management for isolated Pokemon farming profiles."""

import argparse
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from pokemon_farm.backups import backup_runtime_state, restore_backup
from pokemon_farm.gen3 import (
    build_gen3_command,
    preflight_gen3,
    stage_gen3_profile,
    stage_gen3_rom,
    sync_gen3_profile,
)
from pokemon_farm.hashing import sha256_file
from pokemon_farm.models import new_manifest
from pokemon_farm.profiles import create_profile, load_manifest


_run_process = subprocess.run


def _profile_root_for(profile_name: str, profiles_root: Path) -> Path:
    """Return a profile-owned root for one safe profile-name component."""
    if (
        not profile_name.strip()
        or profile_name in {".", ".."}
        or "/" in profile_name
        or "\\" in profile_name
        or profile_name.endswith((".", " "))
        or any(character in profile_name for character in '<>:"|?*')
        or any(ord(character) < 32 for character in profile_name)
    ):
        raise ValueError("profile name must be one safe filename component")

    resolved_profiles_root = profiles_root.resolve()
    profile_root = (resolved_profiles_root / profile_name).resolve()
    if not profile_root.is_relative_to(resolved_profiles_root):
        raise ValueError("profile root must remain within profiles root")
    return profile_root


def _create(args: argparse.Namespace) -> int:
    """Create one profile from an explicitly supplied source ROM."""
    profile_root = _profile_root_for(args.name, Path(args.profiles_root))
    manifest = new_manifest(
        args.name,
        args.game,
        Path(args.rom),
        profile_root,
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


def _provision_gen3(args: argparse.Namespace) -> int:
    """Stage a ROM and open native PokeBot profile provisioning."""
    manifest = load_manifest(Path(args.profile))
    tool_root = Path(args.tool_root).resolve()
    staged_rom = stage_gen3_rom(manifest, tool_root)
    print(f"ROM staged: {staged_rom}")

    result = _run_process(
        build_gen3_command(tool_root, None, None),
        cwd=tool_root,
    )
    upstream_profile = tool_root / "profiles" / manifest.profile_name
    if upstream_profile.is_dir():
        sync_gen3_profile(manifest, tool_root)
        print(f"profile synchronized: {manifest.bot_profile_dir}")
    else:
        print(
            "manual PokeBot profile creation is still required at: "
            f"{upstream_profile}"
        )
    return result.returncode


def _sync_gen3(args: argparse.Namespace) -> int:
    """Copy the selected upstream PokeBot profile back into local ownership."""
    manifest = load_manifest(Path(args.profile))
    tool_root = Path(args.tool_root).resolve()
    sync_gen3_profile(manifest, tool_root)
    print(f"profile synchronized: {manifest.bot_profile_dir}")
    return 0


def _launch_gen3(args: argparse.Namespace) -> int:
    """Launch a validated profile and sync it after a clean exit."""
    manifest = load_manifest(Path(args.profile))
    tool_root = Path(args.tool_root).resolve()
    preflight_gen3(manifest, tool_root)
    staged_rom = stage_gen3_profile(manifest, tool_root)
    print(f"ROM staged: {staged_rom}")

    result = _run_process(
        build_gen3_command(tool_root, manifest.profile_name, args.mode),
        cwd=tool_root,
    )
    upstream_profile = tool_root / "profiles" / manifest.profile_name
    if result.returncode == 0:
        sync_gen3_profile(manifest, tool_root)
        print(f"profile synchronized: {manifest.bot_profile_dir}")
    else:
        print(
            "PokeBot exited nonzero; recoverable upstream profile retained at: "
            f"{upstream_profile}",
            file=sys.stderr,
        )
    return result.returncode


def _add_gen3_profile_arguments(parser: argparse.ArgumentParser) -> None:
    """Add explicit profile and PokeBot checkout arguments."""
    parser.add_argument("--profile", required=True, help="path to profile.json")
    parser.add_argument(
        "--tool-root",
        required=True,
        help="path to the isolated PokeBot Gen3 checkout",
    )


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

    provision_gen3 = commands.add_parser(
        "provision-gen3",
        help="stage a ROM and open one-time native PokeBot provisioning",
    )
    _add_gen3_profile_arguments(provision_gen3)
    provision_gen3.set_defaults(handler=_provision_gen3)

    sync_gen3 = commands.add_parser(
        "sync-gen3",
        help="copy an upstream PokeBot profile back into local ownership",
    )
    _add_gen3_profile_arguments(sync_gen3)
    sync_gen3.set_defaults(handler=_sync_gen3)

    launch_gen3 = commands.add_parser(
        "launch-gen3",
        help="launch a validated native PokeBot profile",
    )
    _add_gen3_profile_arguments(launch_gen3)
    launch_gen3.add_argument("--mode", required=True, help="native PokeBot mode")
    launch_gen3.set_defaults(handler=_launch_gen3)
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
