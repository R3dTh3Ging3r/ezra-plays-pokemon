# Ezra Plays Pokémon Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Publish a safe developer-first project and build a locally testable FireRed automation foundation that can observe a validated session, execute bounded normal-input actions, journal decisions, pause safely, and prepare a farm-job handoff to PokéBot Gen3.

**Architecture:** Keep the existing pokemon_farm profile and PokeBot staging safeguards as the boundary around user-owned game files. Add an autopilot package with emulator-neutral ports, normalized observations, bounded objective execution, a deterministic battle policy, and profile-owned audit records. A project-owned PokeBot bridge is installed into a user-local PokeBot checkout; it exposes only the bridge protocol and normal button inputs, while the controller remains in this repository.

**Tech Stack:** Python 3.13+, pytest, standard-library JSON/JSONL, the existing PokeBot Gen3/libmGBA checkout, Git, and GitHub CLI.

## Global Constraints

- FireRed is the only game supported by this implementation plan; all other games remain roadmap work.
- After setup, all execution is local and requires neither an API key nor a cloud service.
- Users supply their own legally obtained ROMs and saves. Do not commit ROMs, save files, savestates, screenshots containing game assets, credentials, tool virtual environments, or personal absolute paths.
- The controller may read supported emulator state but must affect gameplay only through ordinary controller buttons. It must not alter save data, create items, manipulate RNG, or write emulator memory.
- Every action block has a bounded frame count and an observable expected result. An unknown, stalled, invalid, or unsafe state releases inputs, writes a pause record, and returns control to the user.
- Preserve the existing profile isolation, source hashing, staging, sync, and backup guarantees. No new code may weaken their containment or no-overwrite checks.
- Public tests use synthetic state and mocked ports. Optional smoke tests use a developer-owned FireRed setup and are not part of the default test command.
- Run D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests -q before every task commit.

---

## File Structure

| Path | Responsibility |
| --- | --- |
| README.md | Public landing page, legal boundary, status, and roadmap links. |
| LICENSE | MIT license for original code; it grants no rights to Pokémon assets or upstream tool code. |
| CONTRIBUTING.md | Contributor, test, and no-assets-in-commits rules. |
| .github/ISSUE_TEMPLATE/bug_report.yml | Sanitized bug reports that prohibit game assets and personal saves. |
| farm-toolbox/src/pokemon_farm/autopilot/contracts.py | Stable input, observation, objective, and emulator port types. |
| farm-toolbox/src/pokemon_farm/autopilot/journal.py | Profile-contained JSONL decision and pause records. |
| farm-toolbox/src/pokemon_farm/autopilot/runner.py | One bounded objective step with precondition, success, stall, and pause handling. |
| farm-toolbox/src/pokemon_farm/autopilot/battle.py | Deterministic initial battle-action selection. |
| farm-toolbox/src/pokemon_farm/autopilot/farming.py | Validated farm-job request and result verification. |
| farm-toolbox/src/pokemon_farm/autopilot/bridge.py | Profile-contained bridge paths and JSON protocol validation. |
| farm-toolbox/integrations/pokebot/ezra_bridge.py | User-installed PokeBot plug-in that performs bounded normal inputs and reports normalized state. |
| farm-toolbox/src/pokemon_farm/gen3.py | Safe bridge installation into an explicitly selected PokeBot tool root. |
| farm-toolbox/src/pokemon_farm/cli.py | install-bridge, story-status, and story-step commands. |
| farm-toolbox/tests/test_autopilot_*.py | Synthetic public coverage for every new automation behavior. |

## Task 1: Prepare the public project and publish the roadmap

**Files:**
- Create: README.md
- Create: LICENSE
- Create: CONTRIBUTING.md
- Create: .github/ISSUE_TEMPLATE/bug_report.yml
- Create: farm-toolbox/tests/test_project_metadata.py
- Modify: .gitignore
- Modify: farm-toolbox/README.md
- Modify: farm-toolbox/pyproject.toml

