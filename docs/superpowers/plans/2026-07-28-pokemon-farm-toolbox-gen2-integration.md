# Pokemon Farm Toolbox Gen 2 Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Gold, Silver, and Crystal support by staging isolated profiles into BizHawk 2.10 with the Kakumi Pokebot external tool.

**Architecture:** This plan extends the profile manager from the Gen 3 foundation plan. A Gen 2 adapter creates a unique staged ROM name and a matching BizHawk SaveRAM location for each profile, snapshots that SaveRAM before launch, and syncs it back to the profile-owned working save after BizHawk exits.

**Tech Stack:** Windows 10/11, Python 3.13, pytest, BizHawk 2.10, Kakumi Pokebot release DLL.

## Global Constraints

- Complete the Gen 3 foundation plan before this plan.
- Support only Gold, Silver, and Crystal in this plan.
- Use BizHawk 2.10 because Kakumi Pokebot documents it as the tested emulator version.
- Never download, distribute, modify, or commit ROM files.
- Stage only copied profile files; do not point BizHawk at a user source game path.
- Create a timestamped backup before launching BizHawk and before copying a changed SaveRAM back into a profile.
- Leave `Pokemon Roms/`, upstream tool directories, and mutable profile data ignored by Git.

---

## File Structure

```text
farm-toolbox/
  src/pokemon_farm/
    models.py
    backups.py
    gen2.py
    cli.py
  tests/
    test_gen2.py
  tools/
    bizhawk-2.10/
      EmuHawk.exe
      ExternalTools/Pokebot.dll
      Gameboy/SaveRam/
    pokebot-gsc-release/
```

### Task 1: Add Gen 2 game metadata without weakening Gen 3 validation

**Files:**
- Modify: `farm-toolbox/src/pokemon_farm/models.py`
- Modify: `farm-toolbox/tests/test_models.py`

**Interfaces:**
- Produces: `GEN2_GAME_IDS = frozenset({"gold", "silver", "crystal"})` and `new_manifest()` support for both `GameFamily.GEN2` and `GameFamily.GEN3`.
- Consumed by: Gen 2 staging and CLI validation.

- [ ] **Step 1: Write the failing Gen 2 manifest test**

```python
from pokemon_farm.models import GameFamily, new_manifest


def test_manifest_maps_crystal_to_gen2(tmp_path) -> None:
    rom = tmp_path / "crystal.gbc"
    rom.write_bytes(b"ROM")

    manifest = new_manifest("crystal-fishing", "crystal", rom, tmp_path / "profile")

    assert manifest.game_family is GameFamily.GEN2
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest farm-toolbox/tests/test_models.py::test_manifest_maps_crystal_to_gen2 -q`

Expected: FAIL because `new_manifest()` rejects `crystal`.

- [ ] **Step 3: Implement the minimal mapping change**

Add `GEN2_GAME_IDS`; update `new_manifest()` to look up the family from the two disjoint game-ID sets and raise `ValueError("unsupported game id: <id>")` only when neither set contains the requested ID. For a Gen 2 manifest, set `bot_profile_dir` to `None` and derive `runtime_state` as `<profile-root>/save/<game-id>.sav`; keep Gen 3's `<profile-root>/bot-profile/current_state.ss1`. Keep the Gen 3 test from the foundation plan and update its rejection case to use `yellow` instead of `crystal`.

- [ ] **Step 4: Run model tests**

Run: `python -m pytest farm-toolbox/tests/test_models.py -q`

Expected: PASS.

- [ ] **Step 5: Commit Gen 2 metadata**

```powershell
git add farm-toolbox/src/pokemon_farm/models.py farm-toolbox/tests/test_models.py
git commit -m "feat: add Gen 2 profile metadata"
```

### Task 2: Install the tested emulator and external tool in ignored directories

**Files:**
- Create: `farm-toolbox/scripts/install-gen2-tools.ps1`
- Modify: `farm-toolbox/README.md`

**Interfaces:**
- Produces: `farm-toolbox/tools/bizhawk-2.10/EmuHawk.exe` and `farm-toolbox/tools/bizhawk-2.10/ExternalTools/Pokebot.dll`.
- Consumed by: `preflight_gen2()`.

- [ ] **Step 1: Write an installation verification test**

