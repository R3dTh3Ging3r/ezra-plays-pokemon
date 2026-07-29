"""Safe staging and synchronization for an isolated PokeBot Gen3 checkout."""

import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from pokemon_farm.backups import backup_runtime_state
from pokemon_farm.hashing import sha256_file
from pokemon_farm.models import GameFamily, ProfileManifest


def _is_redirect(path: Path) -> bool:
    """Return whether a path can redirect file operations elsewhere."""
    return path.is_symlink() or path.is_junction()


def _validate_profile_name(profile_name: str) -> None:
    """Require one Windows-safe component for upstream profile and ROM names."""
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


def _contained_directory(root: Path, relative: Path, label: str) -> Path:
    """Return an existing real directory contained by a selected root."""
    root = Path(root).resolve()
    candidate = root / relative
    if _is_redirect(candidate):
        raise ValueError(f"{label} cannot be a symlink")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"{label} must remain within the PokeBot tool root")
    if not resolved.is_dir():
        raise FileNotFoundError(f"{label} directory is absent: {candidate}")
    return resolved


def _required_file(path: Path, label: str) -> Path:
    """Return an existing regular file without accepting a symlink."""
    if _is_redirect(path):
        raise ValueError(f"{label} cannot be a symlink")
    if not path.is_file():
        raise FileNotFoundError(f"{label} is absent: {path}")
    return path


def _validate_tool_install(tool_root: Path) -> tuple[Path, Path]:
    """Validate the fixed upstream program, interpreter, and ROM directory."""
    root = Path(tool_root).resolve()
    _required_file(root / "pokebot.py", "PokeBot pokebot.py")
    _required_file(
        root / ".venv" / "Scripts" / "python.exe",
        "PokeBot .venv Scripts python.exe",
    )
    roms_dir = _contained_directory(root, Path("roms"), "PokeBot roms")
    return root, roms_dir


def _validate_manifest_source(manifest: ProfileManifest) -> None:
    """Validate generation, profile naming, and immutable source integrity."""
    if manifest.game_family is not GameFamily.GEN3:
        raise ValueError("only a Gen 3 manifest can be staged for PokeBot Gen3")
    _validate_profile_name(manifest.profile_name)
    if sha256_file(manifest.source_path) != manifest.source_sha256:
        raise RuntimeError("source ROM hash mismatch; refusing to stage it")


def _upstream_profiles_dir(tool_root: Path) -> Path:
    """Return the validated upstream profiles directory."""
    root = Path(tool_root).resolve()
    return _contained_directory(root, Path("profiles"), "PokeBot profiles")


def _upstream_profile(manifest: ProfileManifest, tool_root: Path) -> Path:
    """Return a contained upstream directory path for the manifest."""
    _validate_profile_name(manifest.profile_name)
    profiles_dir = _upstream_profiles_dir(tool_root)
    profile = profiles_dir / manifest.profile_name
    if _is_redirect(profile):
        raise ValueError("upstream profile cannot be a symlink")
    if not profile.resolve().is_relative_to(profiles_dir):
        raise ValueError("upstream profile must remain within PokeBot profiles")
    return profile


def _local_bot_profile(manifest: ProfileManifest) -> Path:
    """Return the profile-owned bot directory without following a redirect."""
    local_profile = manifest.bot_profile_dir
    if _is_redirect(local_profile):
        raise ValueError("bot profile destination cannot be a symlink")
    resolved = local_profile.resolve()
    if not resolved.is_relative_to(manifest.profile_root.resolve()):
        raise ValueError("bot profile must remain within the selected profile")
    if not resolved.is_dir():
        raise FileNotFoundError(f"bot profile directory is absent: {local_profile}")
    return resolved