**Interfaces:**
- Consumes: docs/superpowers/specs/2026-07-30-ezra-plays-pokemon-design.md.
- Produces: public documentation, an original-code license, a legal-use boundary, and a regression test for those promises.

- [ ] **Step 1: Write the failing metadata test**

    from pathlib import Path

    def test_public_readme_sets_legal_and_safety_boundaries() -> None:
        readme = Path(__file__).parents[2] / "README.md"
        text = readme.read_text(encoding="utf-8")
        assert "Ezra Plays Pokémon" in text
        assert "legally obtained" in text
        assert "does not include ROMs or save files" in text
        assert "FireRed" in text
        assert "local" in text.lower()

- [ ] **Step 2: Run the test to verify it fails**

Run: D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests\test_project_metadata.py -q

Expected: FAIL because README.md is absent.

- [ ] **Step 3: Add public documents and package metadata**

Write a root README with sections named Ezra Plays Pokémon, What it is, Status, Legal and safety boundary, Current capability, Roadmap, Quick start for developers, and Contributing. State that version 0.1 is a FireRed-only foundation, pauses safely when uncertain, uses local-only automation, and link the approved design specification.

Add the standard MIT license text to LICENSE, naming R3dTh3Ging3r as copyright holder. In CONTRIBUTING.md require a focused test, a short behavior demonstration, and no game assets in commits.

Create the YAML issue form with required fields for toolbox version/commit, OS, Python version, PokeBot/emulator version, sanitized logs, expected behavior, actual behavior, and a checkbox that confirms no ROM, save, state, or copyrighted screenshot is attached.

Add these fields to the project table in farm-toolbox/pyproject.toml:

    description = "Local, safety-first Pokémon automation foundations"
    readme = "README.md"
    license = { text = "MIT" }

Extend .gitignore with .env, *.sav, *.ss1, *.state, *.log, farm-toolbox/integrations/pokebot/__pycache__/, and farm-toolbox/.coverage. Do not ignore the project-owned ezra_bridge.py source. Update farm-toolbox/README.md to call the package the local FireRed automation foundation while retaining all existing safe profile instructions.

- [ ] **Step 4: Run public-safety checks**

Run:

    D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests\test_project_metadata.py -q
    git check-ignore -v "farm-toolbox/profiles/firered-farm/bot-profile/current_save.sav"
    git ls-files | Select-String -Pattern '\.(gba|gbc|gb|sav|ss1|state)$'

Expected: test passes; sample save is ignored; tracked-file scan prints no game or state artifacts.

- [ ] **Step 5: Run the full suite and commit**

Run: D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests -q

Expected: all tests pass.

    git add README.md LICENSE CONTRIBUTING.md .github .gitignore farm-toolbox/README.md farm-toolbox/pyproject.toml farm-toolbox/tests/test_project_metadata.py
    git commit -m "docs: prepare Ezra Plays Pokemon public project"

- [ ] **Step 6: Create the public GitHub repository only after the final scan**

Run:

    git ls-files | Select-String -Pattern '(Pokemon Roms|farm-toolbox/profiles|farm-toolbox/tools|\.(gba|gbc|gb|sav|ss1|state)$)'
    # Run this one branch rename from the primary worktree, which currently owns master.
    git branch -m master main
    # Return to this feature worktree for the remote creation and pushes.
    gh repo create R3dTh3Ging3r/ezra-plays-pokemon --public --source=. --remote=origin --description "Local, memory-assisted Pokémon automation: story progression, safe farming, and an auditable living-dex roadmap."
    git push origin HEAD:main
    git push -u origin HEAD
    gh repo edit R3dTh3Ging3r/ezra-plays-pokemon --add-topic pokemon --add-topic automation --add-topic emulator --add-topic local-ai --add-topic firered