```python
from pathlib import Path

import pytest

from pokemon_farm.gen2 import validate_gen2_tool_install


def test_validate_gen2_tool_install_requires_emuhawk_and_dll(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="EmuHawk.exe"):
        validate_gen2_tool_install(tmp_path)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest farm-toolbox/tests/test_gen2.py::test_validate_gen2_tool_install_requires_emuhawk_and_dll -q`

Expected: FAIL because `pokemon_farm.gen2` does not exist.

- [ ] **Step 3: Write the install script**

The script must accept `-BizHawkZip` and `-PokeBotDll` parameters, create `farm-toolbox/tools/bizhawk-2.10`, expand the user-provided BizHawk 2.10 zip there, create `ExternalTools`, and copy the user-provided `Pokebot.dll` into it. It must reject a zip that does not produce `EmuHawk.exe` and reject a DLL whose name is not `Pokebot.dll`. Do not use the script to fetch ROMs or operate on `Pokemon Roms/`.

```powershell
.\farm-toolbox\scripts\install-gen2-tools.ps1 `
  -BizHawkZip C:\Users\emat1\Downloads\BizHawk-2.10-win-x64.zip `
  -PokeBotDll C:\Users\emat1\Downloads\Pokebot.dll
```

- [ ] **Step 4: Implement and test `validate_gen2_tool_install()`**

Require both `EmuHawk.exe` and `ExternalTools/Pokebot.dll`, returning the resolved BizHawk root only when both exist. Run the test from Step 1 and add a passing fixture with both empty files. Add these reusable fixtures to `tests/conftest.py`:

```python
@pytest.fixture
def created_crystal_manifest(tmp_path: Path):
    source_rom = tmp_path / "crystal.gbc"
    source_rom.write_bytes(b"source-rom")
    manifest = new_manifest("crystal-fishing", "crystal", source_rom, tmp_path / "profiles" / "crystal-fishing")
    return create_profile(manifest)


@pytest.fixture
def bizhawk_root(tmp_path: Path) -> Path:
    root = tmp_path / "bizhawk-2.10"
    (root / "EmuHawk.exe").parent.mkdir(parents=True)
    (root / "EmuHawk.exe").write_bytes(b"")
    (root / "ExternalTools").mkdir()
    (root / "ExternalTools" / "Pokebot.dll").write_bytes(b"")
    (root / "Gameboy" / "SaveRam").mkdir(parents=True)
    (root / "roms").mkdir()
    return root
```

Import `pytest`, `Path`, `new_manifest`, and `create_profile` in that fixture file.

- [ ] **Step 5: Commit tool-install support**

```powershell
git add farm-toolbox/scripts/install-gen2-tools.ps1 farm-toolbox/src/pokemon_farm/gen2.py farm-toolbox/tests/test_gen2.py farm-toolbox/README.md
git commit -m "feat: install Gen 2 automation tools"
```

### Task 3: Stage a unique BizHawk ROM and SaveRAM per profile

**Files:**
- Modify: `farm-toolbox/src/pokemon_farm/gen2.py`
- Modify: `farm-toolbox/tests/test_gen2.py`

**Interfaces:**
- Consumes: `ProfileManifest`, `backup_runtime_state`, and `validate_gen2_tool_install`.
- Produces: `Gen2Stage(runtime_rom: Path, runtime_saveram: Path)`, `stage_gen2_profile(manifest: ProfileManifest, bizhawk_root: Path) -> Gen2Stage`, and `sync_gen2_save(manifest: ProfileManifest, stage: Gen2Stage) -> None`.

- [ ] **Step 1: Write failing unique-stage and sync tests**

```python
from pokemon_farm.gen2 import stage_gen2_profile, sync_gen2_save


def test_stage_gen2_profile_uses_a_unique_rom_and_saveram(created_crystal_manifest, bizhawk_root) -> None:
    created_crystal_manifest.runtime_state.parent.mkdir(parents=True, exist_ok=True)
    created_crystal_manifest.runtime_state.write_bytes(b"profile-save")

    stage = stage_gen2_profile(created_crystal_manifest, bizhawk_root)

    assert stage.runtime_rom.name == "crystal-fishing.gbc"
    assert stage.runtime_saveram.name == "crystal-fishing.SaveRAM"
    assert stage.runtime_saveram.read_bytes() == b"profile-save"


def test_sync_gen2_save_makes_a_backup_before_copy(created_crystal_manifest, bizhawk_root) -> None:
    stage = stage_gen2_profile(created_crystal_manifest, bizhawk_root)
    stage.runtime_saveram.write_bytes(b"changed-in-bizhawk")

    sync_gen2_save(created_crystal_manifest, stage)

    assert created_crystal_manifest.runtime_state.read_bytes() == b"changed-in-bizhawk"
    assert list(created_crystal_manifest.backups_dir.glob("*-before-sync.sav"))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest farm-toolbox/tests/test_gen2.py -q`