def _copy_tree_without_deleting(source: Path, destination: Path) -> None:
    """Copy a real directory tree while retaining destination-only files."""
    if _is_redirect(source) or _is_redirect(destination):
        raise ValueError("profile synchronization cannot use symlinked directories")
    if not source.is_dir():
        raise FileNotFoundError(f"profile directory is absent: {source}")

    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()
    for source_path in source.rglob("*"):
        if _is_redirect(source_path):
            raise ValueError(f"profile synchronization cannot copy symlink: {source_path}")
        relative = source_path.relative_to(source)
        destination_path = destination / relative
        if _is_redirect(destination_path):
            raise ValueError(
                f"profile synchronization cannot overwrite symlink: {destination_path}"
            )
        if not destination_path.resolve().is_relative_to(destination_root):
            raise ValueError("profile copy destination escaped its selected root")
        if source_path.is_dir():
            destination_path.mkdir(exist_ok=True)
        elif source_path.is_file():
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)


def stage_gen3_rom(manifest: ProfileManifest, tool_root: Path) -> Path:
    """Verify and atomically stage a uniquely named ROM copy for PokeBot."""
    _, roms_dir = _validate_tool_install(tool_root)
    _validate_manifest_source(manifest)

    staged_rom = roms_dir / f"{manifest.profile_name}{manifest.source_path.suffix}"
    if _is_redirect(staged_rom):
        raise ValueError("staged ROM destination cannot be a symlink")
    if not staged_rom.resolve().is_relative_to(roms_dir):
        raise ValueError("staged ROM must remain within PokeBot roms")

    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=roms_dir, prefix=f".{manifest.profile_name}-", suffix=".staging"
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    try:
        shutil.copy2(manifest.source_path, temporary_path)
        if (
            sha256_file(manifest.source_path) != manifest.source_sha256
            or sha256_file(temporary_path) != manifest.source_sha256
        ):
            raise RuntimeError("source ROM changed while it was being staged")
        os.replace(temporary_path, staged_rom)
    finally:
        temporary_path.unlink(missing_ok=True)
    return staged_rom


def preflight_gen3(manifest: ProfileManifest, tool_root: Path) -> None:
    """Validate that the tool and local native profile are launch-ready."""
    _validate_tool_install(tool_root)
    _upstream_profiles_dir(tool_root)
    _validate_manifest_source(manifest)
    local_profile = _local_bot_profile(manifest)
    _required_file(local_profile / "metadata.yml", "bot profile metadata.yml")
    resolved_runtime_state = manifest.runtime_state.resolve()
    if not resolved_runtime_state.is_relative_to(local_profile):
        raise ValueError("runtime state must remain within the bot profile")
    _required_file(manifest.runtime_state, "bot profile current_state.ss1")


def stage_gen3_profile(manifest: ProfileManifest, tool_root: Path) -> Path:
    """Back up and copy a provisioned local profile into PokeBot."""
    preflight_gen3(manifest, tool_root)
    staged_rom = stage_gen3_rom(manifest, tool_root)
    backup_runtime_state(
        manifest,
        lambda: datetime.now(UTC),
        "before-gen3-stage",
    )
    upstream_profile = _upstream_profile(manifest, tool_root)
    _copy_tree_without_deleting(_local_bot_profile(manifest), upstream_profile)
    return staged_rom


def sync_gen3_profile(manifest: ProfileManifest, tool_root: Path) -> None:
    """Copy upstream PokeBot profile changes back without deleting local files."""
    upstream_profile = _upstream_profile(manifest, tool_root)
    if not upstream_profile.is_dir():
        raise FileNotFoundError(f"upstream PokeBot profile is absent: {upstream_profile}")
    _copy_tree_without_deleting(upstream_profile, _local_bot_profile(manifest))


def build_gen3_command(
    tool_root: Path, profile_name: str | None, mode: str | None
) -> list[str]:
    """Build the bare provisioning command or a fully selected launch command."""
    command = [
        str(Path(tool_root) / ".venv" / "Scripts" / "python.exe"),
        "pokebot.py",
    ]
    if profile_name is None and mode is None:
        return command
    if (
        profile_name is None
        or mode is None
        or not profile_name.strip()
        or not mode.strip()
    ):
        raise ValueError("profile and mode must both be nonblank for launch")
    _validate_profile_name(profile_name)
    return [*command, profile_name, "--bot-mode", mode]