Expected: the scan emits no prohibited files; public main contains the reviewed documentation; the current codex feature branch is also pushed; and the description plus five topics appear in settings.

## Task 2: Define automation contracts and profile-contained journals

**Files:**
- Create: farm-toolbox/src/pokemon_farm/autopilot/__init__.py
- Create: farm-toolbox/src/pokemon_farm/autopilot/contracts.py
- Create: farm-toolbox/src/pokemon_farm/autopilot/journal.py
- Create: farm-toolbox/tests/test_autopilot_contracts.py
- Create: farm-toolbox/tests/test_autopilot_journal.py

**Interfaces:**
- Consumes: ProfileManifest and synthetic test ports.
- Produces: Button, GamePhase, RunDisposition, ObservedState, InputBlock, EmulatorPort, Objective, and RunJournal.

- [ ] **Step 1: Write the failing contract and journal tests**

    import pytest
    from pokemon_farm.autopilot.contracts import Button, GamePhase, InputBlock, ObservedState
    from pokemon_farm.autopilot.journal import RunJournal

    def test_observed_state_is_immutable_and_carries_progress() -> None:
        state = ObservedState(4, GamePhase.OVERWORLD, 3, 0, 12, 8, 1, (14, 12), False)
        assert state.party_levels == (14, 12)

    def test_input_block_rejects_unbounded_action() -> None:
        with pytest.raises(ValueError, match="frames"):
            InputBlock(Button.RIGHT, 0, "walk")

    def test_pause_records_reason_inside_profile(created_manifest) -> None:
        journal = RunJournal.for_manifest(created_manifest)
        state = ObservedState(1, GamePhase.UNKNOWN, None, None, None, None, 0, (), False)
        journal.pause("unexpected dialogue", state)
        assert journal.path.is_relative_to(created_manifest.profile_root)

Also test that a constructed journal path outside profile_root raises ValueError before it creates a file.

- [ ] **Step 2: Run the new tests to verify they fail**

Run: D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests\test_autopilot_contracts.py farm-toolbox\tests\test_autopilot_journal.py -q

Expected: FAIL because the autopilot package is absent.

- [ ] **Step 3: Implement the contracts and append-only journal**

In contracts.py define Button as UP, DOWN, LEFT, RIGHT, A, B, START, and SELECT; GamePhase as OVERWORLD, BATTLE, DIALOGUE, MENU, and UNKNOWN; and RunDisposition as RUNNING, PAUSED, and COMPLETE.

Implement these exact immutable dataclasses:

    @dataclass(frozen=True)
    class ObservedState:
        sequence: int
        phase: GamePhase
        map_group: int | None
        map_number: int | None
        x: int | None
        y: int | None
        badges: int
        party_levels: tuple[int, ...]
        menu_open: bool

    @dataclass(frozen=True)
    class InputBlock:
        button: Button
        frames: int
        label: str

Reject blank labels and values outside 1 through 120 frames. Define EmulatorPort as a Protocol with observe() -> ObservedState, send(block: InputBlock) -> None, and release_all() -> None. Define Objective as a Protocol with objective_id, is_ready(state), is_complete(state), and next_block(state).

Implement RunJournal.for_manifest() with exactly manifest.logs_dir / "autopilot.jsonl". Resolve it, reject redirects, and require it remain under profile_root. record() appends one UTF-8 JSON object per line with kind, UTC timestamp, and normalized state, flushes it, then calls os.fsync(). pause() rejects a blank reason and writes kind paused with the supplied reason.

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests\test_autopilot_contracts.py farm-toolbox\tests\test_autopilot_journal.py -q

Expected: PASS.

- [ ] **Step 5: Run full verification and commit**

Run: D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests -q

    git add farm-toolbox/src/pokemon_farm/autopilot farm-toolbox/tests/test_autopilot_contracts.py farm-toolbox/tests/test_autopilot_journal.py
    git commit -m "feat: add autopilot contracts and journal"

