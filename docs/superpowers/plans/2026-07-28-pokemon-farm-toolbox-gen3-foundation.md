# Pokemon Farm Toolbox Gen 3 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows-local profile manager and connect it to PokeBot Gen3 so each Gen 3 farming run uses a copied game/save plus a pre-run backup.

**Architecture:** A small Python package owns game-family metadata, immutable source hashes, per-profile manifests, working copies, backups, restore operations, and command preflight. PokeBot Gen3 remains an unmodified upstream tool; the package stages a profile into the tool's expected directories and builds a launch command only after validating the profile.

**Tech Stack:** Windows 10/11, Python 3.13, standard library, pytest, PokeBot Gen3, Git.

## Global Constraints

- Support only Ruby, Sapphire, Emerald, FireRed, and LeafGreen in this plan.
- Never download, distribute, modify, or commit ROM files.
- Treat `Pokemon Roms/` as user data: do not move it, edit it, or add it to Git.
- Each profile owns its copied game file, PokeBot profile/state, logs, manifest, and backups.
- Record a SHA-256 hash of each source game file before profile creation and verify it after every profile copy.
- Treat PokeBot Gen3's `current_state.ss1` as its working save; create a timestamped copy before every staged bot launch.
- Use only modes PokeBot Gen3 exposes for the selected game/profile.
- Do not delete a backup or working state in an automated path.

---

## File Structure

```text
.gitignore
farm-toolbox/
  pyproject.toml
  README.md
  src/pokemon_farm/
    __init__.py
    models.py
    hashing.py
    profiles.py
    backups.py
    gen3.py
    cli.py
  tests/
    conftest.py
    test_models.py
    test_profiles.py
    test_backups.py
    test_gen3.py
    test_cli.py
  tools/
    pokebot-gen3/             # ignored upstream checkout or release archive
  profiles/                   # ignored mutable profile data
```

### Task 1: Bootstrap the isolated Python project

**Files:**
- Create: `.gitignore`
- Create: `farm-toolbox/pyproject.toml`
- Create: `farm-toolbox/src/pokemon_farm/__init__.py`
- Create: `farm-toolbox/tests/conftest.py`
- Create: `farm-toolbox/tests/test_imports.py`

**Interfaces:**
- Produces: an installable `pokemon_farm` package and a repeatable `pytest` command for all later tasks.

- [ ] **Step 1: Install Python 3.13 and create a virtual environment**

Run:

```powershell
winget install --exact --id Python.Python.3.13 --source winget
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip pytest
```

Expected: `python --version` reports Python 3.13 and `pytest --version` exits with code 0.

- [ ] **Step 2: Write the failing import test**

```python
# farm-toolbox/tests/test_imports.py
def test_package_imports() -> None:
    import pokemon_farm

    assert pokemon_farm.__version__ == "0.1.0"
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python -m pytest farm-toolbox/tests/test_imports.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'pokemon_farm'`.

- [ ] **Step 4: Add the minimal package and project configuration**

```toml
# farm-toolbox/pyproject.toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "pokemon-farm-toolbox"
version = "0.1.0"
requires-python = ">=3.13"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

```python
# farm-toolbox/src/pokemon_farm/__init__.py
__version__ = "0.1.0"
```

Add these ignore rules:

```gitignore
.venv/
Pokemon Roms/
farm-toolbox/profiles/
farm-toolbox/tools/
__pycache__/
.pytest_cache/
```

- [ ] **Step 5: Run the test and commit the bootstrap**

Run: `python -m pytest farm-toolbox/tests/test_imports.py -q`

Expected: PASS.

```powershell
git add .gitignore farm-toolbox/pyproject.toml farm-toolbox/src/pokemon_farm/__init__.py farm-toolbox/tests/test_imports.py
git commit -m "feat: bootstrap farm toolbox"
```

### Task 2: Define supported games and immutable profile manifests

**Files:**
- Create: `farm-toolbox/src/pokemon_farm/models.py`
- Create: `farm-toolbox/src/pokemon_farm/hashing.py`
- Create: `farm-toolbox/tests/test_models.py`

**Interfaces:**
- Produces: `GameId`, `GameFamily`, `ProfileManifest`, `sha256_file(path: Path) -> str`, and `new_manifest(...) -> ProfileManifest`.
- Consumed by: profile creation, backups, Gen 3 staging, and CLI commands.

- [ ] **Step 1: Write failing supported-game and source-hash tests**

```python
from pathlib import Path