Expected: FAIL because staging and sync functions are absent.

- [ ] **Step 3: Implement staging and sync**

`stage_gen2_profile()` must require a `GEN2` manifest, call `backup_runtime_state()` before copying, copy the profile-owned ROM to `bizhawk_root/roms/<profile-name><suffix>`, and copy the working save to `bizhawk_root/Gameboy/SaveRam/<profile-name>.SaveRAM`. `sync_gen2_save()` must create a second backup named with the exact suffix `-before-sync.sav`, then copy only from that unique runtime SaveRAM to `manifest.runtime_state`.

- [ ] **Step 4: Run Gen 2 tests**

Run: `python -m pytest farm-toolbox/tests/test_gen2.py -q`

Expected: PASS.

- [ ] **Step 5: Commit isolated Gen 2 staging**

```powershell
git add farm-toolbox/src/pokemon_farm/gen2.py farm-toolbox/tests/test_gen2.py
git commit -m "feat: stage isolated Gen 2 saves"
```

### Task 4: Launch BizHawk and sync the profile after exit

**Files:**
- Modify: `farm-toolbox/src/pokemon_farm/gen2.py`
- Modify: `farm-toolbox/src/pokemon_farm/cli.py`
- Modify: `farm-toolbox/tests/test_gen2.py`
- Modify: `farm-toolbox/tests/test_cli.py`
- Modify: `farm-toolbox/README.md`

**Interfaces:**
- Produces: `build_gen2_command(bizhawk_root: Path, stage: Gen2Stage) -> list[str]` and `pokemon-farm launch-gen2 --profile <manifest path>`.

- [ ] **Step 1: Write a failing launch-command test**

```python
from pokemon_farm.gen2 import Gen2Stage, build_gen2_command


def test_build_gen2_command_uses_emuhawk_and_staged_rom(bizhawk_root) -> None:
    stage = Gen2Stage(
        runtime_rom=bizhawk_root / "roms" / "crystal-fishing.gbc",
        runtime_saveram=bizhawk_root / "Gameboy" / "SaveRam" / "crystal-fishing.SaveRAM",
    )

    assert build_gen2_command(bizhawk_root, stage) == [
        str(bizhawk_root / "EmuHawk.exe"), str(stage.runtime_rom)
    ]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest farm-toolbox/tests/test_gen2.py::test_build_gen2_command_uses_emuhawk_and_staged_rom -q`

Expected: FAIL because `build_gen2_command()` is absent.

- [ ] **Step 3: Implement launch behavior**

Use `subprocess.run()` with the exact command list returned by `build_gen2_command()`. Only call `sync_gen2_save()` after EmuHawk exits with return code 0; otherwise print the staged SaveRAM path and leave it intact for inspection. Add `launch-gen2` to the CLI with required `--profile` and `--bizhawk-root` arguments.

- [ ] **Step 4: Run all tests and perform an interactive smoke test**

Run:

```powershell
python -m pytest farm-toolbox/tests -q
pokemon-farm launch-gen2 `
  --profile farm-toolbox/profiles/crystal-fishing/profile.json `
  --bizhawk-root farm-toolbox/tools/bizhawk-2.10
```

Expected: tests pass; BizHawk opens a staged Crystal profile copy. In BizHawk, load `Tools > External Tool > Pokebot`, confirm the game is recognized, close BizHawk normally, then run `pokemon-farm verify --profile farm-toolbox/profiles/crystal-fishing/profile.json` to confirm the working save and backups exist.

- [ ] **Step 5: Commit Gen 2 launch integration**

```powershell
git add farm-toolbox/src/pokemon_farm/gen2.py farm-toolbox/src/pokemon_farm/cli.py farm-toolbox/tests/test_gen2.py farm-toolbox/tests/test_cli.py farm-toolbox/README.md
git commit -m "feat: launch isolated Gen 2 farm profiles"
```