## Task 3: Implement bounded objective, battle, and farm-result policies

**Files:**
- Create: farm-toolbox/src/pokemon_farm/autopilot/runner.py
- Create: farm-toolbox/src/pokemon_farm/autopilot/battle.py
- Create: farm-toolbox/src/pokemon_farm/autopilot/farming.py
- Create: farm-toolbox/tests/test_autopilot_runner.py
- Create: farm-toolbox/tests/test_autopilot_battle.py
- Create: farm-toolbox/tests/test_autopilot_farming.py

**Interfaces:**
- Consumes: EmulatorPort, Objective, RunJournal, ProfileManifest, InputBlock, and ObservedState.
- Produces: ObjectiveRunner.advance(objective) -> RunDisposition, BattleActionPlan, choose_battle_action(), FarmRequest, and FarmCoordinator.verify_result().

- [ ] **Step 1: Write failing runner tests with a local fake port**

Create a ScriptedEmulatorPort in test_autopilot_runner.py whose observe() returns queued states and whose send() stores the action. Cover these cases: an already-complete objective sends no input and returns COMPLETE; a false precondition returns PAUSED and calls release_all once; a same-sequence observation after input returns PAUSED; and a sequence increasing from 7 to 8 returns RUNNING after exactly InputBlock(Button.RIGHT, 8, "walk east").

- [ ] **Step 2: Write failing policy tests**

Use synthetic MoveOption(name, power, accuracy, pp, super_effective) and BattleState(hp_percent, usable_moves, potion_count, can_switch). Assert that a usable super-effective move wins; 15% HP with a potion chooses heal; and no PP, no potion, no switch chooses pause.

Create before/after snapshots with party_levels. Assert FarmCoordinator verifies success only when the chosen party slot reaches FarmRequest(mode="Level Grind", party_slot=0, target_level=12), never decreases, and the profile source hash still matches. Assert unchanged level is rejected and logged.

- [ ] **Step 3: Run focused tests to verify they fail**

Run: D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests\test_autopilot_runner.py farm-toolbox\tests\test_autopilot_battle.py farm-toolbox\tests\test_autopilot_farming.py -q

Expected: FAIL because the runner and policies are absent.

- [ ] **Step 4: Implement the safe execution and policies**

ObjectiveRunner.advance() must observe once, return COMPLETE and log objective-complete if is_complete is true, then pause and release inputs for a failed precondition or absent safe action. It sends exactly one block, then observes once more. It returns RUNNING only if sequence increased; otherwise it releases inputs, logs objective_id plus action stalled, and returns PAUSED.

Define BattleActionPlan(kind: Literal["fight", "heal", "switch", "pause"], detail: str). Choose the usable super-effective move with the highest power times accuracy; otherwise choose the best usable move. At HP <= 20 with a potion choose heal before fighting. If no move is usable, select switch only when allowed; otherwise select pause.

FarmRequest permits only party slots 0 through 5 and target levels 2 through 100. FarmCoordinator.verify_result() compares normalized snapshots, source hash, and selected level, then records farm-complete or farm-rejected. It does not launch PokeBot in this task.

- [ ] **Step 5: Run tests, full verification, and commit**

Run:

    D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests\test_autopilot_runner.py farm-toolbox\tests\test_autopilot_battle.py farm-toolbox\tests\test_autopilot_farming.py -q
    D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests -q

Expected: PASS.

    git add farm-toolbox/src/pokemon_farm/autopilot/runner.py farm-toolbox/src/pokemon_farm/autopilot/battle.py farm-toolbox/src/pokemon_farm/autopilot/farming.py farm-toolbox/tests/test_autopilot_runner.py farm-toolbox/tests/test_autopilot_battle.py farm-toolbox/tests/test_autopilot_farming.py
    git commit -m "feat: add safe story foundation policies"

## Task 4: Define and install the PokeBot bridge safely