import pytest

from pokemon_farm.hashing import sha256_file
from pokemon_farm.models import GameFamily, new_manifest


def test_manifest_maps_emerald_to_gen3(tmp_path: Path) -> None:
    rom = tmp_path / "emerald.gba"
    rom.write_bytes(b"ROM")

    manifest = new_manifest("emerald-level-grind", "emerald", rom, tmp_path / "profile")

    assert manifest.game_family is GameFamily.GEN3
    assert manifest.source_sha256 == sha256_file(rom)


def test_manifest_rejects_a_gen2_game_id(tmp_path: Path) -> None:
    rom = tmp_path / "crystal.gbc"
    rom.write_bytes(b"ROM")

    with pytest.raises(ValueError, match="not supported by the Gen 3 launcher"):
        new_manifest("crystal-fishing", "crystal", rom, tmp_path / "profile")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest farm-toolbox/tests/test_models.py -q`

Expected: FAIL because `pokemon_farm.models` and `pokemon_farm.hashing` do not exist.

- [ ] **Step 3: Implement immutable model and hash helpers**

Implement `GameFamily` as a `StrEnum` with `GEN2 = "gen2"` and `GEN3 = "gen3"`; define the five Gen 3 game IDs in a module-level frozen set. Make `ProfileManifest` a frozen dataclass with `profile_name`, `game_id`, `game_family`, `source_path`, `source_sha256`, `profile_root`, `working_rom`, `bot_profile_dir`, `runtime_state`, `backups_dir`, and `logs_dir` fields. For Gen 3, derive `bot_profile_dir` as `<profile-root>/bot-profile` and `runtime_state` as `<bot-profile-dir>/current_state.ss1`. Implement `sha256_file()` with `hashlib.sha256()` and 1 MiB reads. `new_manifest()` must reject a game ID outside the Gen 3 set and derive all profile-owned paths from `profile_root`.

- [ ] **Step 4: Run model tests**

Run: `python -m pytest farm-toolbox/tests/test_models.py -q`

Expected: PASS.

- [ ] **Step 5: Commit game metadata**

```powershell
git add farm-toolbox/src/pokemon_farm/models.py farm-toolbox/src/pokemon_farm/hashing.py farm-toolbox/tests/test_models.py
git commit -m "feat: define Gen 3 profile manifests"
```

### Task 3: Create copied profiles without touching source games

**Files:**
- Create: `farm-toolbox/src/pokemon_farm/profiles.py`
- Create: `farm-toolbox/tests/test_profiles.py`

**Interfaces:**
- Consumes: `ProfileManifest`, `new_manifest`, and `sha256_file`.
- Produces: `create_profile(manifest: ProfileManifest) -> ProfileManifest` and `load_manifest(path: Path) -> ProfileManifest`.

- [ ] **Step 1: Write a failing source-integrity test**

```python
from pathlib import Path

from pokemon_farm.hashing import sha256_file
from pokemon_farm.models import new_manifest
from pokemon_farm.profiles import create_profile


def test_create_profile_copies_rom_and_keeps_source_hash(tmp_path: Path) -> None:
    source_rom = tmp_path / "emerald.gba"
    source_rom.write_bytes(b"source-rom")
    original_hash = sha256_file(source_rom)
    manifest = new_manifest("emerald-level-grind", "emerald", source_rom, tmp_path / "profiles" / "emerald-level-grind")

    created = create_profile(manifest)

    assert created.working_rom.read_bytes() == b"source-rom"
    assert sha256_file(source_rom) == original_hash
    assert (created.profile_root / "profile.json").is_file()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest farm-toolbox/tests/test_profiles.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'pokemon_farm.profiles'`.

- [ ] **Step 3: Implement profile creation**

Create `game/`, `bot-profile/`, `save/`, `backups/`, and `logs/` inside the profile root. Use `shutil.copy2()` to copy the source ROM to `game/<game_id><source suffix>`. Serialize the manifest as UTF-8 JSON with forward-slash relative paths only. Do not manufacture a Gen 3 `.sav`: PokeBot operates on a native profile and `current_state.ss1`, which the provisioning step creates or imports; the empty `save/` directory is reserved for the Gen 2 extension. Add this reusable test fixture to `tests/conftest.py` after the profile test passes:

```python
import pytest


@pytest.fixture
def created_manifest(tmp_path: Path):
    source_rom = tmp_path / "emerald.gba"
    source_rom.write_bytes(b"source-rom")
    manifest = new_manifest("emerald-level-grind", "emerald", source_rom, tmp_path / "profiles" / "emerald-level-grind")
    return create_profile(manifest)
```

Import `Path`, `new_manifest`, and `create_profile` in that file. Rehash the source after each copy and raise `RuntimeError` when it differs from `source_sha256`. Reject an existing profile root to prevent silently overwriting a run.

- [ ] **Step 4: Run the profile test**

Run: `python -m pytest farm-toolbox/tests/test_profiles.py -q`

Expected: PASS.

- [ ] **Step 5: Commit profile isolation**

```powershell
git add farm-toolbox/src/pokemon_farm/profiles.py farm-toolbox/tests/test_profiles.py
git commit -m "feat: create isolated farm profiles"
```

### Task 4: Back up and restore only the Gen 3 runtime state

**Files:**
- Create: `farm-toolbox/src/pokemon_farm/backups.py`
- Create: `farm-toolbox/tests/test_backups.py`

**Interfaces:**
- Consumes: `ProfileManifest`.
- Produces: `backup_runtime_state(manifest: ProfileManifest, clock: Callable[[], datetime], label: str = "before-run") -> Path` and `restore_backup(manifest: ProfileManifest, backup: Path) -> None`.

- [ ] **Step 1: Write failing backup and restore tests**

```python
from datetime import UTC, datetime
from pathlib import Path

from pokemon_farm.backups import backup_runtime_state, restore_backup


def test_backup_and_restore_touch_only_runtime_state(created_manifest) -> None:
    created_manifest.runtime_state.write_bytes(b"before-run")
    backup = backup_runtime_state(created_manifest, lambda: datetime(2026, 7, 28, 20, 0, tzinfo=UTC))
    created_manifest.runtime_state.write_bytes(b"after-run")

    restore_backup(created_manifest, backup)

    assert backup.name == "20260728T200000Z-before-run.ss1"
    assert created_manifest.runtime_state.read_bytes() == b"before-run"
    assert created_manifest.source_path.read_bytes() == b"source-rom"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest farm-toolbox/tests/test_backups.py -q`

Expected: FAIL because `pokemon_farm.backups` does not exist.

- [ ] **Step 3: Implement backup and restore**

Use `shutil.copy2()` and create backup names with the exact UTC format `YYYYMMDDTHHMMSSZ-before-run.ss1`. `backup_runtime_state()` must raise `FileNotFoundError` before launch when the native PokeBot state is absent. `restore_backup()` must require a file inside `manifest.backups_dir`, then copy it only to `manifest.runtime_state`; it must never write to `manifest.source_path`.

- [ ] **Step 4: Run backup tests**

Run: `python -m pytest farm-toolbox/tests/test_backups.py -q`

Expected: PASS.

- [ ] **Step 5: Commit safe save recovery**

```powershell
git add farm-toolbox/src/pokemon_farm/backups.py farm-toolbox/tests/test_backups.py
git commit -m "feat: add pre-run save backups"
```

### Task 5: Provide a profile-management CLI

**Files:**
- Create: `farm-toolbox/src/pokemon_farm/cli.py`
- Create: `farm-toolbox/tests/test_cli.py`
- Modify: `farm-toolbox/pyproject.toml`
- Modify: `farm-toolbox/README.md`

**Interfaces:**
- Consumes: profile and backup interfaces from Tasks 2-4.
- Produces: `pokemon-farm create`, `pokemon-farm verify`, `pokemon-farm backup`, and `pokemon-farm restore` commands.

- [ ] **Step 1: Write a failing CLI creation test**

```python
from pathlib import Path