**Files:**
- Create: farm-toolbox/src/pokemon_farm/autopilot/bridge.py
- Create: farm-toolbox/integrations/pokebot/ezra_bridge.py
- Modify: farm-toolbox/src/pokemon_farm/gen3.py
- Create: farm-toolbox/tests/test_autopilot_bridge.py
- Modify: farm-toolbox/tests/test_gen3.py

**Interfaces:**
- Consumes: ProfileManifest, a user-selected tool root, the contained-directory helpers in gen3.py, and InputBlock bounds.
- Produces: BridgePaths.for_manifest(manifest), BridgePaths.for_live_gen3(manifest, tool_root), install_pokebot_bridge(manifest, tool_root) -> Path, and the profile-owned command.json, observation.json, and bridge-status.json files.

- [ ] **Step 1: Write failing bridge tests**

    def test_bridge_paths_are_owned_by_selected_profile(created_manifest) -> None:
        paths = BridgePaths.for_manifest(created_manifest)
        assert paths.command.parent.is_relative_to(created_manifest.profile_root)
        assert paths.observation.parent.is_relative_to(created_manifest.profile_root)

    def test_install_copies_source_only_into_selected_plugins_dir(created_manifest, tmp_path) -> None:
        tool_root = _make_tool_root(tmp_path)
        (tool_root / "plugins").mkdir()
        installed = install_pokebot_bridge(created_manifest, tool_root)
        assert installed == tool_root / "plugins" / "ezra_bridge.py"

Add refusal tests for a symlinked plugins directory and a symlinked existing bridge file.

- [ ] **Step 2: Run bridge tests to verify they fail**

Run: D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests\test_autopilot_bridge.py farm-toolbox\tests\test_gen3.py -q

Expected: FAIL because BridgePaths and install_pokebot_bridge are absent.

- [ ] **Step 3: Implement the file bridge and installer**

BridgePaths.for_manifest() resolves exactly manifest.bot_profile_dir / "autopilot", rejects a redirect, and requires containment within the profile. This location is deliberately inside the synchronised native PokeBot profile, so normal stage and sync operations carry bridge data without a separate copy path. BridgePaths.for_live_gen3(manifest, tool_root) resolves that same autopilot directory inside the validated active tool_root/profiles/profile_name directory and rejects redirects or escapes. The live path is the only path used while PokeBot is running; the local path is imported on a clean sync. Both validate command.json schema: sequence is int, button is a known Button value, frames is 1 through 120, and label is nonblank.

The ezra_bridge.py plugin uses the upstream PokeBot plugin API to add an Ezra Bridge BotMode. It reads only a validated command JSON, presses the requested button using context.emulator.press_button(), yields exactly the requested number of frames, and resets held buttons. It writes observation.json atomically with command sequence, PokeBot frame count, normalized game phase, plus raw map/player/party values available through public PokeBot modules. A malformed, stale, or unsupported command resets inputs and writes a bridge-status.json error instead of pressing anything. It does not write emulator memory, patch saves, access the network, or import game files.

install_pokebot_bridge() validates the existing tool root, requires a real plugins directory within that root, copies the project bridge source through a temporary sibling, then atomically replaces only plugins/ezra_bridge.py.

- [ ] **Step 4: Run bridge tests to verify they pass and commit**

Run:

    D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests\test_autopilot_bridge.py farm-toolbox\tests\test_gen3.py -q
    D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests -q

Expected: PASS.

    git add farm-toolbox/src/pokemon_farm/autopilot/bridge.py farm-toolbox/integrations/pokebot/ezra_bridge.py farm-toolbox/src/pokemon_farm/gen3.py farm-toolbox/tests/test_autopilot_bridge.py farm-toolbox/tests/test_gen3.py
    git commit -m "feat: add safe PokeBot bridge"

## Task 5: Expose the foundation commands and prove one normal input safely

**Files:**
- Modify: farm-toolbox/src/pokemon_farm/cli.py
- Modify: farm-toolbox/README.md
- Modify: farm-toolbox/tests/test_cli.py
- Create: farm-toolbox/tests/test_autopilot_cli.py

**Interfaces:**
- Consumes: BridgePaths, RunJournal, InputBlock, install_pokebot_bridge, and existing profile/tool preflight helpers.
- Produces: pokemon-farm install-bridge, story-status, and story-step with explicit paths and fail-closed behavior.

- [ ] **Step 1: Write failing command tests**

    assert main(["install-bridge", "--profile", str(manifest_path), "--tool-root", str(tool_root)]) == 0
    assert main(["story-status", "--profile", str(manifest_path), "--tool-root", str(tool_root)]) == 0
    assert "bridge observation: absent" in capsys.readouterr().out
    assert main(["story-step", "--profile", str(manifest_path), "--tool-root", str(tool_root)]) == 2
    assert "bridge observation is absent" in capsys.readouterr().err

Also assert story-status reports paused plus the final reason when the journal has a pause record, and malformed observation.json returns code 2 without changing command.json.

- [ ] **Step 2: Run command tests to verify they fail**

Run: D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests\test_autopilot_cli.py farm-toolbox\tests\test_cli.py -q

Expected: FAIL because the commands are absent.

- [ ] **Step 3: Implement explicit fail-closed commands**

install-bridge calls install_pokebot_bridge and prints the installed path. story-status and story-step both require --tool-root and operate through BridgePaths.for_live_gen3(), so they communicate with the active PokeBot profile rather than a stale local copy. story-status reports which bridge files are present and prints only final journal kind/reason. story-step requires a valid existing observation, validates its sequence and normalized state, then atomically writes one command file using explicit --button, --frames, and --label parameters. It records a journal event before success. All validation errors return through existing main exception handling with exit code 2 and leave prior bridge files unchanged.

Document this proof in farm-toolbox/README.md: provision a legal FireRed profile; install the bridge; launch Ezra Bridge only after the user confirms at launch time in Terminal A; while it remains running, use Terminal B to run story-status and issue one story-step with the same --tool-root; observe one normal input; close cleanly; sync; verify; and back up. State that the first gym objective implementation starts in a separate Phase 2 plan after this evidence passes.

- [ ] **Step 4: Run focused tests, full verification, and commit**

Run:

    D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests\test_autopilot_cli.py farm-toolbox\tests\test_cli.py -q
    D:\Codex-Projects\Non-App-Projects\pokemon\.venv\Scripts\python.exe -m pytest farm-toolbox\tests -q
    git diff --check
    git status --short

Expected: tests pass, diff has no whitespace errors, and only intended source/test/doc/config files are staged.

    git add farm-toolbox/src/pokemon_farm/cli.py farm-toolbox/README.md farm-toolbox/tests/test_cli.py farm-toolbox/tests/test_autopilot_cli.py
    git commit -m "feat: expose FireRed story foundation"

## Plan Self-Review

- **Spec coverage:** Task 1 implements the public legal boundary and project presentation. Tasks 2 through 3 implement normalized observation, bounded actions, audit, safe pause, battle policy, and farm outcome verification. Task 4 supplies the normal-input PokeBot connection. Task 5 adds explicit local workflows and evidence.
- **Intentional scope boundary:** FireRed story completion, living-dex collection, breeding, local trades, other Gen 3 games, Gen 2, and portable phone save handoffs remain their own roadmap phases. This plan creates the foundation needed to implement them without claiming those capabilities early.
- **Type consistency:** ObservedState, InputBlock, EmulatorPort, Objective, RunJournal, BridgePaths, FarmRequest, and FarmCoordinator are introduced before their consumers.
- **Safety check:** All new paths are profile-contained or tool-root-contained. The only real emulator launch is explicitly conditional on a user confirmation at launch time. No task permits ROM distribution, save editing, network access, credentials, or direct memory writes.