from pokemon_farm.cli import main


def test_create_command_makes_a_profile(tmp_path: Path, capsys) -> None:
    rom = tmp_path / "emerald.gba"
    rom.write_bytes(b"source-rom")

    exit_code = main([
        "create", "--name", "emerald-level-grind", "--game", "emerald",
        "--rom", str(rom), "--profiles-root", str(tmp_path / "profiles"),
    ])

    assert exit_code == 0
    assert "profiles\\emerald-level-grind" in capsys.readouterr().out
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest farm-toolbox/tests/test_cli.py -q`

Expected: FAIL because `pokemon_farm.cli` does not exist.

- [ ] **Step 3: Implement the commands and documentation**

Use `argparse` with no implicit default source directory. Add a `[project.scripts]` entry `pokemon-farm = "pokemon_farm.cli:main"`. `verify` prints source hash, working ROM path, native PokeBot state path, provisioning status, and backup count; it exits nonzero if the source hash differs. Document exact create, verify, backup, and restore examples in `README.md` using the profile name `emerald-level-grind`.

- [ ] **Step 4: Run all foundation tests**

Run: `python -m pytest farm-toolbox/tests -q`

Expected: PASS.

- [ ] **Step 5: Commit CLI support**

```powershell
git add farm-toolbox/pyproject.toml farm-toolbox/src/pokemon_farm/cli.py farm-toolbox/tests/test_cli.py farm-toolbox/README.md
git commit -m "feat: add profile management CLI"
```

### Task 6: Stage and launch PokeBot Gen3 from a validated profile

**Files:**
- Create: `farm-toolbox/src/pokemon_farm/gen3.py`
- Create: `farm-toolbox/tests/test_gen3.py`
- Modify: `farm-toolbox/src/pokemon_farm/cli.py`
- Modify: `farm-toolbox/tests/test_cli.py`
- Modify: `farm-toolbox/README.md`

**Interfaces:**
- Consumes: `ProfileManifest`, `backup_runtime_state`, and `sha256_file`.
- Produces: `stage_gen3_rom(manifest: ProfileManifest, tool_root: Path) -> Path`, `stage_gen3_profile(manifest: ProfileManifest, tool_root: Path) -> Path`, `sync_gen3_profile(manifest: ProfileManifest, tool_root: Path) -> None`, `build_gen3_command(tool_root: Path, profile_name: str | None, mode: str | None) -> list[str]`, `preflight_gen3(manifest: ProfileManifest, tool_root: Path) -> None`, and CLI commands `provision-gen3`, `sync-gen3`, and `launch-gen3`.

- [ ] **Step 1: Install the upstream tool outside Git tracking**

Run:

```powershell
git clone https://github.com/40Cakes/pokebot-gen3.git farm-toolbox/tools/pokebot-gen3
cd farm-toolbox/tools/pokebot-gen3
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe .\pokebot.py
```

Expected: `farm-toolbox/tools/pokebot-gen3/pokebot.py` exists. On its first run, PokeBot checks and installs its own declared dependencies and libmGBA in its isolated virtual environment. Do not alter any upstream source file.

- [ ] **Step 2: Write failing staging and command tests**

```python
from pathlib import Path

from pokemon_farm.gen3 import build_gen3_command, stage_gen3_profile


def test_stage_gen3_profile_uses_a_profile_copy(created_manifest, tmp_path: Path) -> None:
    (created_manifest.bot_profile_dir / "metadata.yml").write_text("version: 1\nrom: {}\n", encoding="utf-8")
    created_manifest.runtime_state.write_bytes(b"state")
    tool_root = tmp_path / "pokebot-gen3"
    (tool_root / "roms").mkdir(parents=True)
    (tool_root / "profiles").mkdir()

    staged_rom = stage_gen3_profile(created_manifest, tool_root)

    assert staged_rom.parent == tool_root / "roms"
    assert staged_rom.read_bytes() == b"source-rom"
    assert (tool_root / "profiles" / "emerald-level-grind" / "current_state.ss1").read_bytes() == b"state"
    assert created_manifest.source_path.read_bytes() == b"source-rom"


def test_build_gen3_command_selects_profile_and_mode(tmp_path: Path) -> None:
    assert build_gen3_command(tmp_path, "emerald-level-grind", "Level Grind") == [
        str(tmp_path / ".venv" / "Scripts" / "python.exe"), "pokebot.py", "emerald-level-grind", "--bot-mode", "Level Grind"
    ]
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python -m pytest farm-toolbox/tests/test_gen3.py -q`

Expected: FAIL because `pokemon_farm.gen3` does not exist.

- [ ] **Step 4: Implement staging and preflight**

`stage_gen3_rom()` must confirm the upstream `pokebot.py`, its `.venv/Scripts/python.exe`, and `roms/` directory exist; confirm `manifest.game_family` is `GEN3`; verify the source hash; and copy the ROM to the unique upstream filename `<profile-name><suffix>`. `preflight_gen3()` adds the requirement for `profiles/`, provisioned `bot-profile/metadata.yml`, and `current_state.ss1`. `stage_gen3_profile()` must call `stage_gen3_rom()`, make a state backup first, and mirror `bot-profile/` into upstream `profiles/<profile-name>/`. `sync_gen3_profile()` must copy that upstream directory back to `bot-profile/` without deleting files. `build_gen3_command()` returns the bare program command when both profile and mode are `None`; otherwise it must require nonblank values for both and return the exact list shown in the test. `provision-gen3` stages the ROM, runs the bare program command for the one-time native PokeBot profile creation, then calls `sync_gen3_profile()` only if the named upstream profile directory exists. `launch-gen3` must preflight, stage, run the selected profile/mode, and sync after a zero exit code; on a nonzero exit it prints the upstream profile path and does not delete anything.

- [ ] **Step 5: Run tests, perform an interactive smoke test, and commit**

Run:

```powershell
python -m pytest farm-toolbox/tests -q
pokemon-farm provision-gen3 `
  --profile farm-toolbox/profiles/emerald-level-grind/profile.json `
  --tool-root farm-toolbox/tools/pokebot-gen3
```

Expected: all tests pass; on this first manual provision, create the profile named `emerald-level-grind`, select its staged ROM, and either begin a new game or use **Load Existing Save** to import an mGBA state. Close PokeBot normally, then run `pokemon-farm sync-gen3 --profile farm-toolbox/profiles/emerald-level-grind/profile.json --tool-root farm-toolbox/tools/pokebot-gen3`. After that, `pokemon-farm launch-gen3 --profile farm-toolbox/profiles/emerald-level-grind/profile.json --tool-root farm-toolbox/tools/pokebot-gen3 --mode "Level Grind"` starts the isolated profile; run `pokemon-farm verify --profile farm-toolbox/profiles/emerald-level-grind/profile.json` and confirm the source hash is unchanged.

```powershell
git add farm-toolbox/src/pokemon_farm/gen3.py farm-toolbox/src/pokemon_farm/cli.py farm-toolbox/tests/test_gen3.py farm-toolbox/tests/test_cli.py farm-toolbox/README.md
git commit -m "feat: stage Gen 3 profiles for PokeBot"
```
